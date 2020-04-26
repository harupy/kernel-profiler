import os
import argparse
import traceback
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
from premailer import transform
import jupytext
from tqdm import tqdm


driver = None
TOP_URL = "https://www.kaggle.com"
TIMEOUT = 15
HEADER = """
## My GitHub repository: [harupy/kernel-profiler](https://github.com/harupy/kernel-profiler) automatically updates this notebook by using [GitHub Actions](https://github.com/features/actions) and [Kaggle API](https://github.com/Kaggle/kaggle-api). Any feedback would be appreciated.
""".strip()  # NOQA


def parse_args():
    parser = argparse.ArgumentParser(description="Kernel Profiler")
    parser.add_argument(
        "-c", "--comp-slug", required=True, help="Competition slug (e.g. titanic)"
    )

    parser.add_argument(
        "-m",
        "--max-num-kernels",
        type=int,
        default=20,
        help="The maximum number of kernels profile for each competition (default: 20)",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        default="output",
        help='Directory to store the output (default: "output")',
    )
    return parser.parse_args()


def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1920x1080")
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/79.0.3945.117 Safari/537.36"
    )
    options.add_argument(f"--user-agent={user_agent}")

    if os.path.exists("./chromedriver"):
        return webdriver.Chrome("./chromedriver", options=options)

    return webdriver.Chrome(options=options)


def make_soup(html):
    return BeautifulSoup(html, "lxml")


def get_kernel_meta(soup):
    medal = soup.select("img.kernel-list-item__medals")

    if len(medal) > 0:
        # Replace "notebook" with "discussion" to use a bigger medal image.
        medal_src = TOP_URL + medal[0].get("src").replace("notebooks", "discussion")
    else:
        medal_src = ""

    return {
        "author_name": (
            soup.select("span.tooltip-container")[0].get("data-tooltip").strip()
        ),
        "author_id": soup.select("a.avatar")[0].get("href").strip("/"),
        "thumbnail_src": soup.select("img.avatar__thumbnail")[0].get("src"),
        "tier_src": TOP_URL + soup.select("img.avatar__tier")[0].get("src"),
        "votes": soup.select("span.vote-button__vote-count")[0].text.strip(),
        "comments": (
            soup.select("a.kernel-list-item__info-block--comment")[0].text.strip()
        ),
        "last_updated": (
            soup.select("div.kernel-list-item__details > span")[0].text.strip()
        ),
        "best_score": float(soup.select("div.kernel-list-item__score")[0].text.strip()),
        "language": soup.select("span.tooltip-container")[2].text.strip(),
        "medal_src": medal_src,
    }


def utcnow():
    return datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S (UTC)")


def extract_public_score(html):
    m = re.search(r'"publicScore":"(.+?)"', html)
    return float(m.group(1)) if m else ""


def extract_best_public_score(html):
    m = re.search(r'"bestPublicScore":([^,]+)', html)
    return float(m.group(1)) if m else ""


def format_run_time(run_time_str):
    run_time = float(run_time_str[:-1])

    if run_time < 60:
        return f"{run_time} s"
    elif run_time >= 60 and run_time < 3600:
        return f"{round(run_time / 60, 1)} m"
    else:
        return f"{round(run_time / 3600, 1)} h"


def make_link(text, url):
    return f"[{text}]({url})"


def make_row(items):
    row = "|".join(map(str, items))
    return f"|{row}|"


def make_image_tag(alt, src):
    return '<img alt="{}" src="{}" align="left">'.format(alt, src)


def make_anchor_tag(href, text):
    return '<a href="{}">{}</a>'.format(href, text)


def make_table(data, header):
    rows = [make_row(header)]
    rows += [make_row(["-" for _ in range(len(header))])]
    rows += [make_row(items) for items in data]
    return "\n".join(rows)


def make_thumbnail(thumbnail_src, tier_src, author_id):
    thumbnail = '<img src="{}" width="72">'.format(thumbnail_src)
    tier = '<img src="{}" width="72">'.format(tier_src)
    author_url = os.path.join(TOP_URL, author_id)
    return '<a href="{}" style="display: inline-block">{}{}</a>'.format(
        author_url, thumbnail, tier
    )


def format_meta_data(meta):
    author_link = make_link(
        meta["author_name"], os.path.join(TOP_URL, meta["author_id"])
    )

    if meta["medal_src"] != "":
        medal_img = make_image_tag("medal", meta["medal_src"])
    else:
        medal_img = "-"

    data = [
        ("Author", author_link),
        ("Language", meta["language"]),
        ("Best Score", meta["best_score"]),
        ("Votes", meta["votes"]),
        ("Medal", medal_img),
        ("Comments", meta["comments"]),
        ("Last Updated", meta["last_updated"]),
    ]
    headers = ["Key", "Value"]

    return data, headers


def extract_commit_data(soup):
    pattern = re.compile(r"VersionsPaneContent_IdeVersionsTable.+")
    rows = soup.find("table", {"class": pattern}).select("tbody > div")
    commits = []

    for row in tqdm(rows):
        version = row.select("a:nth-of-type(2)")[0]
        committed_at = row.find("span", recursive=False).text.strip()
        run_time = row.select("a:nth-of-type(4)")[0].text.strip()
        added = row.select("span:nth-of-type(2)")[0].text.strip()
        deleted = row.select("span:nth-of-type(3)")[0].text.strip()
        href = version.get("href")

        if href is None:
            continue

        # Ignore failed commits.
        icon = row.select("a:nth-of-type(1) > svg")[0].get("data-icon")
        if icon == "times-circle":
            continue

        # Extract the public score.
        url = TOP_URL + href
        resp = requests.get(url)
        score = extract_public_score(resp.text)

        if score == "":
            continue

        commits.append(
            (
                version.text.strip(),
                float(score),
                committed_at,
                format_run_time(run_time),
                added,
                deleted,
                make_anchor_tag(url, "Open"),
            )
        )

    headers = [
        "Version",
        "Score",
        "Committed at",
        "Run Time",
        "Added",
        "Deleted",
        "Link",
    ]
    return commits, headers


def make_profile(kernel_link, thumbnail, commit_table, meta_table):
    return f"""
<br>

# {kernel_link}

{thumbnail}

### Kernel Information
{meta_table}

### Commit History
The highlighted row represent the best score.
{commit_table}
""".strip()


def on_github_action():
    return "GITHUB_ACTION" in os.environ


def get_action_input(name):
    return os.getenv(f"INPUT_{name.upper()}")


def replace_extension(path, ext):
    if not ext.startswith("."):
        ext = "." + ext
    root = os.path.splitext(path)[0]
    return root + ext


def to_notebook(path):
    notebook = jupytext.read(path)
    jupytext.write(notebook, replace_extension(path, ".ipynb"))


def extract_kernels(soup):
    kernels = []

    for ker in soup.select("div.block-link--bordered"):
        if len(ker.select("div.kernel-list-item__score")) == 0:
            continue

        name = ker.select("div.kernel-list-item__name")[0].text
        url = TOP_URL + ker.select("a.block-link__anchor")[0].get("href")
        kernels.append({"name": name, "url": url, **get_kernel_meta(ker)})
    return kernels


def highlight_best_score(row, best_score):
    should_highlight = row["Score"] == best_score
    return [
        ("background-color: #d5fdd5" if should_highlight else "")
        for _ in range(len(row))  # len(row) returns the number of columns.
    ]


def main():
    if on_github_action():
        comp_slug = get_action_input("slug")
        max_num_kernels = int(get_action_input("max_num_kernels"))
        out_dir = get_action_input("out_dir")
    else:
        args = parse_args()
        comp_slug = args.comp_slug
        max_num_kernels = args.max_num_kernels
        out_dir = args.out_dir

    comp_url = f"https://www.kaggle.com/c/{comp_slug}/notebooks"

    profiles = []
    try:
        # Open the notebooks tab.
        driver.get(comp_url)

        # Click 'Sort By' select box.
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.Select-value"))
        )
        sort_by = driver.find_element_by_css_selector("div.Select-value")
        sort_by.click()

        # Select "Best score".
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.Select-menu-outer"))
        )
        options = driver.find_elements_by_css_selector("div.Select-menu-outer div")
        best_score_opt = [opt for opt in options if opt.text == "Best Score"][0]
        best_score_opt.click()

        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.block-link__anchor"))
        )

        # Extract kernels.
        kernels = extract_kernels(make_soup(driver.page_source))
        num_kernels = min(max_num_kernels, len(kernels))

        for ker_idx, kernel in enumerate(kernels):
            if (ker_idx + 1) > max_num_kernels:
                break

            print(f"Processing ({ker_idx + 1} / {num_kernels})")

            # Open the kernel.
            driver.get(kernel["url"])

            # Display the commit table.
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'VersionsInfoBox')]")
                )
            )
            commit_link = driver.find_element_by_xpath(
                "//div[contains(@class, 'VersionsInfoBox')]"
            )
            commit_link.click()

            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.vote-button__voters-modal-title")
                )
            )

            # Get the page source containing the commit table.
            soup = make_soup(driver.page_source)

            # Make a commit table.
            commits, headers = extract_commit_data(soup)
            df = pd.DataFrame(commits, columns=headers)
            commit_table = transform(
                df.style.apply(
                    highlight_best_score, best_score=kernel["best_score"], axis=1
                )
                .hide_index()
                .render()
            )

            meta_table = make_table(*format_meta_data(kernel))
            kernel_link = make_link(kernel["name"], kernel["url"])
            thumbnail = make_thumbnail(
                kernel["thumbnail_src"], kernel["tier_src"], kernel["author_id"]
            )
            profiles.append(
                make_profile(kernel_link, thumbnail, commit_table, meta_table)
            )

        # Save the result with a timestamp.
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{comp_slug}.md")
        timestamp = "## Last Updated: {}".format(utcnow)
        with open(out_path, "w") as f:
            f.write((2 * "\n").join([HEADER, timestamp] + profiles))

        # Convert markdown to notebook.
        to_notebook(out_path)

    except Exception:
        print(traceback.format_exc())
        with open("error.html", "w") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = create_driver()
    main()

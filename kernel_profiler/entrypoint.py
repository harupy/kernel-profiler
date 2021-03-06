import os
import argparse
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
from tqdm import tqdm

from kernel_profiler import markdown as md, html, github_action as ga, utils


TOP_URL = "https://www.kaggle.com"
DESCRIPTION = """
## My GitHub repository: [harupy/kernel-profiler][kernel-profiler] automatically updates this notebook by using [GitHub Actions][actions] and [Kaggle API][kaggle-api]. Any feedback would be appreciated.

[kernel-profiler]: https://github.com/harupy/kernel-profiler
[actions]: https://github.com/features/actions
[kaggle-api]: https://github.com/Kaggle/kaggle-api
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
        help=(
            "The maximum number of kernels to profile "
            "for each competition (default: 20)"
        ),
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        default="output",
        help='Directory to store the output (default: "output")',
    )
    return parser.parse_args()


def create_chrome_driver():
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


def make_soup(markup):
    return BeautifulSoup(markup, "lxml")


def extract_medal_src(soup):
    medal = soup.select("img.kernel-list-item__medals")
    if len(medal) > 0:
        return medal[0].get("src")


def extract_kernel_metadata(soup):
    medal_src = extract_medal_src(soup)

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
        "best_score": soup.select("div.kernel-list-item__score")[0].text.strip(),
        "language": soup.select("span.tooltip-container")[2].text.strip(),
        "medal_src": (
            # Replace "notebook" with "discussion" to use a bigger medal image.
            TOP_URL + medal_src.replace("notebooks", "discussion")
            if medal_src is not None
            else ""
        ),
    }


def format_kernel_metadata(meta):
    author_link = md.make_link(
        meta["author_name"], os.path.join(TOP_URL, meta["author_id"])
    )

    if meta["medal_src"] != "":
        attrs = {
            "alt": "medal",
            "src": meta["medal_src"],
            "align": "left",
        }
        medal_img = html.make_image_tag(attrs)
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

    assert len(data[0]) == len(headers)

    return data, headers


def extract_commits(soup):
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

        version = version.text.strip()

        if href is None:
            continue

        # Ignore failed commits.
        status_icon = row.select("a:nth-of-type(1) > svg")[0].get("data-icon")
        if status_icon == "times-circle":
            continue

        # Extract the public score.
        url = TOP_URL + href
        resp = requests.get(url)
        score = utils.extract_public_score(resp.text)

        # Ignore commits that do not have a score.
        if score is None:
            continue

        ver_num = utils.extract_int(version)

        commits.append(
            (
                ver_num if (ver_num is not None) else version,
                score,
                committed_at,
                utils.round_run_time(run_time),
                added,
                deleted,
                html.make_anchor_tag("Open", {"href": url}),
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

    assert len(commits[0]) == len(headers)

    return commits, headers


def make_profile(kernel_link, thumbnail, commit_table, meta_table):
    return f"""
<br>

# {kernel_link}

{thumbnail}

### Kernel Information

{meta_table}

### Commit History

The highlighted row(s) corresponds to the best score.

{commit_table}
""".strip()


def extract_kernels(soup):
    kernels = []

    for ker in soup.select("div.block-link--bordered"):
        if len(ker.select("div.kernel-list-item__score")) == 0:
            continue

        name = ker.select("div.kernel-list-item__name")[0].text
        url = TOP_URL + ker.select("a.block-link__anchor")[0].get("href")
        kernels.append({"name": name, "url": url, **extract_kernel_metadata(ker)})
    return kernels


def highlight_best_score(row, best_score):
    should_highlight = float(row["Score"]) == float(best_score)
    return [
        ("background-color: #d5fdd5" if should_highlight else "")
        for _ in range(len(row))  # len(row) returns the number of columns.
    ]


def iter_kernels(comp_slug, max_num_kernels):
    driver = create_chrome_driver()

    comp_url = f"{TOP_URL}/c/{comp_slug}/notebooks"

    TIMEOUT = 15  # seconds

    # Open the notebooks tab.
    driver.get(comp_url)

    # Click `Sort By` select box.
    WebDriverWait(driver, TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.Select-value"))
    )
    sort_by = driver.find_element_by_css_selector("div.Select-value")
    sort_by.click()

    # Select `Best score` option.
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

    for ker_idx, kernel_meta in enumerate(kernels[:num_kernels]):
        print(f"Processing ({ker_idx + 1} / {num_kernels})")

        # Open the kernel.
        driver.get(kernel_meta["url"])

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

        yield driver.page_source, kernel_meta

    driver.quit()


def main():
    input_types = {
        "comp_slug": str,
        "max_num_kernels": int,
        "out_dir": str,
    }
    args = ga.get_action_inputs(input_types) if ga.on_github_action() else parse_args()

    comp_slug = args.comp_slug
    max_num_kernels = args.max_num_kernels
    out_dir = args.out_dir

    profiles = []

    for kernel_html, kernel_meta in iter_kernels(comp_slug, max_num_kernels):
        soup = make_soup(kernel_html)

        # Make a commit history table.
        commits, headers = extract_commits(soup)

        # `premailer.transform` turns CSS blocks into style attributes.
        # See: https://github.com/peterbe/premailer
        commit_table = transform(
            pd.DataFrame(commits, columns=headers)
            .style.apply(
                highlight_best_score, best_score=kernel_meta["best_score"], axis=1
            )
            .hide_index()
            .render()
        )

        meta_table = md.make_table(*format_kernel_metadata(kernel_meta))
        kernel_link = md.make_link(kernel_meta["name"], kernel_meta["url"])
        thumbnail = html.make_thumbnail(
            kernel_meta["thumbnail_src"],
            kernel_meta["tier_src"],
            os.path.join(TOP_URL, kernel_meta["author_id"]),
        )

        profiles.append(make_profile(kernel_link, thumbnail, commit_table, meta_table))

    # Save the output.
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, f"{comp_slug}.md")
    timestamp = "## Last Updated: {}".format(
        datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S (UTC)")
    )
    with open(md_path, "w") as f:
        f.write((2 * "\n").join([DESCRIPTION, timestamp, *profiles]))

    # Convert markdown to notebook.
    nb_path = utils.replace_ext(md_path, ".ipynb")
    utils.markdown_to_notebook(md_path, nb_path)

    # Set action outputs.
    if ga.on_github_action():
        ga.set_action_outputs(
            {
                "markdown_path": md_path,
                "markdown_name": os.path.basename(md_path),
                "notebook_path": nb_path,
                "notebook_name": os.path.basename(nb_path),
            }
        )


if __name__ == "__main__":
    main()

import os
import argparse
import traceback
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import jupytext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from tqdm import tqdm


driver = None
TOP_URL = "https://www.kaggle.com"
TIMEOUT = 15
OUT_DIR = "output"
HEADER = """
## This kernel is automatically updated by [harupy/kernel-profiler](https://github.com/harupy/kernel-profiler).
## Last Updated: {}
""".strip()


def build_driver():
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


def parse_args():
    parser = argparse.ArgumentParser(description="Kernel Profiler")
    parser.add_argument("-c", "--comp-slug", help="competition slug (e.g. titanic)")
    return parser.parse_args()


def chromedriver_exists():
    return os.path.exists("chromedriver")


def make_soup(html):
    return BeautifulSoup(html, "lxml")


def get_kernel_meta(kernel):
    return {
        "author_name": kernel.select("span.tooltip-container")[0]
        .get("data-tooltip")
        .strip(),
        "author_id": kernel.select("a.avatar")[0].get("href").strip("/"),
        "thumbnail_src": kernel.select("img.avatar__thumbnail")[0].get("src").strip(),
        "vote_count": kernel.select("span.vote-button__vote-count")[0].text.strip(),
        "comment_count": kernel.select("a.kernel-list-item__info-block--comment")[
            0
        ].text.strip(),
        "last_updated": kernel.select("div.kernel-list-item__details > span")[
            0
        ].text.strip(),
        "best_score": kernel.select("div.kernel-list-item__score")[0].text.strip(),
    }


def utcnow():
    return datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S (UTC)")


def extract_public_score(html):
    m = re.search(r'"publicScore":"(.+?)"', html)
    return float(m.group(1)) if m else ""


def extract_best_public_score(html):
    m = re.search(r'"bestPublicScore":([^,]+)', html)
    return float(m.group(1)) if m else ""


def make_link(text, url):
    return f"[{text}]({url})"


def make_row(items):
    row = "|".join(map(str, items))
    return f"|{row}|"


def make_table(header, data):
    rows = []
    rows.append(make_row(header))
    rows.append(make_row(["-" for _ in range(len(header))]))
    rows.extend([make_row(items) for items in data])
    return "\n".join(rows)


def make_thumbnail(meta):
    thumbnail_template = '<img src="{}" alt="{}" width="72" height="72">'
    thumbnail = thumbnail_template.format(meta["thumbnail_src"], meta["author_name"])
    author_url = os.path.join(TOP_URL, meta["author_id"])
    return '<a href="{}" style="display: inline-block">{}</a>'.format(
        author_url, thumbnail
    )


def make_meta_table(meta):
    author_link = make_link(
        meta["author_name"], os.path.join(TOP_URL, meta["author_id"])
    )
    header = ["Key", "Value"]
    meta_table = [
        ("Author", author_link),
        ("Best Score", meta["best_score"]),
        ("Vote Count", meta["vote_count"]),
        ("Comment Count", meta["comment_count"]),
        ("Last Updated", meta["last_updated"]),
    ]
    return make_table(header, meta_table)


def make_commit_table(commits):
    commit_data = []

    for commit in tqdm(commits):
        version = commit.select("a:nth-of-type(2)")[0]
        committed_at = commit.find("span", recursive=False).text.strip()
        added = commit.select("span:nth-of-type(2)")[0].text.strip()
        deleted = commit.select("span:nth-of-type(3)")[0].text.strip()
        href = version.get("href")
        if href is None:
            continue

        url = TOP_URL + href

        # Ignore failed commits.
        icon = commit.select("a:nth-of-type(1) > svg")[0].get("data-icon")
        if icon == "times-circle":
            continue

        # Extract the public score.
        resp = requests.get(url)
        score = extract_public_score(resp.text)

        if score == "":
            continue

        commit_data.append(
            (
                version.text.strip(),
                score,
                committed_at,
                added,
                deleted,
                make_link("Open", url),
            )
        )

    header = ["Version", "Score", "Committed at", "Added", "Deleted", "Link"]
    return make_table(header, commit_data)


def make_profile(kernel_link, commit_table, meta):
    thumbnail = make_thumbnail(meta)
    meta_table = make_meta_table(meta)
    return f"""
<br>

# {kernel_link}

{thumbnail}

### Kernel Information
{meta_table}

### Commit History
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


def main():
    if on_github_action():
        comp_slug = get_action_input("slug")
    else:
        args = parse_args()
        comp_slug = args.comp_slug

    comp_url = f"https://www.kaggle.com/c/{comp_slug}/notebooks"

    profiles = []
    try:
        # open the notebook page.
        driver.get(comp_url)

        # click 'Sort By' select box.
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.KaggleSelect"))
        )
        sort_by = driver.find_element_by_css_selector("div.KaggleSelect")
        sort_by.click()

        # select 'Best score'.
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.Select-menu-outer"))
        )
        options = driver.find_elements_by_css_selector("div.Select-menu-outer div")
        best_score = [opt for opt in options if opt.text == "Best Score"][0]
        best_score.click()

        # parse kernels.
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.block-link__anchor"))
        )
        soup = make_soup(driver.page_source)
        kernels = soup.select("div.block-link--bordered")
        kernels = [
            (
                ker.select("div.kernel-list-item__name")[0].text,  # kernel name
                TOP_URL
                + ker.select("a.block-link__anchor")[0].get("href"),  # kernel url
                get_kernel_meta(ker),
            )  # kernel metadata
            for ker in kernels
        ]
        num_kernels = len(kernels)

        for ker_idx, (ker_title, ker_url, ker_meta) in enumerate(kernels):
            print(f"Processing {ker_url} ({ker_idx + 1} / {num_kernels})")

            # Open the kernel.
            driver.get(ker_url)

            # Open the commit table.
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.fa-history"))
            )
            commit_link = driver.find_element_by_css_selector("span.fa-history")
            commit_link.click()

            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.vote-button__voters-modal-title")
                )
            )
            soup = make_soup(driver.page_source)

            # Process commit history.
            pattern = r"VersionsPaneContent_IdeVersionsTable.+"
            commits = soup.find("table", {"class": re.compile(pattern)}).select(
                "tbody > div"
            )
            commit_table = make_commit_table(commits)
            kernel_link = make_link(ker_title, ker_url)
            profiles.append(make_profile(kernel_link, commit_table, ker_meta))

        # save the result with a timestamp.
        os.makedirs(OUT_DIR, exist_ok=True)
        out_path = os.path.join(OUT_DIR, f"{comp_slug}.md")
        with open(out_path, "w") as f:
            f.write((2 * "\n").join([HEADER.format(utcnow())] + profiles))

        # Convert markdown to notebook.
        to_notebook(out_path)

    except Exception:
        print(traceback.format_exc())
        with open("error.html", "w") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = build_driver()
    main()

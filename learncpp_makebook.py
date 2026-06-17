#!/usr/bin/env python3
# Title:         learncpp.com book creator
# Version:       1.0 (Python port)
# Original date: 05/31/2026
# Author:        Steven Magana-Zook
# Input:         parameters of website address and output format
# Output:        full book of the website
# Description:   The script creates the learncpp book in 4 steps:
#                STEP1: crawl all links to content from the index page and create an index table
#                STEP2: download all html files from these links
#                STEP3: remove all html frames that do not go into the book
#                STEP4: combine all html files to the book
#
# Dependencies (install with pip):
#   pip install requests lxml pandas

import argparse
import glob
import hashlib
import os
import re
import subprocess
import time

import pandas as pd
import requests
from lxml import html as lxml_html
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# PARAMETERS ---------------------------------------------------------------
HOMEPAGE = "https://www.learncpp.com/"          # page with the index table
TUTORIAL_PAGE = "https://www.learncpp.com/cpp-tutorial/"  # html dir with actual tutorials
REQUEST_TIMEOUT = 60                            # seconds per request
DOWNLOAD_DELAY = 1.0                            # seconds between downloads (be polite)

parser = argparse.ArgumentParser(description="Download learncpp.com and convert to an e-book.")
parser.add_argument(
    "--format", dest="output_format", default="epub3",
    help="Output format passed to pandoc (default: epub3)",
)
parser.add_argument(
    "--output", dest="output_file_name", default="learncpp_book.epub",
    help="Output file name (default: learncpp_book.epub)",
)
args = parser.parse_args()

OUTPUT_FORMAT = args.output_format
OUTPUT_FILE_NAME = args.output_file_name

# HTTP session with browser User-Agent and automatic retries
_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})
_retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=_retry))
_session.mount("http://", HTTPAdapter(max_retries=_retry))


# FUNCTIONS ----------------------------------------------------------------
def _parse_lxml_table(table_node) -> list[list[str]]:
    """Return a list-of-rows (each row is a list of cell text strings) for an lxml table element."""
    rows = []
    for tr in table_node.xpath(".//tr"):
        cells = tr.xpath(".//td|.//th")
        rows.append([c.text_content().strip() for c in cells])
    return rows


def _download_image(url: str, images_dir: str) -> str | None:
    """Download an image to images_dir and return the relative path, or None on failure."""
    try:
        # Derive a safe local filename from the URL path
        url_path = url.split("?")[0]  # strip query strings
        filename = os.path.basename(url_path) or "image"
        # Prefix with a hash of the full URL to avoid collisions from same-named files
        prefix = hashlib.md5(url.encode()).hexdigest()[:8]
        local_name = f"{prefix}_{filename}"
        local_path = os.path.join(images_dir, local_name)

        if not os.path.exists(local_path):
            r = _session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)

        return f"images/{local_name}"
    except Exception as e:
        print(f"  [WARNING] Could not download image {url}: {e}")
        return None


def edit_html(file_in: str, file_out: str, images_dir: str) -> None:
    """Extract only the chapter title and body content from a downloaded HTML file.

    Downloads all images locally and rewrites src attributes so the epub is
    fully self-contained and pandoc does not need to fetch remote resources.
    Produces a minimal HTML document with the <h1> at the top level of <body>
    so that pandoc can correctly detect chapter boundaries and build the TOC.
    """
    print(f"Processing file {file_in}")
    with open(file_in, "rb") as f:
        content = f.read()

    page = lxml_html.fromstring(content)

    # Extract the chapter title (h1.entry-title) and the article body content
    title_nodes = page.xpath('//h1[contains(@class,"entry-title")]')
    content_nodes = page.xpath('//div[contains(@class,"entry-content")]')

    title_html = (
        lxml_html.tostring(title_nodes[0], encoding="unicode")
        if title_nodes else ""
    )
    content_html = (
        lxml_html.tostring(content_nodes[0], encoding="unicode")
        if content_nodes else ""
    )

    # Fallback: if the page has no article structure (e.g. the index table),
    # keep the full body content as-is.
    if not title_nodes and not content_nodes:
        body_nodes = page.xpath("//body")
        fallback = (
            lxml_html.tostring(body_nodes[0], encoding="unicode")
            if body_nodes else lxml_html.tostring(page, encoding="unicode")
        )
        # Unwrap the outer <body> tag so we get just the inner HTML
        fallback = re.sub(r'^<body[^>]*>', '', fallback, count=1)
        fallback = re.sub(r'</body>$', '', fallback)
        body_inner = fallback
    else:
        body_inner = title_html + "\n" + content_html

    # Download all remote images and rewrite src attributes to local paths
    def rewrite_images(html_str: str) -> str:
        def replace_src(match):
            src = match.group(1)
            if src.startswith("http://") or src.startswith("https://"):
                local = _download_image(src, images_dir)
                if local:
                    return f'src="{local}"'
            return match.group(0)
        return re.sub(r'src="(https?://[^"]+)"', replace_src, html_str)

    body_inner = rewrite_images(body_inner)

    minimal_html = (
        "<!DOCTYPE html>\n"
        "<html><head><meta charset='utf-8'/></head>\n"
        "<body>\n"
        + body_inner +
        "\n</body></html>\n"
    )

    with open(file_out, "w", encoding="utf-8") as f:
        f.write(minimal_html)


# PROGRAM ------------------------------------------------------------------
# STEP1: crawl all links to content from the index page and create an index table
print("** Starting creation of index table (STEP1)")

response = _session.get(HOMEPAGE, timeout=REQUEST_TIMEOUT)
response.raise_for_status()
page = lxml_html.fromstring(response.content)

# The site now uses a div-based layout (class="lessontable-row") instead of HTML tables.
# Each row has a number div and a title div containing the link.
lesson_rows = page.xpath('//div[@class="lessontable-row"]')

records = []
for row in lesson_rows:
    number_nodes = row.xpath('.//div[@class="lessontable-row-number"]')
    title_nodes = row.xpath('.//div[@class="lessontable-row-title"]//a')

    if not number_nodes or not title_nodes:
        continue

    chapter = number_nodes[0].text_content().strip()
    name = title_nodes[0].text_content().strip()
    href = title_nodes[0].get('href', '').strip()

    if not chapter or not name or not href:
        continue

    records.append({'chapter': chapter, 'name': name, 'href': href})

tb = pd.DataFrame(records)
tb = tb.reset_index(drop=True)

# Strip URL prefix to get bare slugs
tb["links"] = tb["href"].apply(
    lambda l: re.sub(r'https://www\.learncpp\.com/cpp-tutorial/', '', l, count=1)
)
tb = tb.drop(columns=["href"])

# Sanitize names: replace "/" with "-" (avoids filesystem issues)
tb["name"] = tb["name"].str.replace("/", "-", regex=False)

# Zero-padded index to keep chapters in the correct order in the book
tb["index"] = [str(i + 1).zfill(4) for i in range(len(tb))]

# Write index table to HTML (mirrors write_tableHTML)
os.makedirs("html_raw", exist_ok=True)
tb[["chapter", "name"]].to_html("html_raw/0000---index.html", index=False)

# STEP2: download all html files from these links
print("** Starting downloads (STEP2)")

for _, row in tb.iterrows():
    url = TUTORIAL_PAGE + row["links"]
    dest = f"html_raw/{row['index']}---{row['chapter']}---{row['name']}.html"
    print(f"  Downloading {row['chapter']} -> {dest}")
    r = _session.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    time.sleep(DOWNLOAD_DELAY)

html_files = os.listdir("html_raw")
assert len(html_files) == len(tb) + 1, (
    f"Expected {len(tb) + 1} files, got {len(html_files)}"
)
print(f"** Successfully downloaded {len(tb)} html files.")

# STEP3: remove all html frames that do not go into the book and write to html_edit dir
print("** Starting html editing (STEP3)")
os.makedirs("html_edit", exist_ok=True)
images_dir = os.path.join("html_edit", "images")
os.makedirs(images_dir, exist_ok=True)

for filename in sorted(html_files):
    edit_html(
        file_in=f"html_raw/{filename}",
        file_out=f"html_edit/{filename}",
        images_dir=images_dir,
    )

assert len(os.listdir("html_raw")) == len(glob.glob("html_edit/*.html")), (
    "File count mismatch after editing"
)

# STEP4: combine all html files to the book (requires pandoc installed on the system)
print("** Starting book conversion (STEP4)")
html_edit_files = sorted(
    f for f in glob.glob("html_edit/*.html")
    if not os.path.basename(f).startswith("0000---")
)
cmd = [
    "pandoc", "-s", *html_edit_files,
    "-f", "html",
    "-t", OUTPUT_FORMAT,
    "--toc",
    "--toc-depth", "1",
    "--resource-path", "html_edit",
    "--metadata", "title=LEARN C++",
    "--metadata", "author=Alex",
    "--metadata", "author=Nascardriver",
    "--metadata", "author=Cosmin James",
    "-o", OUTPUT_FILE_NAME,
]
subprocess.run(cmd, check=True)

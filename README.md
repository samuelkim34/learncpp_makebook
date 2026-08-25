# learncpp.com book downloader

[learncpp.com](https://www.learncpp.com/) is one of the most appreciated resources to learn C++. Unfortunately, the website is not available off-line. To provide access to the book without access to a computer/internet, this script **downloads the HTML files** and **converts them to a one-file book** that can be read on, for instance, an e-reader.

## Changes in this fork

This fork improves PDF generation in the Python version of the LearnCpp book downloader.

Changes include:

- Detecting WebP images based on their actual contents, even when they are served with `.png` filenames
- Converting WebP images to PNG for compatibility with PDF engines
- Repairing previously cached WebP images saved with misleading file extensions
- Scaling oversized images so they remain within PDF page boundaries
- Wrapping long syntax-highlighted code lines instead of allowing them to run off the page
- Using 0.75-inch PDF margins for better page utilization
- Adding optional `--pdf-engine` support
- Adding Pillow as a Python dependency

Example PDF generation using Tectonic:

```bash
python3 learncpp_makebook.py \
  --format pdf \
  --output learncpp_book.pdf \
  --pdf-engine tectonic
```

Converted books are for private use only and should not be distributed.

## Disclaimer

This program is solely for educational purposes. Note that although running the script to convert these pages is allowed, it is not allowed to distribute the converted book, so please refrain from doing so. As stated on the website:

> Is there a PDF version of this site available for offline viewing?
>
> Unfortunately, there is not. The site is able to stay free for everyone because we’re ad-sponsored -- that model simply doesn’t work in PDF format. You are welcome to convert pages from this website into PDF (or any other) format for your own private use, so long as you do not distribute them.

## Program details

The script creates the learncpp book in 4 steps:

- STEP1: crawl all links to content from the index page and create an index table
- STEP2: download all HTML files from these links
- STEP3: remove all HTML frames that do not go into the book (such as the side panes and comments)
- STEP4: combine all edited HTML files into one book

## Support learncpp.com

If you appreciate the content of this excellent website, please consider supporting the creators by visiting [https://www.learncpp.com/about/#Support](https://www.learncpp.com/about/#Support) and donating.

As mentioned by the creators:

> LearnCpp.com is a totally free website devoted to teaching you to program in C++. Whether you’ve had any prior experience programming or not, the tutorials on this site will walk you through all the steps you’ll need to know in order to create and compile your programs. Becoming an expert programmer won’t happen overnight, but with a little patience, you’ll get there. And LearnCpp.com will show you the way.
>
> Did we mention the site is completely free? And not free as in “First one is free, man!”, nor “This wonderful synopsis of our content is completely free. Full access for 3 months is only $129.99!”. LearnCpp.com is totally, 100% free, no strings, no catches, no hidden fees, no taxes, and no license and documentation charges.
>
> So, the obvious question is, “what’s in it for us?”. Two things:
>
> - We love to teach, and we love to talk about programming. This site allows us to do that without having to get a PhD, grade homework, and deal with students who need to have the final moved because their “cat just died” (sorry kitty!). Furthermore, our readers are creative, inventive, and very intelligent -- sometimes they teach us stuff in return! So we learn while we teach you, and that makes us better in our careers or hobbies. Plus, it allows us to give something back to the internet community at large. We’re just trying to make the world a better place, okay!?! (*sniff*)
> - Advertising revenues. See those adsense ads on the right? Every time someone clicks one, we make a few cents. It’s not much, but it’s (hopefully) enough to at least pay the hosting fees and maybe buy ourselves a Hawaiian pizza and a pint of Newcastle every once in a while\*.
>
> (\* Beer and programming don’t mix. Please code responsibly.)

## Scripts

Two implementations are available:

| Script | Language | Status |
|---|---|---|
| `learncpp_makebook.py` | Python 3 | Current, actively maintained |
| `learncpp_makebook.R` | R | Original, may be outdated |

The Python port (`learncpp_makebook.py`) is the recommended version. It includes a browser-like User-Agent header, automatic retry logic with exponential backoff to handle slow or rate-limiting responses from the server, and is current with the redesigned learncpp website.

## Requirements

### Python (recommended)

- **Python 3.10+**
- Install the required Python packages with:

```bash
pip install -r requirements.txt
```

The Python dependencies are:

- `requests`
- `lxml`
- `pandas`
- `Pillow`

- **Pandoc** is required for the final conversion step. See [Pandoc's installation instructions](https://pandoc.org/installing.html).

Without Pandoc, the HTML files can still be downloaded and edited, but no single-file book will be generated.

PDF output additionally requires a Pandoc-supported PDF engine, such as:

- Tectonic
- pdflatex
- xelatex

### R (original)

Requires an R installation with `Rscript` on the PATH. See [https://www.r-project.org/](https://www.r-project.org/).

The following R packages are required: `tidyverse`, `rvest`, and `tableHTML`. Install each with:

```r
install.packages("package_name")
```

Also requires **Pandoc** for the final conversion step.

### Cloning

To clone the repository, you need Git installed. See [Atlassian's Git installation guide](https://www.atlassian.com/git/tutorials/install-git).

## Usage

### Python

Clone this fork and install the dependencies:

```bash
git clone https://github.com/samuelkim34/learncpp_makebook.git
cd learncpp_makebook
pip install -r requirements.txt
```

By default, the script produces an EPUB3 file named `learncpp_book.epub`:

```bash
python3 learncpp_makebook.py
```

Both the output format and file name can be overridden on the command line:

| Argument | Description | Default |
|---|---|---|
| `--format FORMAT` | Output format passed to Pandoc | `epub3` |
| `--output FILENAME` | Output file name | `learncpp_book.epub` |
| `--pdf-engine ENGINE` | Optional PDF engine passed to Pandoc | Pandoc default |

Examples:

```bash
# Default: EPUB3 output
python3 learncpp_makebook.py

# PDF output using Pandoc's default PDF engine
python3 learncpp_makebook.py --format pdf --output learncpp_book.pdf

# PDF output using Tectonic
python3 learncpp_makebook.py \
  --format pdf \
  --output learncpp_book.pdf \
  --pdf-engine tectonic

# Custom EPUB filename
python3 learncpp_makebook.py --output my_cpp_book.epub

# Show all options
python3 learncpp_makebook.py --help
```

The script creates two working directories (`html_raw/` and `html_edit/`) and writes the final book to the specified output file.

### PDF output

PDF output includes additional handling for compatibility and readability.

#### WebP image handling

Some images on LearnCpp are served as WebP image data despite their URLs ending in `.png`. These images may not be supported directly by PDF engines such as XeTeX or Tectonic.

The Python script checks the actual image format using Pillow and automatically converts WebP images to PNG before PDF generation.

Previously cached WebP files are also detected and converted when possible.

#### Image sizing

Oversized images and screenshots are automatically scaled to remain within the printable area of the PDF while preserving their aspect ratio.

#### Code wrapping

Long syntax-highlighted code lines are wrapped rather than extending beyond the right edge of the page.

Continuation markers may appear where long lines are wrapped.

#### PDF margins

PDF output uses 0.75-inch margins to make better use of the available page width while retaining comfortable spacing around the content.

#### Selecting a PDF engine

A PDF engine can optionally be selected using `--pdf-engine`.

For example, with Tectonic:

```bash
python3 learncpp_makebook.py \
  --format pdf \
  --output learncpp_book.pdf \
  --pdf-engine tectonic
```

If `--pdf-engine` is not specified, Pandoc uses its normal default PDF engine.

### R

```bash
git clone https://github.com/samuelkim34/learncpp_makebook.git
cd learncpp_makebook

# If needed, change the output format and file name in the script's parameters
Rscript learncpp_makebook.R
```

## Generated files

Running the Python script creates:

```text
html_raw/
html_edit/
```

and the requested output file, for example:

```text
learncpp_book.epub
learncpp_book.pdf
```

These generated files are not intended to be committed to the repository.

In accordance with LearnCpp's policy, generated books should only be used privately and should **not be distributed**.
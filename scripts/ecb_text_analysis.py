from pathlib import Path
# pathlib is a built-in Python module that helps you work with file paths, like where files and folders are on your computer.
# Path = a class in pathlib module, the main tool you actually use.
import re
# a Python module for working with text patterns, called regular expressions.
# basically: search, match, and manipulate text in smart ways
import requests
# requests = a tool that lets Python access the internet like a browser.
from bs4 import BeautifulSoup
# Take a tool called BeautifulSoup from a library called bs4
# BeautifulSoup = a tool that helps you read and extract data from websites easily

# Store the webpage address in a variable called URL
URL = "https://www.ecb.europa.eu/press/press_conference/monetary-policy-statement/2025/html/ecb.is250605~f00a36ef2b.en.html"

# Create folder paths for data and outputs
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")

# Create the folders if they do not already exist.
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Cleaning messy text
def clean_whitespace(text: str) -> str:
    # HTML text can contain extra spaces, tabs, and line breaks.
    # This function turns repeated whitespace into a single clean space.
    return re.sub(r"\s+", " ", text).strip() # \s means whitespace, + means “one or more”

# Send a browser-like identity to the website. We are pretending to be a browser.
headers = {
    "User-Agent": "Mozilla/5.0 (beginner text analysis tutorial)"
}

# Download the ECB webpage.
# timeout=30 means Python will wait up to 30 seconds before giving up.
response = requests.get(URL, headers=headers, timeout=30)
# result is stored in 'response' containing the webpage data

# Stop the script immediately if the website returns an error code.
# For example, 404 means page not found and 500 means server error.
# .raise_for_status() checks if the request was successful and raises an error if it was not.
response.raise_for_status()

# Parse the HTML with BeautifulSoup so we can search inside it. Parse = break messy data into a structured, usable form
# "lxml" is the parser engine. It is fast and commonly used.
soup = BeautifulSoup(response.text, "lxml")

# Find the main content block that holds the press conference text. Useful content is in main div.section.
section = soup.select_one("main div.section")
if section is None:
    raise RuntimeError("Could not find the article section. The page structure may have changed.")

# Remove unwanted parts of a webpage in the analysis text.
for unwanted in section.select('script, style, a[href="#qa"], .ecb-publicationDate'):
    unwanted.decompose() # Deletes them completely from the page structure

# Prepare an empty list to collect each cleaned heading or paragraph.
text_blocks = []

# Loop through headings and paragraphs inside the section.
# We use both h2 and p because the section titles are meaningful text too.
for element in section.find_all(["h2", "p"]):
    classes = element.get("class", []) # Checks if that element has a CSS class, []= if no class exists, return an empty list instead of crashing

    # Skip the subtitle line with speaker names.
    if "ecb-pressContentSubtitle" in classes:
        continue

    # Extract visible text from the HTML tag and clean its spacing.
    text = clean_whitespace(element.get_text(" ", strip=True))

    # Only keep non-empty text blocks.
    if text:
        text_blocks.append(text) 
    # Adds the text into a list called text_blocks, append = add to the end of the list

# Combine all text blocks into one long script.
# We put blank lines between blocks to keep the text readable.
full_text = "\n\n".join(text_blocks)   # \n\n = put two line breaks between each one

# Choose the output filename for the cleaned text.
text_path = DATA_DIR / "ecb_press_conference_2026-06-05.txt"

# Save the full script as a UTF-8 text file. UTF-8 is like a universal translator
# Converts it into machine-readable code and back correctly
text_path.write_text(full_text, encoding="utf-8")

# Print checks so we can check what happened.
print("Saved text to:", text_path)
print("Number of extracted text blocks:", len(text_blocks))
print()
print("Preview:")
print(full_text[:800])


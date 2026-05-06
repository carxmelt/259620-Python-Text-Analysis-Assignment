from pathlib import Path
# pathlib is a built-in Python module that helps you work with file paths, like where files and folders are on your computer.
# Path = a class in pathlib module, the main tool you actually use.
from collections import Counter
# Counter helps to count how many times each item appears in a list or collection.
import re
# a Python module for working with text patterns, called regular expressions.
# basically: search, match, and manipulate text in smart ways
import requests
# requests = a tool that lets Python access the internet like a browser.
import pandas as pd
# pandas = a library for working with data, especially tables (like Excel spreadsheets).
import matplotlib.pyplot as plt
# matplotlib.pyplot = a tool for making graphs and charts in Python.
from bs4 import BeautifulSoup
# Take a tool called BeautifulSoup from a library called bs4
# BeautifulSoup = a tool that helps you read and extract data from websites easily
from textblob import TextBlob
from wordcloud import STOPWORDS, WordCloud

# Store the webpage address in a variable called URL
URL = "https://www.ecb.europa.eu/press/press_conference/monetary-policy-statement/2025/html/ecb.is250605~f00a36ef2b.en.html"

# Create folder paths for data and outputs
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")

# Create the folders if they do not already exist.
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Defining functions.
# 1. Cleaning messy text
def clean_whitespace(text: str) -> str:
    # HTML text can contain extra spaces, tabs, and line breaks.
    # This function turns repeated whitespace into a single clean space.
    return re.sub(r"\s+", " ", text).strip() # \s means whitespace, + means “one or more”
# 2. converts numbers into words for sentiment analysis
def sentiment_label(polarity: float) -> str:
    # Convert the numeric TextBlob polarity score into a simple label.
    # TextBlob polarity ranges from -1 to 1.
    """Convert a TextBlob polarity score into a simple label."""
    if polarity >= 0.1:
        return "positive"
    if polarity <= -0.1:
        return "negative"
    return "neutral"
# 3. for wordcloud 
def tokenize_words(text: str, stopwords: set[str]) -> list[str]:
    # Step 6: Break the text into lowercase word tokens.
    # We keep alphabetic words and allow apostrophes or hyphens inside them.
    # Then we remove short words and stopwords.
    """Make a simple list of lowercase words, excluding stopwords."""
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]+", text.lower())
    return [
        token
        for token in tokens
        if len(token) > 2 and token not in stopwords
    ]

# Send a browser-like identity to the website. We are pretending to be a browser.
headers = {
    "User-Agent": "Mozilla/5.0 (i am impostor)"
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

# Sentiment analysis paragraph by paragraph
paragraph_results = [] #create empty list to store results for each paragraph

for i, paragraph in enumerate(text_blocks, 1):  # Start counting paragraphs starting from 1
# enumerate = function that gives you both the index (i) and the value (paragraph) as it loops through text_blocks
    blob = TextBlob(paragraph) # create textblob object for a paragraph
    polarity = blob.sentiment.polarity # extract sentiment score from a paragraph

    paragraph_results.append({
        "paragraph_num": i,
        "paragraph_text": paragraph, 
        "polarity": polarity,
        "subjectivity": blob.sentiment.subjectivity,
        "sentiment_label": sentiment_label(polarity) #Converts the score to a word ("positive", "negative", or "neutral").
    })

# Save to CSV file
df_paragraphs = pd.DataFrame(paragraph_results)
sentiment_path = OUTPUT_DIR / "ecb_sentiment_summary.csv"
df_paragraphs.to_csv(sentiment_path, index=False)

# Start from the default English stopwords used by the wordcloud package.
custom_stopwords = set(STOPWORDS)

# Add domain-specific words that would otherwise dominate the figure.
# These words are common in ECB texts, so removing them helps other themes stand out.
custom_stopwords.update(
    {
        "ecb",
        "euro",
        "area",
        "monetary",
        "policy",
        "inflation",
        "per",
        "cent",
        "will",
        "would",
        "could",
        "also",
        "question",
        "questions",
        "answer",
        "answers",
        "think",
        "going",
    }
)

# Tokenize the clean text and remove stopwords.
tokens = tokenize_words(full_text, custom_stopwords)

# Count how often each remaining word appears.
word_counts = Counter(tokens)

# Save the top 30 words as a CSV table.
top_words = pd.DataFrame(
    word_counts.most_common(30),
    columns=["word", "count"],
)
top_words_path = OUTPUT_DIR / "ecb_top_words.csv"
top_words.to_csv(top_words_path, index=False)

# Build the word cloud image from the full text.
# The display settings control the size, colors, and reproducibility of the figure.
wordcloud = WordCloud(
    width=1200,
    height=700,
    background_color="white",
    stopwords=custom_stopwords,
    colormap="viridis",
    random_state=42,
).generate(full_text)

# Choose the output path for the word cloud image.
wordcloud_path = OUTPUT_DIR / "ecb_wordcloud.png"

# Draw the word cloud with matplotlib and save it as a PNG file.
plt.figure(figsize=(12, 7))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.tight_layout(pad=0)
plt.savefig(wordcloud_path, dpi=200, bbox_inches="tight")
plt.close()

# Print a short summary so we can confirm all output files were created.
print("Saved text to:", text_path)
print("Saved paragraph sentiment analysis to:", sentiment_path)
print("Saved top words table to:", top_words_path)
print("Saved word cloud to:", wordcloud_path)
print()
print("All paragraphs by sentiment:")
print(df_paragraphs[["paragraph_num", "polarity", "sentiment_label"]])
print()
print("Top 10 words after stopword removal:")
print(top_words.head(10))
import re, requests
from bs4 import BeautifulSoup
from google.cloud import language_v1
from google.cloud.language_v1 import enums

# def install(package):
#   import pip
#   pip.main(["install", package])

# install("google-api-python-client")
# install("google-cloud")
# install("google-cloud-language")

#######################################
## Get all Billie Eilish song lyrics ##
#######################################

# This function builds Genius urls from Billie Eilish song titles.
def build_genius_url(song_title):
  kebab_cased = song_title. \
    replace(" ", "-"). \
    replace("!", ""). \
    replace("'", ""). \
    replace("&Burn", "and-vince-staples-burn"). \
    lower()
  return f"https://genius.com/Billie-eilish-{kebab_cased}-lyrics"

song_titles = []
songs = {}

page = requests.get("https://en.wikipedia.org/wiki/Category:Billie_Eilish_songs")
soup = BeautifulSoup(page.content, "html.parser")

groups = soup.find_all(class_="mw-category-group")
for group in groups:
  links = group.find_all("a")
  for link in links:
    tidied = re.sub(r"\(.*\)", "", link.get_text()).strip()
    song_titles.append(tidied)

for song_title in song_titles:
  page = requests.get(build_genius_url(song_title))
  if page.status_code == 200:
    print(f"Fetched \"{song_title}\"")
  else:
    print(f"Failed to fetch \"{song_title}\"")
    continue

  soup = BeautifulSoup(page.content, "html.parser")

  lyrics_div = soup.find(class_="lyrics")
  lyrics = lyrics_div.find("p").get_text()
  songs[song_title] = lyrics

  print(f"Stored lyrics for \"{song_title}\"\n")

##################################################################
## Perform sentiment analysis on all Billie Eilish song lyrics  ##
## using Google Cloud's Natural Language API (requires account) ##
##################################################################

PATH_TO_ACCOUNT_JSON = "./service_account_viewer.json"

def analyze_sentiment(text_content):
  client = \
    language_v1.LanguageServiceClient.from_service_account_json(PATH_TO_ACCOUNT_JSON)
  type_ = enums.Document.Type.PLAIN_TEXT
  language = "en"
  document = {"content": text_content, "type": type_, "language": language}

  encoding_type = enums.EncodingType.UTF8
  return client.analyze_sentiment(document, encoding_type=encoding_type)


for (title, lyrics) in songs.items():
  tidy_lyrics = re.sub(r"\[.*\]\n", "", lyrics)
  response = analyze_sentiment(tidy_lyrics)

  print("#" * (len(title) + 3))
  print(f"## {title}")
  print(f"## Overall sentiment score: {response.document_sentiment.score}")
  print(f"## Overall sentiment magnitude: {response.document_sentiment.magnitude}")
  print("#" * (len(title) + 3))

  for s in response.sentences:
    print(f"{s.text.content} - score: {s.sentiment.score}, mag: {s.sentiment.magnitude}")

import code; code.interact(local=dict(globals(), **locals()))

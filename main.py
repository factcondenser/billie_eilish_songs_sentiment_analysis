import json, os, re, requests
import plotly.graph_objects as go

from bs4 import BeautifulSoup
from google.cloud import language_v1
from google.cloud.language_v1 import enums

###############
## CONSTANTS ##
###############

DECIMAL_PLACES = 2
GITHUB_REPO_NAME = "billie_eilish_songs_sentiment_analysis"
GITHUB_USERNAME = "factcondenser"
PATH_TO_ANALYZED_SONGS_JSON = "analyzed_songs.json"
PATH_TO_CHARTS = "charts"
PATH_TO_GOOGLE_SERVICE_ACCOUNT_JSON = "service_account_viewer.json"
PATH_TO_README = "README.md"
README_CHART_HEIGHT = 285

##########################
## FUNCTION DEFINITIONS ##
##########################

# Uses Google Cloud's Natural Language API to provide sentiment analysis for some text.
def analyze_sentiment(text_content):
  client = language_v1.LanguageServiceClient.from_service_account_json(
    PATH_TO_GOOGLE_SERVICE_ACCOUNT_JSON
  )
  type_ = enums.Document.Type.PLAIN_TEXT
  language = "en"
  document = {"content": text_content, "type": type_, "language": language}

  encoding_type = enums.EncodingType.UTF8
  return client.analyze_sentiment(document, encoding_type=encoding_type)

# Builds a Genius url from a Billie Eilish song title.
def build_genius_url_for_billie_eilish_song(song_title):
  kebab_cased = song_title. \
    replace(" ", "-"). \
    replace("!", ""). \
    replace("'", ""). \
    replace("&Burn", "and-vince-staples-burn"). \
    lower()
  return f"https://genius.com/Billie-eilish-{kebab_cased}-lyrics"

# Removes text in square brackets ("[" and "]") and adds periods to the ends of lines.
def clean_up_genius_lyrics(lyrics):
  return re.sub(r"([^\s.])\n", r"\1.\n", re.sub(r"\[.*\]\n", "", lyrics))

# Fetches items from a Wikipedia set category page.
def fetch_items_from_wikipedia_category(category_name):
  items = []

  page = requests.get(f"https://en.wikipedia.org/wiki/Category:{category_name}")
  soup = BeautifulSoup(page.content, "html.parser")

  groups = soup.find_all(class_="mw-category-group")
  for group in groups:
    links = group.find_all("a")
    for link in links:
      tidied = re.sub(r"\(.*\)", "", link.get_text()).strip()
      items.append(tidied)

  return items

# Fetches song lyrics from a Genius url.
def fetch_genius_lyrics(genius_url):
  page = requests.get(genius_url)
  if not page.ok:
    print(f"Failed to fetch from \"{genius_url}\": Status {page.status_code}")
    return

  soup = BeautifulSoup(page.content, "html.parser")

  lyrics_div = soup.find(class_="lyrics")
  return lyrics_div.find("p").get_text()

# Generate HTML and PNG charts from the songs data.
def generate_charts(songs):
  for song in songs:
    title, overall_score, _overall_magnitude, lines = song.values()
    texts, scores, magnitudes = [], [], []

    for i, line in enumerate(lines):
      text, score, magnitude = line.values()
      texts.append(f"L{i + 1}: {text}")
      scores.append(score)
      magnitudes.append(magnitude)

    path = f"{PATH_TO_CHARTS}/{title}"
    if not os.path.exists(path):
      os.makedirs(path)

    fig = go.Figure(
      data=[go.Bar(x=texts, y=scores)],
      layout=go.Layout(
          title=dict(
            text=f"{title} (overall score: {round(overall_score, DECIMAL_PLACES)})",
            font=dict(size=24)
          ),
          yaxis=dict(
            title="sentiment score",
            autorange=False,
            range=[-1.0, 1.0]
          )
      )
    )
    fig.write_html(f"{path}/{title}.html")

    fig.update_layout(
      xaxis=dict(
        showticklabels=False
      ),
      autosize=False,
      height=500
    )
    fig.write_image(f"{path}/{title}.png")

# Generate a README from the songs data (assumes code is hosted on GitHub).
def generate_readme(songs):
  sorted_unique_scores = sorted(list(set(map(lambda x : x["score"], songs))))
  lowest_score = sorted_unique_scores[0]
  second_highest_score = sorted_unique_scores[-2]
  highest_score = sorted_unique_scores[-1]

  lowest_scoring = list(filter(
    lambda x : x["score"] == lowest_score,
    sorted(songs, key=lambda x : (x["score"], x["title"]))
  ))
  highest_scoring = list(filter(
    lambda x : x["score"] in [highest_score, second_highest_score],
    sorted(songs, key=lambda x : (-x["score"], x["title"]))
  ))

  with open(PATH_TO_README, "w") as readme:
    readme.write("### Songs with highest sentiment score\n")
    for song in highest_scoring:
      readme.write(f'{song["title"]} ({round(song["score"], DECIMAL_PLACES)})  \n')

    readme.write("### Songs with lowest sentiment score\n")
    for song in lowest_scoring:
      readme.write(f'{song["title"]} ({round(song["score"], DECIMAL_PLACES)})  \n')

    for song in songs:
      title = song["title"]
      path = f"{PATH_TO_CHARTS}/{title}"
      readme.write(
        f'''
<a href="https://htmlpreview.github.io/?https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/blob/master/{path}/{title}.html">
  <img src="https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/blob/master/{path}/{title}.png" height="{README_CHART_HEIGHT}"/>
</a>
        '''
      )

#################
## MAIN SCRIPT ##
#################

# songs = []

# song_titles = fetch_items_from_wikipedia_category("Billie_Eilish_songs")
# for song_title in song_titles:
#   genius_url = build_genius_url_for_billie_eilish_song(song_title)
#   lyrics = fetch_genius_lyrics(genius_url)
#   tidy_lyrics = clean_up_genius_lyrics(lyrics)
#   analysis_result = analyze_sentiment(tidy_lyrics)

#   song = {
#     "title": song_title,
#     "score": analysis_result.document_sentiment.score,
#     "magnitude": analysis_result.document_sentiment.magnitude,
#     "lines": []
#   }

#   for sentence in analysis_result.sentences:
#     song["lines"].append({
#       "text": sentence.text.content,
#       "score": sentence.sentiment.score,
#       "magnitude": sentence.sentiment.magnitude
#     })

#   songs.append(song)

# # Write songs data to JSON file.
# with open("analyzed_songs.json", "w") as json_file:
#   json.dump(songs, json_file)

# Load songs data from JSON file.
with open("./analyzed_songs.json") as json_file:
  songs = json.load(json_file)

# generate_charts(songs)
generate_readme(songs)

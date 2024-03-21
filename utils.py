import pandas as pd
import ast
import string
from nltk.tokenize import WordPunctTokenizer
from nltk.corpus import stopwords, words
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import PorterStemmer
import re
import mysql.connector
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# custom_nltk_data_dir = "nltk_data/"
# os.makedirs(custom_nltk_data_dir, exist_ok=True)
# nltk.data.path.append(custom_nltk_data_dir)

## Download NLTK data if not already downloaded
# nltk.download('punkt', download_dir=custom_nltk_data_dir)
# nltk.download('stopwords', download_dir=custom_nltk_data_dir)
# nltk.download('wordnet', download_dir=custom_nltk_data_dir)
# nltk.download('words', download_dir=custom_nltk_data_dir)



    
def treat_title(input_data):

  translator = str.maketrans("", "", string.punctuation)
  if isinstance(input_data, str):
    processed_title = input_data.lower().translate(translator).replace(" ", '')
    return processed_title
  elif isinstance(input_data, list):
    processed_titles = [title.lower().translate(translator).replace(" ", '') for title in input_data]
    return processed_titles

def extract_crew(x, process = False):
  crew = []
  try:
    for i in ast.literal_eval(x):
      if (i['department'].lower() == 'directing'):
        if process == True:
          crew.append(i['name'].replace(' ', '').replace('.', '').lower())
        else:
          crew.append(i['name'])
        break
  except:
    for i in x:
      if process == True:
        crew.append(i['name'].replace(' ', '').replace('.', '').lower())
      else:
        crew.append(i['name'])
      break

  return ' '.join(crew)

def extract_cast(x):
  cast = []
  try:
    x = ast.literal_eval(x)
    if len(x) > 2:
      for i in range(2):
        cast.append(x[i]['name'].replace(' ', '').replace('.', '').lower())
    else:
      for i in x:
        cast.append(i['name'].replace(' ', '').replace('.', '').lower())
  except:
    if len(x) > 2:
      for i in range(2):
        cast.append(x[i]['name'].replace(' ', '').replace('.', '').lower())
    else:
      for i in x:
        cast.append(i['name'].replace(' ', '').replace('.', '').lower())

  return ' '.join(cast)

def get_year(x):
  if 2020 < x < 2030:
     return '2020s'
  elif 2010 < x < 2020:
     return '2010s'
  elif 2000 < x < 2010:
     return '2000s'
  elif 1990 < x < 2000:
    return '1990s'
  elif 1980 < x < 1990:
    return '1980s'
  elif 1970 < x < 1980:
    return '1970s'
  elif 1960 < x < 1970:
    return '1960s'
  elif 1950 < x < 1960:
    return '1950s'
  elif 1940 < x < 1950:
    return '1940s'
  elif 1930 < x < 1940:
    return '1930s'
  else:
    return 'older'



genre_dict = {"genres":[{"id":28,"name":"Action"},
{"id":12,"name":"Adventure"},
{"id":16,"name":"Animation"},
{"id":35,"name":"Comedy"},
{"id":80,"name":"Crime"},
{"id":99,"name":"Documentary"},
{"id":18,"name":"Drama"},
{"id":10751,"name":"Family"},
{"id":14,"name":"Fantasy"},
{"id":36,"name":"History"},
{"id":27,"name":"Horror"},
{"id":10402,"name":"Music"},
{"id":9648,"name":"Mystery"},
{"id":10749,"name":"Romance"},
{"id":878,"name":"Science Fiction"},
{"id":10770,"name":"TV Movie"},
{"id":53,"name":"Thriller"},
{"id":10752,"name":"War"},
{"id":37,"name":"Western"}]}

def map_genres(genre_ids):
  genre_mapping = {genre['id']: genre['name'] for genre in genre_dict['genres']}
  if isinstance(genre_ids, str):
    genre_ids = ast.literal_eval(genre_ids)
  
  temp_list = [genre_mapping[genre_id].lower() for genre_id in genre_ids]
  genre_list = []
  for i in temp_list:
    genre_list.append(i.replace(' ', '').replace('.', ''))

  return ' '.join(genre_list)


def get_genres_for_display(genre_list):
  genres = []
  for i in genre_list:
    genres.append(i['name'])
  
  return genres


def treat_overview(text):

  text = text.replace("'", '').lower()
  tokenizer = WordPunctTokenizer()
  tokens = tokenizer.tokenize(text)
  text = [token for token in tokens if token.isalnum()]

  return ' '.join(text)



def get_topwords_overview(df):
  stop_words = set(stopwords.words('english'))
  lemmatizer = WordNetLemmatizer()
  # english_word_set = set(words.words())
  ps = PorterStemmer()

  def preprocess_text(text):
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token.isalnum() and token.lower() not in stop_words]
    return ' '.join(tokens)

  df['treated_overview'] = df['treated_overview'].apply(preprocess_text)

  # TF-IDF Vectorizer
  tfidf_vectorizer = TfidfVectorizer()
  tfidf_matrix = tfidf_vectorizer.fit_transform(df['treated_overview'])

  # Get feature names (words)
  feature_names = tfidf_vectorizer.get_feature_names_out()

  # Find the most important keywords based on TF-IDF scores
  top_keywords_indices = tfidf_matrix.sum(axis=0).argsort()[0, ::-1] # Adjust the number of top keywords as needed
  top_words = [feature_names[idx] for idx in top_keywords_indices][0].tolist()[0][:5000]


  def process_text(x, top_words=top_words):
    words = x.split()
    # english_words = [word for word in words if (word.endswith('s') and word[:-1].isnumeric())]
    cleaned_text = ' '.join(words)
    cleaned_text = re.sub(r'\b\d+\b', '', cleaned_text)

    if top_words:
      cleaned_text = ' '.join([word for word in cleaned_text.split() if word in top_words]) #Removes words that are not in top 5000

    stemmed_words = [ps.stem(word) for word in cleaned_text.split()]
    return ' '.join(stemmed_words)
  
  df['treated_overview'] = df['treated_overview'].apply(process_text)
  return df




DATABASE_PASS = os.getenv("DATABASE_PASS")
DATABASE_URL = os.getenv("DATABASE_URL")

def process_data(df):
  df['treated_overview'] = df['overview'].apply(treat_overview)
  df = get_topwords_overview(df)
  df['doc'] = df['adult'] +' '+ df['release_year'] + ' ' + df['treated_overview'] +' '  + df['genres'] +' ' + df['cast'] +' '+ df['crew'] + ' ' +df['keywords']
  df = df.drop(columns = ['treated_overview'])

  conn = mysql.connector.connect(user='root', password=DATABASE_PASS, host='127.0.0.1', database='movie')
  cursor = conn.cursor()
  cursor.execute("DROP TABLE movies_dataset")
  conn.commit()
  cursor.close()
  conn.close()
  print("db deleted")

  engine = create_engine(DATABASE_URL)
  df.to_sql("movies_dataset", con=engine, if_exists='append', index=False)
  print("db added")
  return df



def prepare_tags(data):

  data = process_data(data)
  tfidf = TfidfVectorizer(stop_words = 'english')
  tags = tfidf.fit_transform(data['doc'])

  genres = set()
  for genre in data['genres'].str.split():
      genres.update(genres)
  genres = list(genres)

  keywords = set()
  for keyword in data['keywords'].str.split():
      keywords.update(keyword)
  keywords = list(keywords)

  directors = set()
  for director in data['crew'].str.split():
      directors.update(director)
  directors = list(directors)

  feature_names = list(tfidf.get_feature_names_out())
  genre_indices = []
  for genre in genres:
    try:
      index = feature_names.index(genre)
      genre_indices.append(index)
    except:
      pass

  keywords_indices = []
  for keyword in keywords:
    try:
      index = feature_names.index(keyword)
      keywords_indices.append(index)
    except:
      pass

  dir_indices = []
  for dir in directors:
    try:
      index = feature_names.index(dir)
      dir_indices.append(index)
    except:
      pass

  tags[:,genre_indices] *= 2
  tags[:,dir_indices] *= 2.5
  tags[:,keywords_indices] *= 2.5

  return tags, genre_indices, dir_indices, keywords_indices, feature_names, data

def extract_data_from_db(columns):

  conn = mysql.connector.connect(user='root', password=DATABASE_PASS, host='127.0.0.1', database='movie')
  cursor = conn.cursor()

  cursor.execute(f"SELECT {', '.join(columns)} FROM movies_dataset")
    
  rows = cursor.fetchall()
  df = pd.DataFrame(rows, columns=columns)
  df = df.dropna(subset=['title'])
  df = df[~df.title.duplicated()].reset_index()

  cursor.close()
  conn.close()

  return df

def extract_rows_from_db(columns, ids):

  conn = mysql.connector.connect(user='root', password=DATABASE_PASS, host='127.0.0.1', database='movie')
  cursor = conn.cursor()

  if isinstance(ids, list):
    ids_str = ', '.join(map(str, ids))
    cursor.execute(f"SELECT {', '.join(columns)} FROM movies_dataset WHERE id IN ({ids_str})")

  elif isinstance(ids, int):
    cursor.execute(f"SELECT {', '.join(columns)} FROM movies_dataset WHERE id IN ({str(ids)})")

  rows = cursor.fetchall()
  df = pd.DataFrame(rows, columns=columns)
  # df = df.dropna(subset=['title'])
  # df = df[~df.title.duplicated()].reset_index(drop=True)

  cursor.close()
  conn.close()

  return df

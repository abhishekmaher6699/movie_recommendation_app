import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
from utils import treat_title,map_genres, get_year, treat_overview, extract_cast, extract_crew
from requests.exceptions import RequestException
from sqlalchemy import create_engine
import pymysql

from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("TMDB_KEY")

def fetch_moviedata(page):
    url = f"https://api.themoviedb.org/3/movie/top_rated?language=en-US&page={page}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {key}"
    }
    response = requests.get(url, headers=headers)

    return response

def get_keywords(idx, movies_dict):
  
  url = f"https://api.themoviedb.org/3/movie/{idx}/keywords"
  headers = {
      "accept": "application/json",
      "Authorization": f"Bearer {key}"
  }
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    movie = response.json()
    keywords = []
    for i in movie['keywords']:
        kword = i['name'].replace(' ', '').replace('.', '').lower()
        keywords.append(kword)

    movies_dict[idx]['keywords'] = ' '.join(keywords)
  else:
     response.raise_for_status()

def get_credits(idx, movies_dict):

  url = f"https://api.themoviedb.org/3/movie/{idx}/credits?language=en-US"
  headers = {
      "accept": "application/json",
      "Authorization": f"Bearer {key}"
      }

  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    movie = response.json()
    movies_dict[idx]['cast'] = extract_cast(movie['cast'])
    movies_dict[idx]['crew'] = extract_crew(movie['crew'])
  else:
     response.raise_for_status()


def store_data(df):
    print("Started storing data in db")
    engine = create_engine(os.getenv("DATABASE_URL"))
    df.to_sql("dataset", con=engine, if_exists='append', index=False)


def transform_data(dict):
   
    df = pd.DataFrame(dict).T
    # df = get_topwords_overview(df)
    # df['doc'] = df['adult'] +' '+ df['release_year'] + ' ' + df['treated_overview'] +' ' + df['genres'] +' ' + df['cast'] +' '+ df['crew'] + ' ' +df['keywords']
    df['title'] = df['title'].drop_duplicates()
    df = df.reset_index()

    return df



def main(start_page, end_page):
    try:
        movies_dict = {}
        before = time.time()
        for page in range(start_page, min(end_page+1, 501)):
            
            response = fetch_moviedata(page)
            for movie in response.json()['results']:
                id_ = movie['id']

                movies_dict[id_] = {
                    'display_title' : movie['title'],
                    'title': treat_title(movie['title']),
                    'id_' : movie['id'],
                    'overview' : movie['overview'],
                    'treated_overview': treat_overview(movie['overview']),
                    'genres' : map_genres(movie['genre_ids']),
                    'poster_path' : movie['poster_path'],
                    'adult' : 'adult' if movie['adult'] else 'notadult',
                    'vote_count' : movie['vote_count'],
                    'vote_average' : movie['vote_average'],
                    'release_year' :  get_year(pd.to_datetime(movie['release_date'], errors='coerce').year)
                    }
        after = time.time()
        print(f"Chunk {i}-{i+50} completed in {after - before}seconds!")
            
        ids = [movie_data['id_'] for movie_data in movies_dict.values()] 

        before = time.time()
        with ThreadPoolExecutor(max_workers=40) as executor:
            executor.map(lambda idx: get_keywords_wrapper(idx, movies_dict), ids)
        after = time.time()
        print(f"Time taken to fetch keywords for chunk {i}:", after - before)

        before = time.time()
        with ThreadPoolExecutor(max_workers=40) as executor:
            executor.map(lambda idx: get_credits_wrapper(idx, movies_dict), ids)
        after = time.time()
        print(f"Time taken to fetch credits for chunk {i}:", after - before)
        
        df = transform_data(movies_dict)
        store_data(df)

    except RequestException as e:
        print(f"Error occurred: {e}")
        print(f"Retrying chunk {start_page}-{end_page} in 30 seconds...")
        time.sleep(20)
        main(start_page, end_page)
    
    time.sleep(20)

def get_keywords_wrapper(idx, movies_dict):
    retries = 10  # Maximum number of retries for a movie
    while retries > 0:
        try:
            get_keywords(idx, movies_dict)
            return  # Successfully fetched keywords, exit function
        except Exception as e:
            print(f"Error fetching keywords for movie {idx}: {e}")
            retries -= 1
            time.sleep(1)
    print(f"Failed to fetch keywords for movie {idx} after {retries} retries.")


def get_credits_wrapper(idx, movies_dict):
    retries = 50  # Maximum number of retries for a movie
    while retries > 0:
        try:
            get_credits(idx, movies_dict)
            return  # Successfully fetched credits, exit function
        except Exception as e:
            print(f"Retry no. {retries} Error fetching credits for movie {idx}: {e}")
            retries -= 1
            time.sleep(1)

    # Set 'cast' and 'crew' to None if credits couldn't be fetched
    movies_dict[idx]['cast'] = None
    movies_dict[idx]['crew'] = None
    print(f"Failed to fetch credits for movie {idx} after {retries} retries.")


for i in range(0, 500, 50):
    print(f"On page {i}")
    main(i, i+50)
from flask import Flask, render_template, request
from models import get_recommendations
from utils import  extract_rows_from_db, get_genres_for_display
from apis import chatgpt, get_movie
import json
import json.decoder
import time
import threading
import requests

app = Flask(__name__,  static_folder='static')
app.config['CACHE_TYPE'] = 'null'

def get_movie_with_retry(idx):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            response = get_movie(idx)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}. Retrying...")
            retries += 1
    raise Exception("Max retries reached. Unable to fetch data from API.")

def fetch_movie_info(idx, display_info, gpt_response, output_dict):
    try:
        movie_data = get_movie_with_retry(idx)
    except Exception as e:
        print(f" Error occured: {e}")
        movie_data = None

    print(movie_data)
    movie_info = {}
    if gpt_response is not None:
        movie_info['gpt_response'] = gpt_response.get(str(idx), '')
    else:
        pass

    if movie_data is not None:
        movie_info['name'] = movie_data.get('title', '')
        movie_info['release_date'] =  movie_data.get('release_date', '')
        movie_info['ratings'] = round(movie_data.get('vote_average', ''), 1)
        movie_info['overview'] = movie_data.get('overview', '')
        movie_info['poster_path'] =  movie_data.get('poster_path', '')
        movie_info['link'] = movie_data.get('imdb_id', '')
        movie_info['genres'] = get_genres_for_display(movie_data.get('genres', []))

    else:

        movie_info['name'] = output_dict.loc[idx, 'display_title']
        movie_info['ratings'] = round(output_dict.loc[idx, 'rating'], 1)
        movie_info['overview'] =output_dict.loc[idx, 'overview']
        movie_info['poster_path'] =  output_dict.loc[idx, 'poster_path']
        movie_info['genres'] = output_dict.loc[idx, 'genres'].split()    

    display_info.append(movie_info)


def get_gptresponse_with_retry(input_df, output_df):
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            response = json.loads(chatgpt(input_df.T.to_dict(), output_df.T.to_dict()))
            return response
        except json.decoder.JSONDecodeError as e:
            print(f"Request failed: {e}. Retrying...")
            retries += 1
    raise Exception("Max retries reached. Unable to fetch data from API.")

@app.route('/', methods=['GET', 'POST'])
def index():
    # recommendations = []
    display_info = []

    # gpt_response = {}
    movie_name = None
    if request.method == 'POST':
        before = time.time()

        movie_name = request.form.get('movie_name')
        if movie_name:
            try:
                _, recc_ids, input_id = get_recommendations(movie_name)
            except:
                message = "Movie not found! Try to use correct spelling."
                return render_template('index.html', message=message)

            output_dict =  extract_rows_from_db(['id', 'display_title','title','rating','poster_path', 'genres', 'release_year','overview','cast', 'crew', 'keywords' , 'doc'],list(recc_ids.values))
            print("output_dixt done")
            input_dict = extract_rows_from_db(['id', 'display_title','title','genres', 'release_year','overview','cast', 'crew', 'keywords' , 'doc'], int(input_id))
            print("input_dict done")
            try:
                gpt_response = get_gptresponse_with_retry(input_dict, output_dict)
            except:
                gpt_response = None
            
            threads = []
            for idx in list(recc_ids.values):
                thread = threading.Thread(target=fetch_movie_info, args=(idx, display_info, gpt_response, output_dict.set_index('id')))
                thread.start()
                threads.append(thread)

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            after = time.time()
            print(after - before)
    
    else:
        display_info = []
    return render_template('index.html', recommendations=display_info)

if __name__ == "__main__":
    app.run(debug=True)
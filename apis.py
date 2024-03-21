import openai
import requests
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = "Your openai key"

def chatgpt(input, output):

  response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": """You're assisting a movie recommender system. Given a movie input from the user, the model will suggest 10 similar movies based on tags and additional insights. 
       The task is to provide explanations on why the recommended movies are similar to the input movie, leveraging tags, cast, crew,themes and interesting facts from the given data or your own data. 
      Tell if there are same people working on both movies.  'crew' in given data means directors of the movie.
      Avoid explicitly mentioning the input dictionaries; rather, use them to highlight similarities. Ensure a minimum of 4 lines of similarity for each recommended movie. 
       All recommendations should be filled, providing detailed similarities in the following JSON format: 
       {
        "recommended_movie_id(from the id column. return as STRINGS)" : "similarity of this movie and the inout movie",
       ...
       }.'"""},
      
      {"role": "user", "content": f"Input_dict - {input}. Output_dict = {output}"}
    ]
  )
  print(response.choices[0].message.content)
  return response.choices[0].message.content

key = os.getenv("TMDB_KEY")
        
def get_movie(idx):
  headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {key}"
    }
    
  url1 = f"https://api.themoviedb.org/3/movie/{idx}"
  # url2 = f"https://api.themoviedb.org/3/movie/{idx}/external_ids"
  # url3 = f"https://api.themoviedb.org/3/movie/{idx}/credits?language=en-US"

  response1 = requests.get(url1, headers=headers)
  response1.raise_for_status()
  movie_data = response1.json()
  return movie_data

    
        # try:
        #     response2 = requests.get(url2, headers=headers)
        #     response2.raise_for_status()
        #     external_ids = response2.json()
        # except requests.exceptions.RequestException as e:
        #     print(f"Error fetching external IDs from API: {e}")
        #     time.sleep(1)  # Wait for a moment before retrying

        # try:
        #     response3 = requests.get(url3, headers=headers)
        #     response3.raise_for_status()
        #     crew = extract_crew(response3.json()['crew'])
        # except requests.exceptions.RequestException as e:
        #     print(f"Error fetching crew data from API: {e}")
        #     time.sleep(1)  # Wait for a moment before retrying

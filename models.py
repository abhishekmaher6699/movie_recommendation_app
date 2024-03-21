import os
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
from utils import treat_title, prepare_tags, extract_data_from_db
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, lil_matrix
from sklearn.decomposition import TruncatedSVD

path = "data\processed_data.pkl"

if os.path.exists(path):
  print('opening file')
  with open(path, 'rb') as f:
    processed_data = pickle.load(f)
    df, indices, tags, genre_indices, dir_indices, keywords_indices, feature_names = processed_data
else:
  print('processing data')
  df = extract_data_from_db(['id', 'adult', 'release_year', 'display_title', 'title','overview','poster_path', 'rating', 'genres', 'keywords','cast', 'crew'])
  
  indices = pd.Series(df.index, index=df.title).drop_duplicates()

  tags, genre_indices, dir_indices, keywords_indices, feature_names, df = prepare_tags(df)

  cached_data = df, indices, tags, genre_indices, dir_indices, keywords_indices, feature_names
  
  with open(path, 'wb') as f: 
    pickle.dump(cached_data, f)
    

# Get Recommendations based on a input movie
def get_recommendations(input):

  title = treat_title(input)
  try:
    idx = indices[title]
  except:
    return None
  similarity_matrix = cosine_similarity(tags[idx], tags)
  sim_scores = list(enumerate(similarity_matrix[0]))
  sorted_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
  reccs = sorted_scores[1:11]
  recc_indices = [i[0] for i in reccs]

  return df['display_title'].iloc[recc_indices], df['id'].iloc[recc_indices], df['id'].iloc[idx]

# Get recommendation based on user's 5 fav movies
def get_user_profile(liked_movies, weights, features):

  liked_movies_indices = list(indices[liked_movies].values)
  movies = features[liked_movies_indices]
  n_components = 1
  svd = TruncatedSVD(n_components=n_components)
  user_profile = svd.fit_transform(movies.toarray().T * weights).T

  return user_profile

def user_preferred_movies(input_list, weights):

  liked_movies = treat_title(input_list)

  features = tags.copy()
  liked_movies_indices = list(indices[liked_movies].values)
  user_profile = get_user_profile(liked_movies, weights, features)
  user_profile_similarity = cosine_similarity(user_profile.reshape(1,-1), features)

  sim_scores = list(enumerate(user_profile_similarity[0]))
  sorted_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
  scores = [item for item in sorted_scores if item[0] not in liked_movies_indices][0:20]
  recc_indices = [i[0] for i in scores]

  return df['display_title'].iloc[recc_indices]

# Recommend movies based on favourite movies and also an input movie
def get_updated_feature(features, title, user_profile, liked_movies, feature_names = feature_names):

  non_genre_keyword_mask = np.ones_like(features[indices[title]].toarray(), dtype=bool)
  non_genre_keyword_mask[:, keywords_indices] = False

  _average = np.average(np.vstack((features[indices[title]][:, genre_indices + keywords_indices], user_profile[:, genre_indices + keywords_indices])), axis=0)
  features[indices[title], genre_indices + keywords_indices] =_average[0]

  liked_movies_indices = list(indices[liked_movies].values)

  keywords = sorted(list(df.iloc[liked_movies_indices]['keywords'].explode()))
  word_counts = Counter(keywords)
  words_to_weigh = [(word, count) for word, count in word_counts.items() if count > 1]
  for i in words_to_weigh:
      features[indices[title], feature_names.index(i[0])] += i[1]/1.5
      features[:,feature_names.index(i[0])] *= i[1]/1.5

  genres = sorted(list(df.iloc[liked_movies_indices]['genres'].explode()))
  word_counts = Counter(genres)
  words_to_weigh = [(word, count) for word, count in word_counts.items() if count > 1]
  for i in words_to_weigh:
      #  features[indices[title], feature_names.index(i[0])] += i[1]/1.5
       features[:,feature_names.index(i[0])] *= i[1]/1.5

  return features

def recommend_preferred_movies(input_title, input_liked_movies, weights):

  title = treat_title(input_title)
  liked_movies = treat_title(input_liked_movies)
  features = tags.copy().tolil()

  features[indices[title]] *= 20
  user_profile = lil_matrix(get_user_profile(liked_movies, weights, features))
  features = get_updated_feature(features, title, user_profile, liked_movies)

  liked_movies_indices = list(indices[liked_movies].values)
  idx = indices[title]
  similarity_matrix = cosine_similarity(features[idx], features)

  sim_scores = list(enumerate(similarity_matrix[0]))

  sorted_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
  scores = [item for item in sorted_scores if item[0] not in liked_movies_indices][1:11]
  recc_indices = [i[0] for i in scores]

  return df['display_title'].iloc[recc_indices]

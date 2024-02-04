from fastapi import FastAPI

import pickle
import pandas as pd
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import requests

movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
cv = CountVectorizer(max_features=5000, stop_words='english')

vectors = cv.fit_transform(movies['tags']).toarray()

similarity = cosine_similarity(vectors)
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
]

app = FastAPI(middleware=middleware)


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)),
                         reverse=True, key=lambda x: x[1])[1:6]
    recommend_movies = []
    for i in movies_list:
        recommend_movies.append(moviedetails(movies.iloc[i[0]].movie_id))
    return recommend_movies


def moviedetails(movieid):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=3b0ea003564064bbb54301ede5b1c63d&language=en-US'.format(movieid))
    data = response.json()
    return data


def genrebasedmovies(gl):
    id = []
    for i in gl:
        if i == "mystery":
            id.append(9648)
        elif i == "horror":
            id.append(27)
        elif i == "action":
            id.append(28)
        elif i == "comedy":
            id.append(35)
    genersmovies = []
    for i in id:
        response = requests.get(
            'https://api.themoviedb.org/3/discover/movie?api_key=3b0ea003564064bbb54301ede5b1c63d&with_genres={}'.format(i))
        data = response.json()
        # if (float(data["results"]["vote_average"]) > 6.0):
        genersmovies.append(data["results"])
    completemovieset = []
    for i in genersmovies:
        for j in i:
            # if (float(j["vote_average"]) > 6.0):
            completemovieset.append(j)
    return completemovieset


@app.get("/{title}")
def index(title: str):
    l = recommend(title)
    return json.dumps(l)


@app.get("/genres/{genresstring}")
def genres(genresstring: str):
    gl = genresstring.split(".")
    gmovies = genrebasedmovies(gl)
    return json.dumps(gmovies)

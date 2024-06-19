import streamlit as st
import pandas as pd
import pickle
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load movie data
movie_data = pd.read_csv('movie_data.csv')  # Adjust path as needed

# Load precomputed cosine similarity matrix
with open('cosine_sim_matrix (1).pkl', 'rb') as f:
    cosine_sim = pickle.load(f)

# Function to get movie recommendations
def recommend_movies(title, cosine_sim=cosine_sim):
    idx = movie_data[movie_data['title'] == title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]
    movie_indices = [i[0] for i in sim_scores]
    return movie_data.iloc[movie_indices]

# Function to fetch movie details from TMDB with retry logic
def fetch_movie_details(movie_id):
    api_key = '589ac2056bb72048a0b60bedd759ccd1'
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&append_to_response=credits"
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    try:
        response = http.get(url)
        response.raise_for_status()
        data = response.json()
        poster_path = data['poster_path']
        full_path = f"https://image.tmdb.org/t/p/w200{poster_path}"
        return full_path, data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching movie details: {e}")
        return None, None

# Set page configuration
st.set_page_config(page_title="CineMatch", layout="wide", page_icon="🎥")

# Center the title
st.markdown("<h1 style='text-align: center; font-size: 65px;'>Movie Recommender System🍿🎉</h1>", unsafe_allow_html=True)

movie_list = movie_data['title'].values
selected_movie = st.selectbox("Select a movie", movie_list)

if st.button('Search'):
    recommendations = recommend_movies(selected_movie)
    
    # Fetch basic info for the selected movie
    selected_movie_id = movie_data[movie_data['title'] == selected_movie].iloc[0].id
    poster_url, movie_info = fetch_movie_details(selected_movie_id)
    
    if movie_info:
        info_col, image_col = st.columns([2, 1])  # Adjust the ratio as needed
        
        with info_col:
            st.markdown(f"<h1 style='text-align: center'>{movie_info['title']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 18px;'><strong>Release Date:</strong> {movie_info['release_date']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 20px;'><strong>Overview:</strong> {movie_info['overview']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 18px;'><strong>Genres:</strong> {', '.join([genre['name'] for genre in movie_info['genres']])}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 18px;'><strong>Director:</strong> {', '.join([crew['name'] for crew in movie_info['credits']['crew'] if crew['job'] == 'Director'])}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 18px;'><strong>Cast:</strong> {', '.join([cast['name'] for cast in movie_info['credits']['cast'][:5]])}</p>", unsafe_allow_html=True)
        
        with image_col:
            if poster_url:
                st.image(poster_url, width=250)
    
    st.write("### Top 5 movie recommendations:")

    # Create columns for each recommendation
    cols = st.columns(5)  # Adjust the number of columns based on the number of recommendations

    for i, movie in enumerate(recommendations.itertuples(), 1):
        with cols[i - 1]:  # Place each poster in its respective column
            poster_url, _ = fetch_movie_details(movie.id)
            if poster_url:
                st.image(poster_url, width=200)
            st.write(f"{movie.title}")

from .models import SpotifyToken
from django.utils import timezone
from datetime import timedelta
from .credentials import CLIENT_ID,CLIENT_SECRET
from requests import post, put, get
from django.http import HttpResponse
from django.contrib.sessions.models import Session
import requests
import base64

BASE_URL = "https://api.spotify.com/v1/me/"

def get_user_tokens(session_id):
    print("spotify util get_user_tokens session_id", session_id)
    # user = SpotifyToken.objects.get(user=session_id)
    # print("user", user)
    user_tokens = SpotifyToken.objects.filter(user=session_id)
    #print("spotify User tokens:", user_tokens)
    if user_tokens.exists():
        print("exists")
        return user_tokens[0]
    else:
        print("does not exist")
        return None

def update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token):
    print("tokens before update/create", access_token, refresh_token,token_type,expires_in)
    tokens = get_user_tokens(session_id)
    print('spotify update_or_create_user_tokens session_id', session_id)
    expires_in = timezone.now() + timedelta(seconds=expires_in)
    if tokens:
        
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=
                    ['access_token','refresh_token','expires_in','token_type'])
        print("tokens after update/create",access_token,"\n", refresh_token,"\n",token_type,"\n",expires_in)
    else:
        tokens = SpotifyToken(user=session_id, access_token=access_token, refresh_token=refresh_token,token_type=token_type,expires_in=expires_in)
        tokens.save()

def is_spotify_authenticated(session_id):
     print('spotify util is_spotify_authenticated session_id', session_id)
     tokens = get_user_tokens(session_id)     
    #  print("Spotify util authenticated:", tokens.expires_in)
     print(timezone.now())
     if tokens:
         expiry = tokens.expires_in
         if expiry <= timezone.now():
             print("expired")
             refresh_spotify_token(session_id)
         return True
     return False

def refresh_spotify_token(session_id):
    print("spotify refresh tokens session_id", session_id)
    
    refresh_token = get_user_tokens(session_id).refresh_token
    print(refresh_token)

    token_url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode('utf-8')
    headers = {
        'Authorization': f'Basic {auth_header}',
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        # 'client_id': CLIENT_ID,
        # 'client_secret': CLIENT_SECRET
    }

    response = requests.post(token_url, headers = headers, data=data)
    
    if response.status_code == 200:
        response_data = response.json()
        
        # Extract the new tokens
        access_token = response_data.get('access_token')
        token_type = response_data.get('token_type')
        expires_in = response_data.get('expires_in')
        # refresh_token = response_data.get('refresh_token')
        
        print("Token details:", session_id, access_token, token_type, expires_in, refresh_token)
        
        # Update or create user tokens in your database
        update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token)
    else:
        # Handle the error response
        print("Error refreshing token. Status Code:", response.status_code)
        print("Error Response:", response.text)
    
def execute_spotify_api_request(session_id, endpoint):
    print("execute_spotify_api_request", session_id)
    tokens = get_user_tokens(session_id)
    print("tokens", tokens)
    print(tokens.access_token)
    
    headers = {"Authorization": f"Bearer {tokens.access_token}"}

    response = requests.get(BASE_URL + endpoint, headers=headers)

    if response.status_code == 200:
        return response.json()
        
    else:
        print(f"Error: {response.status_code}")

    # if post_:
    #     post(BASE_URL + endpoint, headers=headers)
    # if put_:
    #     put(BASE_URL + endpoint, headers=headers)

    # response = get(BASE_URL + endpoint, {}, headers=headers)

    # try:
    #     return response.json()
    # except:
    #     return {'Error': 'Issue with request'}

# def execute_spotify_api_request(session_id, endpoint, method='GET'):
#     BASE_URL = "https://api.spotify.com/v1/me/player/currently-playing"  # Replace with your Spotify API base URL
#     print("execute_spotify_api_request", session_id)
#     tokens = get_user_tokens(session_id)
#     print("access_tokens", tokens.access_token)
    
#     headers = {"Authorization": "Bearer BQBwuPUQCh7dkpLH3N1hVxq-PK0b1q1AxdfYKCEQZ37SLU6CFsdqUjHo2Rdl2IqZu5NdIfnlOyThMlPeip4Buf8RugGAXnKlz6IE-Mox_IQc1MaqGu0gBoa07aS-nofQ0eCG51gGvZVdN46nQIP4TWzjvuWxQjonFtUArA6-zSa0T6QjsBub89feDTknzEFeDyzrkjbO_cftNCU" }
    
#     try:
#         if method == 'GET':
#             response = requests.get(BASE_URL, headers=headers)
#         elif method == 'POST':
#             response = requests.post(BASE_URL, headers=headers)
#         elif method == 'PUT':
#             response = requests.put(BASE_URL, headers=headers)
#         else:
#             return {'Error': 'Invalid HTTP method'}

#         response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)

#         try:
#             response_data = response.json()
#             return response_data
#         except ValueError:
#             print("Invalid JSON response:")
#             print(response.text)  # Log the response content
#             return {'Error': 'Invalid JSON response'}
#     except requests.exceptions.RequestException as e:
#         return {'Error': f'Request error: {str(e)}'}


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
    user_tokens = SpotifyToken.objects.filter(user=session_id)
    if user_tokens.exists():
        print("exists")
        return user_tokens[0]
    else:
        print("does not exist")
        return None

def update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token):
    tokens = get_user_tokens(session_id)
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
    }

    response = requests.post(token_url, headers = headers, data=data)
    
    if response.status_code == 200:
        response_data = response.json()
        
        access_token = response_data.get('access_token')
        token_type = response_data.get('token_type')
        expires_in = response_data.get('expires_in')
        print("Token details:", session_id, access_token, token_type, expires_in, refresh_token)
        
        update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token)
    else:
        print("Error refreshing token. Status Code:", response.status_code)
        print("Error Response:", response.text)
    
def execute_spotify_api_request(session_id, endpoint, post_=False, put_=False):
    print("execute_spotify_api_request", session_id)
    tokens = get_user_tokens(session_id)
    print("tokens", tokens)
    print(tokens.access_token)
    
    headers = {"Authorization": f"Bearer {tokens.access_token}"}

    if post_:
        post(BASE_URL + endpoint, headers=headers)
        
    if put_:
        put(BASE_URL + endpoint, headers=headers)
    
    response = get(BASE_URL + endpoint, {}, headers=headers)

    if response.status_code == 200:
        return response.json()
        
    else:
        print(f"Error: {response.status_code}")

def play_song(session_id):
    return execute_spotify_api_request(session_id,'player/play', put_=True)

def pause_song(session_id):
    return execute_spotify_api_request(session_id,'player/pause', put_=True)

def skip_song(session_id):
    return execute_spotify_api_request(session_id, "player/next", post_=True)
from django.shortcuts import render, redirect
from .credentials import REDIRECT_URI,CLIENT_ID, CLIENT_SECRET
from rest_framework.views import APIView
from requests import Request, post
from rest_framework import status, generics
from rest_framework.response import Response
from .util import *
from api.models import Room    
import base64

class AuthURL(APIView):
    def get(self, request, format=None):
        scopes = 'user-read-playback-state user-modify-playback-state user-read-currently-playing'

        url = Request('GET', "https://accounts.spotify.com/authorize", params={
            'scope': scopes,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID
        }).prepare().url

        print("getAuth url", url)
        # Return the URL with a 200 OK response
        return Response({'url': url}, status=status.HTTP_200_OK)

def spotify_callback(request, format=None):
    code = request.GET.get('code')
    print("views code:", code)
    error = request.GET.get('error')
    print("error", error)

    auth_options = {
        'url': 'https://accounts.spotify.com/api/token',
        'data': {
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        },
        'headers': {
            'Authorization': 'Basic ' + base64.b64encode((CLIENT_ID + ':' + CLIENT_SECRET).encode()).decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }
    response = requests.post(auth_options['url'], data=auth_options['data'], headers=auth_options['headers'])

    if response.status_code == 200:
        response_data= response.json()
    # response = post('https://accounts.spotify.com/api/token', data={
    #     'grant_type': 'authorization_code',
    #     'code': code,
    #     'redirect_uri': REDIRECT_URI,
    #     'client_id': CLIENT_ID,
    #     'client_secret': CLIENT_SECRET,
    # }).json()
    
    print("token details", response_data.get('access_token'), response_data.get('token_type'),response_data.get('refresh_token'),response_data.get('expires_in'))
    access_token = response_data.get('access_token')
    token_type = response_data.get('token_type')
    refresh_token = response_data.get('refresh_token')
    expires_in = response_data.get('expires_in')
    error = response_data.get('error')

    if not request.session.exists(request.session.session_key):
        request.session.create()
         
    print(request.session.session_key)

    update_or_create_user_tokens(request.session.session_key, access_token, token_type, expires_in, refresh_token)

    # Redirect the user to your React frontend or another appropriate URL.
    return redirect('http://localhost:3000')

class IsAuthenticated(APIView):
    def get(self, request, format=None):
        print("spotify view IsAuthenticated self session_key", self.request.session.session_key)
        #is_authenticated = is_spotify_authenticated('ougk2pxeic31c58squffdusjsq9nift8')
        is_authenticated = is_spotify_authenticated(self.request.session.session_key)
        print("is spotify authenticated response", is_authenticated)
        return Response({'status': is_authenticated}, status=status.HTTP_200_OK)
    
class CurrentSong(APIView):
    def get(self, request, format = None):
        room_code = self.request.session.get('room_code')
        print("Current song room code", room_code)
        room = Room.objects.filter(code=room_code)
        if room.exists():
            print("room exists")
            room = room[0]
        else:
            print("Room does not exist")
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        host = room.host
        print('host:', host)
        endpoint = "player/currently-playing"
        response = execute_spotify_api_request(host, endpoint)
        
        if 'error' in response or 'item' not in response:
            return Response({},status=status.HTTP_204_NO_CONTENT)
        
        item  = response.get('item')
        duration = item.get('duration_ms')
        progress = response.get('progress_ms')
        album_cover = item.get('album').get('images')[0].get('url')
        is_playing = response.get('is_playing')
        song_id = item.get('id')

        artist_string = ""
        for i, artist in enumerate(item.get('artists')):
            if i>0:
                artist_string += ', '
            name = artist.get('name')
            artist_string += name

        song = {
            'title': item.get('name'),
            'artist': artist_string,
            'duration' : duration,
            'time' : progress,
            'image_url' : album_cover,
            'is_playing' : is_playing,
            'votes':0,
            'id': song_id
        }
        return Response(song, status=status.HTTP_200_OK)


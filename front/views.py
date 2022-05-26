import hashlib
import json
from django.utils import timezone
import spotipy
import csv
import os

from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings
from spotipy.oauth2 import SpotifyOAuth
from uuid import uuid4

from front.exceptions import ExportSizeLimitPassed
from front.models import AccessToken

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_sp_auth():
    return SpotifyOAuth(
        client_id = settings.SPOTIFY_CLIENT_ID,
        client_secret = settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri = settings.SPOTIFY_REDIRECT_URI,
        scope='user-library-read playlist-read-private playlist-read-collaborative user-read-private'
    )

def index(request):
    return render(request, 'front/index.html')

def authorize(request):
    sp_auth = get_sp_auth()

    return redirect(sp_auth.get_authorize_url())

def spotify_callback(request):
    sp_auth = get_sp_auth()

    rs_made = AccessToken.objects.filter(
        created__gte = timezone.now() - timezone.timedelta(hours=1),
        ip_address=get_client_ip(request)
    )

    if rs_made.count() >= 3:
        return render(request, 'front/error.html', {'title': 'Export failed!', 'error': 'You have already made 3 or more exports in the past hour!'})
        
    code = request.GET.get("code", "")
    try:
        token = sp_auth.get_access_token(code)
        sp = spotipy.Spotify(auth=token['access_token'])

        outfile_name = str(uuid4())
        outfile_path = settings.SPOTIFY_EXPORT_ROOT + outfile_name

        outfile = open(outfile_path, 'w')
        fwriter = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        headers = [
            'Playlist Name',
            'Song Name',
            'Album',
            'Artist'
        ]
        fwriter.writerow(headers)

        total = 50
        fetched = 0

        offset = 0
        
        while total > fetched:
            playlists = sp.current_user_playlists(offset=fetched)
            total = playlists['total']

            for playlist in playlists['items']:
                songs_total = 50
                songs_fetched = 0
                while songs_total > songs_fetched:
                    songs = sp.user_playlist_tracks(playlist_id=playlist['id'], offset=songs_fetched, limit=50)
                    songs_total = songs['total']

                    if len(songs['items']) == 0:
                        songs_fetched += 50
                        continue
                   
                    for song in songs['items']:
                        fwriter.writerow([
                            playlist['name'],
                            song['track']['name'],
                            song['track']['album']['name'],
                            ', '.join([i['name'] for i in song['track']['artists']])
                        ])

                        if os.path.getsize(outfile_path) > settings.SPOTIFY_EXPORT_SIZE_LIMIT:
                            raise ExportSizeLimitPassed()
                    

                    songs_fetched += 50



            fetched += 50
        total = 50
        fetched = 0
        while total > fetched:
            songs = sp.current_user_saved_tracks(limit=50, offset=fetched)
            total = songs['total']

            if len(songs['items']) == 0:
                songs_fetched += 50
                continue
        
            for song in songs['items']:
                fwriter.writerow([
                    'Liked Songs',
                    song['track']['name'],
                    song['track']['album']['name'],
                    ', '.join([i['name'] for i in song['track']['artists']])
                ])

                if os.path.getsize(outfile_path) > settings.SPOTIFY_EXPORT_SIZE_LIMIT:
                    raise ExportSizeLimitPassed()
            
            fetched += 50

        outfile.close()

        at_key = str(uuid4())
        at = AccessToken(
            key = hashlib.sha256(at_key.encode('UTF-8')).hexdigest(),
            file = outfile_path,
            ip_address = get_client_ip(request)
        )
        at.save()

        
        return render(request, 'front/success.html', {'key': at_key})
        
    except Exception as e:
        try:
            os.remove(outfile_name)
        except:
            pass
        raise e
        if type(e) == ExportSizeLimitPassed:
            return render(request, 'front/error.html', {'title': 'Error during export!', 'error': 'The export size limit was surpassed. You have too many playlists/songs!'})
        
        return render(request, 'front/error.html', {'title': 'Error during export!', 'error': 'Unexpected error occured during export!'})


def download_export(request, key):
    at = AccessToken.objects.filter(key=hashlib.sha256(key.encode('UTF-8')).hexdigest())

    if at.count() == 0:
        return render(request, 'front/error.html', {'title': 'Export was not found!', 'error': 'This export was not found in our database!'})
    
    at = at[0]

    if at.expired:
        return render(request, 'front/error.html', {'title': 'Export has expired!', 'error': 'This export has already expired!'})
    try:
        return FileResponse(open(at.file, 'rb'), as_attachment=True, filename=at.download_name)
    except:
        return render(request, 'front/error.html', {'title': 'Download failed!', 'error': 'Export download failed unexpectedly!'})

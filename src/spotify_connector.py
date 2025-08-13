import os, base64
from time import time

import requests

from . import logger


class SpotifyConnector:
    def __init__(self, client_id: str=None, client_secret: str=None):
        self._client_id = client_id
        self._client_secret = client_secret
        self.token_url = 'https://accounts.spotify.com/api/token'
        self.base_url = 'https://api.spotify.com/v1/'
        self.access_token = None
        self.token_expiry = None

        # Authenticate on creation
        self.authenticate()

    @property
    def client_id(self):
        if self._client_id is None:
            self._client_id = os.getenv('SPOTIFY_CLIENT_ID')
            if not self._client_id:
                raise ValueError("SPOTIFY_CLIENT_ID environment variable not set.")
        return self._client_id

    @property
    def client_secret(self):
        if self._client_secret is None:
            self._client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            if not self._client_id:
                raise ValueError("SPOTIFY_CLIENT_SECRET environment variable not set.")
        return self._client_secret

    def authenticate(self):
        """
        Authenticate and obtain an access token using the Client Credentials Flow.
        """
        auth_header = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': f'Basic {auth_header}'
        }
        data = {
            'grant_type': 'client_credentials',
        }

        response = requests.post(self.token_url, headers=headers, data=data)
        token_info = response.json()
        
        if response.status_code == 200:
            self.access_token = token_info['access_token']
            expires_in = token_info['expires_in']
            self.token_expiry = time() + expires_in
        else:
            raise Exception('Failed to authenticate with Spotify API')

    def is_token_expired(self):
        """
        Check if the current access token is expired.
        """
        return time() > self.token_expiry

    def refresh_token(self):
        """
        Refresh the access token if it's expired.
        """
        if self.is_token_expired():
            logger.info("Token expired, refreshing...")
            self.authenticate()

    def make_request(self, endpoint: str):
        """
        Make a GET request to a specified endpoint in the Spotify API.
        """
        self.refresh_token()
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        logger.debug(f"Making request to endpoint: {self.base_url + endpoint}")
        response = requests.get(self.base_url + endpoint, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching data from Spotify API: {response.status_code}, {response.text}")
            raise Exception(f"Error fetching data from Spotify API: {response.status_code}, {response.text}")

    def get_playlists(self, category_id: str = None):
        """
        Fetch a list of playlist IDs. If category_id is provided, fetch playlists from that category.
        If category_id is None, fetch all public playlists (no category filter).
        """
        if category_id:
            # Fetch playlists for a specific category
            endpoint = f'browse/categories/{category_id}/playlists'
        else:
            # Fetch all public playlists without any category filter
            endpoint = 'browse/featured-playlists'  # This retrieves a broader list of playlists
        
        logger.debug(f"Fetching playlists with endpoint: {endpoint}")
        data = self.make_request(endpoint)
        
        # Extract playlist IDs from the response
        playlists = data.get('playlists', {}).get('items', [])
        playlist_ids = [playlist['id'] for playlist in playlists]
        
        logger.info(f"Fetched {len(playlist_ids)} playlists.")
        return playlist_ids

    def get_user_playlists(self):
        """
        Fetch a list of the user's own playlists.
        """
        endpoint = 'me/playlists'
        logger.debug(f"Fetching user's playlists with endpoint: {endpoint}")
        data = self.make_request(endpoint)

        # Extract playlist details from the response
        playlists = data.get('items', [])
        user_playlists = [
            {
                'id': playlist['id'],
                'name': playlist['name'],
                'tracks_count': playlist['tracks']['total']
            }
            for playlist in playlists
        ]

        logger.info(f"Fetched {len(user_playlists)} user playlists.")
        return user_playlists

    def get_playlist_tracks(self, playlist_id: str):
        """
        Fetch tracks from a specific playlist.

        Args:
            playlist_id (str): The ID of the playlist.

        Returns:
            list: A list of tracks with details including name, artist, and track ID.
        """
        endpoint = f'playlists/{playlist_id}/tracks'
        logger.debug(f"Fetching tracks from playlist with endpoint: {endpoint}")
        data = self.make_request(endpoint)

        # Extract track details from the response
        tracks = data.get('items', [])
        track_details = [
            {
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name'],
                'id': track['track']['id']
            }
            for track in tracks
        ]

        logger.info(f"Fetched {len(track_details)} tracks from playlist {playlist_id}.")
        return track_details

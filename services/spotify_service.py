from __future__ import annotations

import os
from typing import List, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from core.models import Playlist, Track, TrackRef
from services.base import MusicService


class SpotifyService(MusicService):
    def __init__(self) -> None:
        self._client: Optional[spotipy.Spotify] = None

    @property
    def name(self) -> str:
        return "spotify"

    def ensure_authenticated(self) -> None:
        if self._client is not None:
            return

        # Scopes for reading playlists (and later adding if you want Deezer -> Spotify)
        scope = "playlist-read-private playlist-read-collaborative"

        self._client = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                open_browser=True,
                cache_path=".spotify_token_cache",  # stored locally in repo
            )
        )

        # Sanity call (forces auth)
        self._client.current_user()

    def get_playlist(self, playlist_id: str) -> Playlist:
        assert self._client is not None

        data = self._client.playlist(playlist_id, fields="id,name,description")
        return Playlist(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
        )

    def list_playlist_tracks(self, playlist_id: str) -> List[TrackRef]:
        assert self._client is not None

        out: List[TrackRef] = []
        offset = 0
        limit = 100

        while True:
            page = self._client.playlist_items(
                playlist_id,
                offset=offset,
                limit=limit,
                fields="items(track(id,name,artists(name),album(name),duration_ms,external_ids(isrc),explicit)),next",
            )

            for item in page["items"]:
                t = item.get("track") or {}
                if not t or t.get("id") is None:
                    # Local files or unavailable tracks show up like this
                    continue

                artists = t.get("artists") or []
                artist_name = artists[0]["name"] if artists else ""

                external_ids = t.get("external_ids") or {}
                isrc = external_ids.get("isrc")

                track = Track(
                    title=t.get("name") or "",
                    artist=artist_name,
                    album=(t.get("album") or {}).get("name"),
                    isrc=isrc,
                    duration_ms=t.get("duration_ms"),
                    explicit=t.get("explicit"),
                )

                out.append(TrackRef(id=t["id"], track=track))

            if page.get("next") is None:
                break

            offset += limit

        return out

    # These are not needed for Spotify -> Deezer export (for now)
    def create_playlist(self, name: str, description: Optional[str] = None) -> Playlist:
        raise NotImplementedError

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        raise NotImplementedError

    def search_tracks(self, query: str, limit: int = 10) -> List[TrackRef]:
        raise NotImplementedError
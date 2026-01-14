from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from core.models import Playlist, Track, TrackRef


class MusicService(ABC):
    """
    A service adapter must implement these methods.

    This design keeps your transfer engine service-agnostic:
    Spotify <-> Deezer (or Apple, YouTube, etc.) can be swapped in.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        # Example: "spotify" or "deezer"
        raise NotImplementedError

    @abstractmethod
    def ensure_authenticated(self) -> None:
        """
        Perform whatever is needed so calls can be made.
        - For Spotify (spotipy): ensure token is available
        - For Deezer (requests): ensure access_token exists
        """
        raise NotImplementedError

    # ---- Playlists ----

    @abstractmethod
    def get_playlist(self, playlist_id: str) -> Playlist:
        raise NotImplementedError

    @abstractmethod
    def list_playlist_tracks(self, playlist_id: str) -> List[TrackRef]:
        """
        Returns TrackRefs with:
        - source service track id
        - normalized Track payload
        """
        raise NotImplementedError

    @abstractmethod
    def create_playlist(self, name: str, description: Optional[str] = None) -> Playlist:
        raise NotImplementedError

    @abstractmethod
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        raise NotImplementedError

    # ---- Searching / Matching ----

    @abstractmethod
    def search_tracks(self, query: str, limit: int = 10) -> List[TrackRef]:
        """
        Service-specific search. You pass a query string.
        Returns candidates as TrackRefs.
        """
        raise NotImplementedError

    def build_search_query(self, track: Track) -> str:
        """
        Default query builder that works decently across services.
        Services can override if they have better options.
        """
        # Keep it simple; add album if it helps
        if track.album:
            return f"{track.artist} {track.title} {track.album}"
        return f"{track.artist} {track.title}"
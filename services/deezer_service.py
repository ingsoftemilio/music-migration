from __future__ import annotations

import os
from typing import List, Optional
from urllib.parse import quote_plus

import requests

from core.exceptions import AuthError, ServiceError
from core.models import Playlist, Track, TrackRef
from services.base import MusicService


class DeezerService(MusicService):
    def __init__(self) -> None:
        self._access_token: Optional[str] = None
        self._user_id: Optional[int] = None
        self._base_url = "https://api.deezer.com"

    @property
    def name(self) -> str:
        return "deezer"

    def ensure_authenticated(self) -> None:
        if self._access_token is not None and self._user_id is not None:
            return

        token = os.getenv("DEEZER_ACCESS_TOKEN")
        if not token:
            raise AuthError("Missing DEEZER_ACCESS_TOKEN in .env")

        self._access_token = token

        # Verify token + fetch user id
        me = self._get("/user/me")
        self._user_id = int(me["id"])

    def get_playlist(self, playlist_id: str) -> Playlist:
        data = self._get(f"/playlist/{playlist_id}")
        return Playlist(
            id=str(data["id"]),
            name=data["title"],
            description=data.get("description"),
        )

    def list_playlist_tracks(self, playlist_id: str) -> List[TrackRef]:
        # Not needed for Spotify -> Deezer export (for now), but we’ll implement basic version anyway
        data = self._get(f"/playlist/{playlist_id}/tracks")
        out: List[TrackRef] = []

        for t in data.get("data", []):
            artist = (t.get("artist") or {}).get("name") or ""
            album = (t.get("album") or {}).get("title")

            track = Track(
                title=t.get("title") or "",
                artist=artist,
                album=album,
                duration_ms=(t.get("duration") or 0) * 1000 if t.get("duration") is not None else None,
                # Deezer sometimes exposes isrc in "isrc" depending on endpoints; often not present
                isrc=t.get("isrc"),
                explicit=bool(t.get("explicit_lyrics")) if t.get("explicit_lyrics") is not None else None,
            )
            out.append(TrackRef(id=str(t["id"]), track=track))

        return out

    def create_playlist(self, name: str, description: Optional[str] = None) -> Playlist:
        assert self._user_id is not None
        # Deezer create playlist uses query params
        r = requests.post(
            f"{self._base_url}/user/{self._user_id}/playlists",
            params={"title": name, "access_token": self._access_token},
            timeout=30,
        )
        data = self._ensure_json(r)

        # Deezer returns {"id": ...} on success
        playlist_id = str(data["id"])
        return Playlist(id=playlist_id, name=name, description=description)

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        # Deezer supports adding multiple track ids via "songs" comma-separated
        if not track_ids:
            return

        # Chunk to avoid URL/query size issues
        chunk_size = 50
        for i in range(0, len(track_ids), chunk_size):
            chunk = track_ids[i : i + chunk_size]
            songs = ",".join(chunk)

            r = requests.post(
                f"{self._base_url}/playlist/{playlist_id}/tracks",
                params={"songs": songs, "access_token": self._access_token},
                timeout=30,
            )
            data = self._ensure_json(r)

            # Deezer returns boolean-ish success (True/False) sometimes
            if data is False:
                raise ServiceError("Deezer failed to add tracks to playlist")

    def search_tracks(self, query: str, limit: int = 10) -> List[TrackRef]:
        q = query.strip()
        if not q:
            return []

        data = self._get("/search", params={"q": q})
        out: List[TrackRef] = []

        for t in (data.get("data") or [])[:limit]:
            artist = (t.get("artist") or {}).get("name") or ""
            album = (t.get("album") or {}).get("title")

            track = Track(
                title=t.get("title") or "",
                artist=artist,
                album=album,
                duration_ms=(t.get("duration") or 0) * 1000 if t.get("duration") is not None else None,
                isrc=t.get("isrc"),
                explicit=bool(t.get("explicit_lyrics")) if t.get("explicit_lyrics") is not None else None,
            )
            out.append(TrackRef(id=str(t["id"]), track=track))

        return out

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        r = requests.get(
            f"{self._base_url}{path}",
            params={**(params or {}), "access_token": self._access_token},
            timeout=30,
        )
        return self._ensure_json(r)

    def _ensure_json(self, r: requests.Response) -> dict:
        try:
            data = r.json()
        except Exception as e:
            raise ServiceError(f"Deezer returned non-JSON: HTTP {r.status_code}") from e

        # Deezer uses {"error": {...}} style
        if isinstance(data, dict) and "error" in data:
            msg = (data["error"] or {}).get("message", "Unknown Deezer error")
            raise ServiceError(f"Deezer API error: {msg}")

        return data
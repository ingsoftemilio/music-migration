from __future__ import annotations

from typing import Callable, Optional

from core.models import TransferResult, TransferItemResult, TrackRef
from services.base import MusicService


class TransferEngine:
    def __init__(
        self,
        source: MusicService,
        dest: MusicService,
        pick_best_match: Callable[[TrackRef, list[TrackRef]], tuple[Optional[TrackRef], list[TrackRef], Optional[str]]],
    ) -> None:
        self._source = source
        self._dest = dest
        self._pick_best_match = pick_best_match

    def transfer_playlist(self, source_playlist_id: str, new_playlist_name: Optional[str] = None) -> TransferResult:
        # Make sure both sides can call APIs
        self._source.ensure_authenticated()
        self._dest.ensure_authenticated()

        # Load playlist metadata
        src_playlist = self._source.get_playlist(source_playlist_id)

        # Decide destination name
        dest_name = new_playlist_name if new_playlist_name else f"{src_playlist.name} (migrated)"

        # Create destination playlist
        dest_playlist = self._dest.create_playlist(dest_name, description=src_playlist.description)

        # Pull tracks from source
        src_tracks = self._source.list_playlist_tracks(src_playlist.id)

        # For results
        result = TransferResult(source_playlist=src_playlist, dest_playlist=dest_playlist)

        # Add in small batches (we'll implement batch sizes per service later if needed)
        dest_track_ids_to_add: list[str] = []

        for src_ref in src_tracks:
            # Build a query from normalized track info
            query = self._dest.build_search_query(src_ref.track)

            # Search destination candidates
            candidates = self._dest.search_tracks(query=query, limit=10)

            # Decide best match (or none)
            matched, kept_candidates, reason = self._pick_best_match(src_ref, candidates)

            item = TransferItemResult(source=src_ref, matched=matched, candidates=kept_candidates, reason=reason)
            result.items.append(item)

            if matched is not None:
                dest_track_ids_to_add.append(matched.id)

        # Actually add tracks (single call for now; later we can chunk)
        if dest_track_ids_to_add:
            self._dest.add_tracks_to_playlist(dest_playlist.id, dest_track_ids_to_add)

        return result
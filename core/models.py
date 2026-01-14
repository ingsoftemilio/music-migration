from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass(frozen=True) # fronzen so once created, cannot be changed
class Track:
    # Human-friendly title
    title: str
    # Main artist name
    artist: str
    # Optional album name
    album: Optional[str] = None
    # Optional International Standard Recording Code (best identifier)
    isrc: Optional[str] = None
    # Optional duration for tie-breaking matches
    duration_ms: Optional[int] = None
    # Optional explicit flag (sometimes useful to avoid clean/explicit mismatches)
    explicit: Optional[bool] = None


@dataclass(frozen=True)
class TrackRef:
    # The service-specific ID (Spotify track id, Deezer track id, etc.)
    id: str
    # A normalized Track payload you can use for matching/searching on the other service
    track: Track


@dataclass(frozen=True)
class Playlist:
    # Service-specific playlist id
    id: str
    # Display name
    name: str
    # Optional description
    description: Optional[str] = None


@dataclass
class TransferItemResult:
    # Original track from source service
    source: TrackRef
    # Selected match on destination service (if any)
    matched: Optional[TrackRef] = None
    # If no match, store a reason
    reason: Optional[str] = None
    # If ambiguous, store candidates (optional)
    candidates: List[TrackRef] = field(default_factory=list)


@dataclass
class TransferResult:
    # Source playlist
    source_playlist: Playlist
    # Destination playlist
    dest_playlist: Playlist
    # Per-track outcomes
    items: List[TransferItemResult] = field(default_factory=list)

    def summary(self) -> Dict[str, int]:
        matched = 0
        missing = 0
        ambiguous = 0

        for item in self.items:
            if item.matched is not None:
                matched += 1
                continue
            if item.candidates:
                ambiguous += 1
                continue
            missing += 1

        return {"matched": matched, "missing": missing, "ambiguous": ambiguous, "total": len(self.items)}
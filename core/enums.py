# core/enums.py
from enum import Enum


class ServiceName(str, Enum):
    spotify = "spotify"
    deezer = "deezer"
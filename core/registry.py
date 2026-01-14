from __future__ import annotations

from typing import Dict

from core.enums import ServiceName
from services.base import MusicService


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: Dict[ServiceName, MusicService] = {}

    def register(self, service: MusicService) -> None:
        self._services[ServiceName(service.name)] = service

    def get(self, name: ServiceName) -> MusicService:
        return self._services[name]
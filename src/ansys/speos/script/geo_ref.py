from __future__ import annotations

from typing import Mapping, Optional


class GeoRef:
    """Represent a CAD object"""

    def __init__(self, name: str, description: Optional[str], metadata: Mapping[str, str]):
        self.name = name
        self.description = description
        self.metadata = metadata
        return

    @staticmethod
    def from_native_link(geopath: str) -> GeoRef:
        return GeoRef("", "", {"GeoPath": geopath})

    def to_native_link(self) -> str:
        return self.metadata["GeoPath"]

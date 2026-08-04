from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Coordinates


class RouteCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS geocodes (
                normalized_address TEXT PRIMARY KEY,
                original_address TEXT NOT NULL,
                longitude REAL NOT NULL,
                latitude REAL NOT NULL
            )
            """
        )
        self.connection.commit()

    @staticmethod
    def normalize(address: str) -> str:
        return " ".join(address.strip().casefold().split())

    def get(self, address: str) -> Coordinates | None:
        key = self.normalize(address)
        row = self.connection.execute(
            "SELECT longitude, latitude FROM geocodes WHERE normalized_address = ?",
            (key,),
        ).fetchone()
        if not row:
            return None
        return Coordinates(longitude=float(row[0]), latitude=float(row[1]))

    def put(self, address: str, coordinates: Coordinates) -> None:
        key = self.normalize(address)
        self.connection.execute(
            """
            INSERT INTO geocodes(normalized_address, original_address, longitude, latitude)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(normalized_address) DO UPDATE SET
                original_address = excluded.original_address,
                longitude = excluded.longitude,
                latitude = excluded.latitude
            """,
            (key, address, coordinates.longitude, coordinates.latitude),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

"""Read-only inventory contract for the isolated CyberPanel control plane.

No network access, credentials, shell commands or CyberPanel imports.
The fixture is synthetic and must never be presented as server state.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol, Literal

InventoryKind = Literal["sites", "ssl", "backups"]


@dataclass(frozen=True)
class InventoryItem:
    id: str
    label: str
    state: str


@dataclass(frozen=True)
class InventorySnapshot:
    kind: InventoryKind
    source: Literal["synthetic", "not_connected"]
    production_connected: bool
    items: tuple[InventoryItem, ...]

    def as_json(self) -> dict:
        return {
            "kind": self.kind,
            "source": self.source,
            "production_connected": self.production_connected,
            "items": [asdict(item) for item in self.items],
        }


class ReadOnlyInventoryAdapter(Protocol):
    def inventory(self, kind: InventoryKind) -> InventorySnapshot:
        """Return inventory only; must not mutate upstream state."""


class DisconnectedAdapter:
    """Safe default: no fabricated server assets."""

    def inventory(self, kind: InventoryKind) -> InventorySnapshot:
        if kind not in ("sites", "ssl", "backups"):
            raise ValueError("unsupported inventory kind")
        return InventorySnapshot(kind, "not_connected", False, ())


class SyntheticAdapter:
    """Explicit test-only fixture. Never attach to real CyberPanel credentials."""

    def inventory(self, kind: InventoryKind) -> InventorySnapshot:
        if kind not in ("sites", "ssl", "backups"):
            raise ValueError("unsupported inventory kind")
        fixtures = {
            "sites": (InventoryItem("example-site", "example.invalid", "fixture"),),
            "ssl": (InventoryItem("example-cert", "example.invalid", "fixture"),),
            "backups": (InventoryItem("example-backup", "sample-only", "fixture"),),
        }
        return InventorySnapshot(kind, "synthetic", False, fixtures[kind])

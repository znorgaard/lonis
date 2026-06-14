"""MtgCard dataclass representing a single unique Magic: The Gathering card."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MtgCard:
    """A single unique Magic: The Gathering card, aggregated across all of its faces."""

    name: str
    layout: str
    types: frozenset[str]
    subtypes: frozenset[str]
    supertypes: frozenset[str]
    legalities: dict[str, str]
    is_funny: bool

    @classmethod
    def from_atomic_entry(cls, name: str, faces: list[dict[str, Any]]) -> MtgCard | None:
        """
        Build an MtgCard from an AtomicCards entry.

        Args:
            name: The card name (the key in the AtomicCards dict).
            faces: List of face objects for this card name. Single-face cards have one element.

        Returns:
            An MtgCard, or None if the card is a token.
        """
        first = faces[0]
        layout: str = first.get("layout", "")
        if layout == "token":
            return None
        types: frozenset[str] = frozenset()
        subtypes: frozenset[str] = frozenset()
        supertypes: frozenset[str] = frozenset()
        for face in faces:
            types = types | frozenset(face.get("types", []))
            subtypes = subtypes | frozenset(face.get("subtypes", []))
            supertypes = supertypes | frozenset(face.get("supertypes", []))
        return cls(
            name=name,
            layout=layout,
            types=types,
            subtypes=subtypes,
            supertypes=supertypes,
            legalities=dict(first.get("legalities", {})),
            is_funny=bool(first.get("isFunny", False)),
        )

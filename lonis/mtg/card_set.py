"""MtgCardSet — an immutable collection of MtgCard with filter and aggregation methods."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from typing import Any

from lonis.mtg.card import MtgCard

_LEGAL = "Legal"


class MtgCardSet:
    """An immutable collection of unique Magic: The Gathering cards."""

    def __init__(self, cards: tuple[MtgCard, ...]) -> None:
        """
        Create an MtgCardSet from a tuple of cards.

        Args:
            cards: The cards in this set.
        """
        self._cards = cards

    def __iter__(self) -> Iterator[MtgCard]:
        """Iterate over the cards in this set."""
        return iter(self._cards)

    @classmethod
    def from_atomic_data(cls, data: dict[str, list[dict[str, Any]]]) -> MtgCardSet:
        """
        Build an MtgCardSet from a parsed AtomicCards dict.

        Args:
            data: The value of the "data" key in AtomicCards JSON — card name to list of faces.

        Returns:
            An MtgCardSet containing all non-token cards.
        """
        cards = []
        for name, faces in data.items():
            card = MtgCard.from_atomic_entry(name, faces)
            if card is not None:
                cards.append(card)
        return cls(tuple(cards))

    def filter_format(self, fmt: str) -> MtgCardSet:
        """
        Return a new MtgCardSet containing only cards legal in the given format.

        Args:
            fmt: Format name, e.g. "commander", "modern", "standard".

        Returns:
            A filtered MtgCardSet.

        Raises:
            ValueError: If fmt is not a recognized format name.
        """
        if self._cards:
            # Keys from the first card work here because mtgjson emits a consistent
            # legalities object across all cards.
            valid_formats = set(self._cards[0].legalities.keys())
            if fmt not in valid_formats:
                raise ValueError(f"Unknown format {fmt!r}. Valid formats: {sorted(valid_formats)}")
        return MtgCardSet(tuple(c for c in self._cards if c.legalities.get(fmt) == _LEGAL))

    def filter_creatures(self) -> MtgCardSet:
        """
        Return a new MtgCardSet containing only cards with the Creature type.

        Returns:
            A filtered MtgCardSet.
        """
        return MtgCardSet(tuple(c for c in self._cards if "Creature" in c.types))

    def creature_type_counts(self) -> dict[str, int]:
        """
        Count how many cards of each creature subtype are in this set.

        Returns:
            A dict mapping creature subtype to number of cards with that subtype.
            Only cards with the Creature type contribute to the count.
        """
        counter: Counter[str] = Counter()
        for card in self._cards:
            if "Creature" not in card.types:
                continue
            for subtype in card.subtypes:
                counter[subtype] += 1
        return dict(counter)

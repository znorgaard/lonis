"""Tests for MtgCard."""

from lonis.mtg.card import MtgCard


def _face(
    *,
    layout: str = "normal",
    types: list[str] | None = None,
    subtypes: list[str] | None = None,
    supertypes: list[str] | None = None,
    legalities: dict[str, str] | None = None,
    is_funny: bool = False,
) -> dict[str, object]:
    return {
        "layout": layout,
        "types": types or [],
        "subtypes": subtypes or [],
        "supertypes": supertypes or [],
        "legalities": legalities or {},
        "isFunny": is_funny,
    }


def test_from_atomic_entry_single_face() -> None:
    faces = [
        _face(
            types=["Creature"],
            subtypes=["Human", "Warrior"],
            supertypes=["Legendary"],
            legalities={"commander": "Legal", "modern": "Legal"},
        )
    ]
    card = MtgCard.from_atomic_entry("Adanto Vanguard", faces)
    assert card is not None
    assert card.name == "Adanto Vanguard"
    assert card.layout == "normal"
    assert card.types == frozenset({"Creature"})
    assert card.subtypes == frozenset({"Human", "Warrior"})
    assert card.supertypes == frozenset({"Legendary"})
    assert card.legalities == {"commander": "Legal", "modern": "Legal"}
    assert card.is_funny is False


def test_from_atomic_entry_multi_face_aggregates_types() -> None:
    faces = [
        _face(
            layout="transform",
            types=["Creature"],
            subtypes=["Human", "Warrior"],
            supertypes=[],
            legalities={"commander": "Legal"},
        ),
        _face(
            layout="transform",
            types=["Creature"],
            subtypes=["Werewolf"],
            supertypes=[],
            legalities={"commander": "Legal"},
        ),
    ]
    card = MtgCard.from_atomic_entry("Huntmaster of the Fells // Ravager of the Fells", faces)
    assert card is not None
    assert card.subtypes == frozenset({"Human", "Warrior", "Werewolf"})
    assert card.types == frozenset({"Creature"})
    assert card.layout == "transform"


def test_from_atomic_entry_token_returns_none() -> None:
    faces = [
        _face(
            layout="token",
            types=["Creature"],
            subtypes=["Soldier"],
            legalities={"commander": "Not Legal"},
        )
    ]
    assert MtgCard.from_atomic_entry("Soldier Token", faces) is None


def test_from_atomic_entry_is_funny_flag() -> None:
    faces = [
        _face(
            types=["Creature"],
            subtypes=["Chicken"],
            is_funny=True,
            legalities={"commander": "Not Legal"},
        )
    ]
    card = MtgCard.from_atomic_entry("Chicken (Unhinged)", faces)
    assert card is not None
    assert card.is_funny is True

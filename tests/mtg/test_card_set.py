"""Tests for MtgCardSet."""

from typing import Any

import pytest

from lonis.mtg.card import MtgCard
from lonis.mtg.card_set import MtgCardSet


def _make_card(
    name: str,
    *,
    types: list[str] | None = None,
    subtypes: list[str] | None = None,
    color_identity: list[str] | None = None,
    colors: list[str] | None = None,
    converted_mana_cost: float = 0.0,
    legalities: dict[str, str] | None = None,
) -> MtgCard:
    return MtgCard(
        name=name,
        layout="normal",
        types=frozenset(types or []),
        subtypes=frozenset(subtypes or []),
        supertypes=frozenset(),
        color_identity=frozenset(color_identity or []),
        colors=frozenset(colors or []),
        converted_mana_cost=converted_mana_cost,
        legalities=legalities or {},
        is_funny=False,
    )


def test_from_atomic_data_excludes_tokens() -> None:
    data: dict[str, list[dict[str, Any]]] = {
        "Elvish Mystic": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
        "Soldier Token": [
            {
                "layout": "token",
                "types": ["Creature"],
                "subtypes": ["Soldier"],
                "supertypes": [],
                "legalities": {},
                "isFunny": False,
            }
        ],
    }
    card_set = MtgCardSet.from_atomic_data(data)
    names = {c.name for c in card_set}
    assert "Elvish Mystic" in names
    assert "Soldier Token" not in names


def test_filter_format_keeps_legal_cards() -> None:
    cards = (
        _make_card("Legal Card", legalities={"commander": "Legal"}),
        _make_card("Banned Card", legalities={"commander": "Banned"}),
        _make_card("Not Legal Card", legalities={"commander": "Not Legal"}),
    )
    result = MtgCardSet(cards).filter_format("commander")
    assert {c.name for c in result} == {"Legal Card"}


def test_filter_format_raises_on_unknown_format() -> None:
    cards = (_make_card("Card", legalities={"commander": "Legal", "modern": "Legal"}),)
    with pytest.raises(ValueError, match="unknown_format"):
        MtgCardSet(cards).filter_format("unknown_format")


def test_filter_format_empty_card_set_does_not_raise() -> None:
    result = MtgCardSet(()).filter_format("commander")
    assert list(result) == []


def test_filter_creatures_keeps_only_creature_cards() -> None:
    cards = (
        _make_card("Creature Card", types=["Creature"]),
        _make_card("Instant Card", types=["Instant"]),
        _make_card("Artifact Creature", types=["Artifact", "Creature"]),
        _make_card("Tribal Instant", types=["Tribal", "Instant"]),
    )
    result = MtgCardSet(cards).filter_creatures()
    assert {c.name for c in result} == {"Creature Card", "Artifact Creature"}


def test_creature_type_counts_ignores_non_creature_subtypes() -> None:
    cards = (
        _make_card("Llanowar Elves", types=["Creature"], subtypes=["Elf"]),
        _make_card("Darksteel Citadel", types=["Artifact", "Land"], subtypes=["Artifact"]),
        _make_card("Arrest", types=["Enchantment"], subtypes=["Aura"]),
    )
    counts = MtgCardSet(cards).creature_type_counts()
    assert counts == {"Elf": 1}
    assert "Artifact" not in counts
    assert "Aura" not in counts


def test_filter_format_handles_first_card_with_empty_legalities() -> None:
    cards = (
        _make_card("Empty Legalities Card", legalities={}),
        _make_card("Legal Card", legalities={"commander": "Legal"}),
        _make_card("Banned Card", legalities={"commander": "Banned"}),
    )
    result = MtgCardSet(cards).filter_format("commander")
    assert {c.name for c in result} == {"Legal Card"}


def test_filter_color_identity_keeps_cards_within_identity() -> None:
    cards = (
        _make_card("Mono-Green", color_identity=["G"]),
        _make_card("Green-White", color_identity=["G", "W"]),
        _make_card("Red", color_identity=["R"]),
        _make_card("Colorless", color_identity=[]),
    )
    result = MtgCardSet(cards).filter_color_identity("GW")
    assert {c.name for c in result} == {"Mono-Green", "Green-White", "Colorless"}


def test_filter_color_identity_colorless_only() -> None:
    cards = (
        _make_card("Colorless", color_identity=[]),
        _make_card("Blue Card", color_identity=["U"]),
    )
    result = MtgCardSet(cards).filter_color_identity("")
    assert {c.name for c in result} == {"Colorless"}


def test_filter_color_identity_raises_on_invalid_color() -> None:
    cards = (_make_card("Card", color_identity=["G"]),)
    with pytest.raises(ValueError, match="Invalid color"):
        MtgCardSet(cards).filter_color_identity("X")


def test_creature_type_counts() -> None:
    cards = (
        _make_card("Elvish Mystic", types=["Creature"], subtypes=["Elf", "Druid"]),
        _make_card("Llanowar Elves", types=["Creature"], subtypes=["Elf", "Druid"]),
        _make_card("Goblin Guide", types=["Creature"], subtypes=["Goblin", "Scout"]),
    )
    counts = MtgCardSet(cards).creature_type_counts()
    assert counts == {"Elf": 2, "Druid": 2, "Goblin": 1, "Scout": 1}


def test_filter_single_subtype_includes_single_subtype() -> None:
    cards = (_make_card("Pure Goblin", types=["Creature"], subtypes=["Goblin"]),)
    result = MtgCardSet(cards).filter_single_subtype()
    assert {c.name for c in result} == {"Pure Goblin"}


def test_filter_single_subtype_excludes_multi_subtype() -> None:
    cards = (_make_card("Elvish Mystic", types=["Creature"], subtypes=["Elf", "Druid"]),)
    result = MtgCardSet(cards).filter_single_subtype()
    assert list(result) == []


def test_filter_single_subtype_excludes_zero_subtypes() -> None:
    cards = (_make_card("Wall of Stone", types=["Creature"], subtypes=[]),)
    result = MtgCardSet(cards).filter_single_subtype()
    assert list(result) == []


def test_filter_single_subtype_mixed_set() -> None:
    cards = (
        _make_card("Pure Goblin", types=["Creature"], subtypes=["Goblin"]),
        _make_card("Elvish Mystic", types=["Creature"], subtypes=["Elf", "Druid"]),
        _make_card("Wall of Stone", types=["Creature"], subtypes=[]),
    )
    result = MtgCardSet(cards).filter_single_subtype()
    assert {c.name for c in result} == {"Pure Goblin"}

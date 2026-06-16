"""Tests for MtgCard."""

from lonis.mtg.card import MtgCard


def _face(
    *,
    layout: str = "normal",
    types: list[str] | None = None,
    subtypes: list[str] | None = None,
    supertypes: list[str] | None = None,
    color_identity: list[str] | None = None,
    colors: list[str] | None = None,
    converted_mana_cost: float = 0.0,
    legalities: dict[str, str] | None = None,
    is_funny: bool = False,
) -> dict[str, object]:
    return {
        "layout": layout,
        "types": types or [],
        "subtypes": subtypes or [],
        "supertypes": supertypes or [],
        "colorIdentity": color_identity or [],
        "colors": colors or [],
        "convertedManaCost": converted_mana_cost,
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


def test_card_is_hashable() -> None:
    faces = [_face(types=["Creature"], subtypes=["Elf"], legalities={"commander": "Legal"})]
    card = MtgCard.from_atomic_entry("Elvish Mystic", faces)
    assert card is not None
    assert hash(card) is not None
    assert len({card, card}) == 1


def test_from_atomic_entry_color_identity() -> None:
    faces = [
        _face(layout="transform", types=["Creature"], color_identity=["R", "G"], legalities={}),
        _face(layout="transform", types=["Creature"], color_identity=["R"], legalities={}),
    ]
    card = MtgCard.from_atomic_entry("Huntmaster of the Fells // Ravager of the Fells", faces)
    assert card is not None
    assert card.color_identity == frozenset({"R", "G"})


def test_from_atomic_entry_colorless_card() -> None:
    faces = [_face(types=["Artifact", "Creature"], color_identity=[], legalities={})]
    card = MtgCard.from_atomic_entry("Blightsteel Colossus", faces)
    assert card is not None
    assert card.color_identity == frozenset()


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


def test_from_atomic_entry_colors_single_face() -> None:
    faces = [_face(types=["Creature"], colors=["W"], legalities={})]
    card = MtgCard.from_atomic_entry("Serra Angel", faces)
    assert card is not None
    assert card.colors == frozenset({"W"})


def test_from_atomic_entry_colors_multi_face_aggregated() -> None:
    faces = [
        _face(layout="transform", types=["Creature"], colors=["R", "G"], legalities={}),
        _face(layout="transform", types=["Creature"], colors=["R"], legalities={}),
    ]
    card = MtgCard.from_atomic_entry("Huntmaster of the Fells // Ravager of the Fells", faces)
    assert card is not None
    assert card.colors == frozenset({"R", "G"})


def test_from_atomic_entry_colorless_colors() -> None:
    faces = [_face(types=["Artifact", "Creature"], colors=[], legalities={})]
    card = MtgCard.from_atomic_entry("Blightsteel Colossus", faces)
    assert card is not None
    assert card.colors == frozenset()


def test_from_atomic_entry_converted_mana_cost() -> None:
    faces = [_face(types=["Creature"], converted_mana_cost=3.0, legalities={})]
    card = MtgCard.from_atomic_entry("Serra Angel", faces)
    assert card is not None
    assert card.converted_mana_cost == 3.0

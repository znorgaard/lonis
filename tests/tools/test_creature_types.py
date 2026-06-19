"""End-to-end tests for the creature_types tool."""

import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from lonis.mtg.cache import MtgDataCache
from lonis.tools.creature_types import CardListMetric
from lonis.tools.creature_types import CreatureTypeMetric
from lonis.tools.creature_types import creature_types

_ATOMIC_DATA = {
    "Elvish Mystic": [
        {
            "layout": "normal",
            "types": ["Creature"],
            "subtypes": ["Elf", "Druid"],
            "supertypes": [],
            "colorIdentity": ["G"],
            "legalities": {"commander": "Legal", "modern": "Legal"},
            "isFunny": False,
        }
    ],
    "Goblin Guide": [
        {
            "layout": "normal",
            "types": ["Creature"],
            "subtypes": ["Goblin", "Scout"],
            "supertypes": [],
            "colorIdentity": ["R"],
            "legalities": {"commander": "Legal", "modern": "Legal"},
            "isFunny": False,
        }
    ],
    "Lightning Bolt": [
        {
            "layout": "normal",
            "types": ["Instant"],
            "subtypes": [],
            "supertypes": [],
            "colorIdentity": ["R"],
            "legalities": {"commander": "Legal", "modern": "Legal"},
            "isFunny": False,
        }
    ],
    "Ancestral Recall": [
        {
            "layout": "normal",
            "types": ["Instant"],
            "subtypes": [],
            "supertypes": [],
            "colorIdentity": ["U"],
            "legalities": {"commander": "Banned", "modern": "Not Legal"},
            "isFunny": False,
        }
    ],
    "Goblin Token": [
        {
            "layout": "token",
            "types": ["Creature"],
            "subtypes": ["Goblin"],
            "supertypes": [],
            "colorIdentity": ["R"],
            "legalities": {},
            "isFunny": False,
        }
    ],
}


def test_creature_types_writes_correct_types(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    creature_types(output=output)
    creature_type_names = {m.creature_type for m in CreatureTypeMetric.read(output)}
    assert creature_type_names == {"Elf", "Druid", "Goblin", "Scout"}


def test_creature_types_counts_are_correct(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    creature_types(output=output)
    metrics = {m.creature_type: m.count for m in CreatureTypeMetric.read(output)}
    assert metrics["Elf"] == 1
    assert metrics["Druid"] == 1
    assert metrics["Goblin"] == 1
    assert metrics["Scout"] == 1


def test_creature_types_sorted_count_desc_then_alpha(tmp_path: Path, mocker: MockerFixture) -> None:
    data = {
        "Elvish Mystic": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "colorIdentity": ["G"],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
        "Llanowar Elves": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "colorIdentity": ["G"],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
        "Goblin Guide": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Goblin", "Scout"],
                "supertypes": [],
                "colorIdentity": ["R"],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    output = tmp_path / "sorted.tsv"
    creature_types(output=output)
    metrics = list(CreatureTypeMetric.read(output))
    # Druid=2, Elf=2 (tie → alpha: Druid < Elf), Goblin=1, Scout=1 (tie → Goblin < Scout)
    assert metrics[0].creature_type == "Druid"
    assert metrics[1].creature_type == "Elf"
    assert metrics[2].creature_type == "Goblin"
    assert metrics[3].creature_type == "Scout"


def test_creature_types_invalid_format_raises(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    with pytest.raises(ValueError, match="notaformat"):
        creature_types(output=output, fmt="notaformat")


def test_creature_types_empty_result_writes_header_only(
    tmp_path: Path, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    data = {
        "Lightning Bolt": [
            {
                "layout": "normal",
                "types": ["Instant"],
                "subtypes": [],
                "supertypes": [],
                "colorIdentity": ["R"],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    output = tmp_path / "empty.tsv"
    with caplog.at_level(logging.WARNING, logger="lonis.tools.creature_types"):
        creature_types(output=output)
    metrics = list(CreatureTypeMetric.read(output))
    assert metrics == []
    assert "No creature types found" in caplog.text


def test_creature_types_identity_filter(tmp_path: Path, mocker: MockerFixture) -> None:
    # Elvish Mystic is G, Goblin Guide is R — filtering to G should exclude Goblin/Scout
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "identity.tsv"
    creature_types(output=output, identity="G")
    creature_type_names = {m.creature_type for m in CreatureTypeMetric.read(output)}
    assert "Elf" in creature_type_names
    assert "Druid" in creature_type_names
    assert "Goblin" not in creature_type_names
    assert "Scout" not in creature_type_names


def test_creature_types_invalid_identity_raises(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    with pytest.raises(ValueError, match="Invalid color"):
        creature_types(output=output, identity="X")


def test_creature_types_card_list_not_written_by_default(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    card_list = tmp_path / "cards.tsv"
    creature_types(output=tmp_path / "out.tsv")
    assert not card_list.exists()


def test_creature_types_card_list_contains_contributing_creatures(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    card_list = tmp_path / "cards.tsv"
    creature_types(output=tmp_path / "out.tsv", card_list=card_list)
    card_names = {m.name for m in CardListMetric.read(card_list)}
    assert "Elvish Mystic" in card_names
    assert "Goblin Guide" in card_names
    # non-creatures, banned cards, and tokens must not appear
    assert "Lightning Bolt" not in card_names
    assert "Ancestral Recall" not in card_names
    assert "Goblin Token" not in card_names


def test_creature_types_card_list_sorted_by_name(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    card_list = tmp_path / "cards.tsv"
    creature_types(output=tmp_path / "out.tsv", card_list=card_list)
    names = [m.name for m in CardListMetric.read(card_list)]
    assert names == sorted(names)


def test_creature_types_card_list_fields(tmp_path: Path, mocker: MockerFixture) -> None:
    data = {
        "Elvish Mystic": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "colorIdentity": ["G"],
                "colors": ["G"],
                "convertedManaCost": 1.0,
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    card_list = tmp_path / "cards.tsv"
    creature_types(output=tmp_path / "out.tsv", card_list=card_list)
    rows = list(CardListMetric.read(card_list))
    assert len(rows) == 1
    row = rows[0]
    assert row.name == "Elvish Mystic"
    assert row.colors == ["G"]
    assert row.color_identity == ["G"]
    assert row.converted_mana_cost == 1.0
    assert set(row.subtypes or []) == {"Elf", "Druid"}


def test_creature_types_single_subtype_flag(tmp_path: Path, mocker: MockerFixture) -> None:
    # Elvish Mystic has 2 subtypes (Elf, Druid) — should be excluded.
    # Goblin Guide has 2 subtypes (Goblin, Scout) — should be excluded.
    # Pure Goblin has 1 subtype (Goblin) — should be included.
    data = {
        "Elvish Mystic": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "colorIdentity": ["G"],
                "legalities": {"commander": "Legal", "modern": "Legal"},
                "isFunny": False,
            }
        ],
        "Goblin Guide": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Goblin", "Scout"],
                "supertypes": [],
                "colorIdentity": ["R"],
                "legalities": {"commander": "Legal", "modern": "Legal"},
                "isFunny": False,
            }
        ],
        "Pure Goblin": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Goblin"],
                "supertypes": [],
                "colorIdentity": ["R"],
                "legalities": {"commander": "Legal", "modern": "Legal"},
                "isFunny": False,
            }
        ],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    output = tmp_path / "out.tsv"
    creature_types(output=output, single_subtype=True)
    metrics = {m.creature_type: m.count for m in CreatureTypeMetric.read(output)}
    assert metrics == {"Goblin": 1}


def test_creature_types_single_subtype_card_list(tmp_path: Path, mocker: MockerFixture) -> None:
    data = {
        "Elvish Mystic": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "colorIdentity": ["G"],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
        "Pure Goblin": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Goblin"],
                "supertypes": [],
                "colorIdentity": ["R"],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    card_list = tmp_path / "cards.tsv"
    creature_types(output=tmp_path / "out.tsv", card_list=card_list, single_subtype=True)
    names = {m.name for m in CardListMetric.read(card_list)}
    assert "Pure Goblin" in names
    assert "Elvish Mystic" not in names

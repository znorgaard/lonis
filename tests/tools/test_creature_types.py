"""End-to-end tests for the creature_types tool."""

import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from lonis.mtg.cache import MtgDataCache
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
        creature_types(output=output, format="notaformat")


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

"""CLI tool: report creature types and their card counts for a given Magic format."""

from __future__ import annotations

import logging
from pathlib import Path

from fgmetric import Metric
from fgmetric import MetricWriter

from lonis.mtg.cache import MtgDataCache
from lonis.mtg.card_set import MtgCardSet

logger = logging.getLogger(__name__)


class CreatureTypeMetric(Metric):
    """One row of creature type output: the type name and number of cards with that type."""

    creature_type: str
    count: int


class CardListMetric(Metric):
    """One row of card list output: a creature card that contributed to the type counts."""

    name: str
    colors: list[str] | None
    color_identity: list[str] | None
    converted_mana_cost: float
    types: list[str] | None
    subtypes: list[str] | None
    supertypes: list[str] | None


def creature_types(
    *,
    output: Path,
    fmt: str = "commander",
    identity: str | None = None,
    card_list: Path | None = None,
    single_subtype: bool = False,
) -> None:
    """Report all creature types and the number of cards with each type in a format.

    Args:
        output: Path to write the output TSV file.
        fmt: Magic: The Gathering format to filter cards by (e.g. commander, modern, standard).
        identity: Commander color identity filter as MTG color letters (W, U, B, R, G), e.g. WUG.
                  Only cards whose color identity fits within these colors are included.
                  Omit to include all colors.
        card_list: Optional path to write a TSV of all creature cards that contributed to the
                   counts. Omit to skip writing the card list.
        single_subtype: Only include creatures that have exactly one subtype.
    """
    data = MtgDataCache().load()
    card_set = MtgCardSet.from_atomic_data(data)
    card_set = card_set.filter_format(fmt)
    if identity is not None:
        card_set = card_set.filter_color_identity(identity)
    creature_set = card_set.filter_creatures()
    if single_subtype:
        creature_set = creature_set.filter_single_subtype()
    counts = creature_set.creature_type_counts()
    if not counts:
        logger.warning("No creature types found for format %r — writing empty output", fmt)
    metrics = [
        CreatureTypeMetric(creature_type=ct, count=count)
        for ct, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),  # most common first, ties alphabetical
        )
    ]
    with MetricWriter(CreatureTypeMetric, output) as writer:
        writer.writeall(metrics)
    if card_list is not None:
        with MetricWriter(CardListMetric, card_list) as writer:
            writer.writeall(
                CardListMetric(
                    name=card.name,
                    colors=sorted(card.colors) or None,
                    color_identity=sorted(card.color_identity) or None,
                    converted_mana_cost=card.converted_mana_cost,
                    types=sorted(card.types) or None,
                    subtypes=sorted(card.subtypes) or None,
                    supertypes=sorted(card.supertypes) or None,
                )
                for card in sorted(creature_set, key=lambda c: c.name)
            )

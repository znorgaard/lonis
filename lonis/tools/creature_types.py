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


def creature_types(*, output: Path, fmt: str = "commander", identity: str | None = None) -> None:
    """Report all creature types and the number of cards with each type in a format.

    Args:
        output: Path to write the output TSV file.
        fmt: Magic: The Gathering format to filter cards by (e.g. commander, modern, standard).
        identity: Commander color identity filter as MTG color letters (W, U, B, R, G), e.g. WUG.
                  Only cards whose color identity fits within these colors are included.
                  Omit to include all colors.
    """
    data = MtgDataCache().load()
    card_set = MtgCardSet.from_atomic_data(data)
    card_set = card_set.filter_format(fmt)
    if identity is not None:
        card_set = card_set.filter_color_identity(identity)
    counts = card_set.filter_creatures().creature_type_counts()
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

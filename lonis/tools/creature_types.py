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


def creature_types(*, output: Path, fmt: str = "commander") -> None:
    """Report all creature types and the number of cards with each type in a format.

    Args:
        output: Path to write the output TSV file.
        fmt: Magic: The Gathering format to filter cards by (e.g. commander, modern, standard).
    """
    data = MtgDataCache().load()
    card_set = MtgCardSet.from_atomic_data(data)
    counts = card_set.filter_format(fmt).filter_creatures().creature_type_counts()
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

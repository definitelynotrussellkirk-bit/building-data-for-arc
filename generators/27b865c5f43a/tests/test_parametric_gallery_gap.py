"""Focused, non-production tests for the proposed gallery_gap prototype."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
sys.path.insert(0, str(HOME / "workspace" / "parametric"))
from reference_probe import canonical_pairs, rule_output  # noqa: E402
from gallery_gap import (  # noqa: E402
    ALLOWED_GAPS,
    DEFAULT_GAP,
    choose_gap,
    gallery_output,
    normalized_hash,
    racket_source,
)


def test_default_source_remains_the_selected_authority():
    source = racket_source(DEFAULT_GAP)
    assert normalized_hash(source) == "de4d9d03f710"
    assert hashlib.sha256(source.encode()).hexdigest()


@pytest.mark.parametrize("gap", ALLOWED_GAPS)
def test_each_gap_is_deterministic_and_changes_only_gallery_spacing(gap):
    source = racket_source(gap)
    assert source == racket_source(gap)
    pair = canonical_pairs()[0]
    output = gallery_output(pair["input"], gap)
    assert len(output) == 9 + 2 * gap
    assert len(output[0]) == 9 + 2 * gap
    if gap == DEFAULT_GAP:
        assert output == pair["output"] == rule_output(pair["input"])


def test_settings_are_pairwise_distinguishable_on_every_canonical_input():
    for pair in canonical_pairs():
        outputs = [gallery_output(pair["input"], gap) for gap in ALLOWED_GAPS]
        assert len({repr(output) for output in outputs}) == len(ALLOWED_GAPS)


def test_seed_choice_is_once_per_episode_and_covers_bounded_domain():
    assert choose_gap(17) == choose_gap(17)
    assert {choose_gap(seed) for seed in range(30)} == set(ALLOWED_GAPS)


@pytest.mark.parametrize("value", (-1, 3, 1.0, True, "1", None))
def test_invalid_gap_is_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        racket_source(value)

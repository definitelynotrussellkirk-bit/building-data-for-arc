"""Focused regressions for public-call scalar validation."""

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)


def _load_generator():
    """Use the selected portable source without changing cached dependencies.

    The retained frozen fixture imports this task first in the same pytest
    process.  Re-running ``load_selected_generator`` afterward correctly rejects
    those already-cached legacy dependencies as cross-tree.  The task-test
    controller exposes the exact selected file through ``GENERATOR_UNDER_TEST``;
    direct repository runs fall back to the source under ``find_root``.
    """
    source = Path(
        os.environ.get(
            "GENERATOR_UNDER_TEST",
            ROOT / "generators/dc050b56cac4/generator.py",
        )
    ).resolve()
    body = source.read_bytes()
    spec = importlib.util.spec_from_file_location("dc050b56_review_hardening", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    exec(compile(body, str(source), "exec"), module.__dict__)
    return module, source, hashlib.sha256(body).hexdigest()


GEN, SOURCE, SOURCE_SHA256 = _load_generator()


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_a_literal_integer(seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", None])
def test_sample_index_requires_a_literal_integer(sample_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.generate(991, sample_index, difficulty="hard")


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        GEN.generate(991, -1)


def test_schedule_profile_uses_the_same_scalar_contract():
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.schedule_profile(True, 0)
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.schedule_profile(0, 0.0)
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        GEN.schedule_profile(0, -1)

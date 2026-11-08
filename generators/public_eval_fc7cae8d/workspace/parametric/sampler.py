"""Stable, setting-independent teaching and private-query input banks."""

import hashlib
import importlib.util
from pathlib import Path
import random


def sample_banks(seed):
    """Return six teaching inputs and four shuffled query inputs, all fresh."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be between 0 and 2**63 - 1")
    generator_path = Path(__file__).resolve().parents[2] / "generator.py"
    spec = importlib.util.spec_from_file_location("fc7cae8d_exact_source_generator", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the task's exact generator source")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    train = [generator.generate(seed, index) for index in range(6)]
    query = [generator.generate(seed, index) for index in range(100, 104)]
    digest = hashlib.sha256(
        f"public_eval_fc7cae8d|1.0.0|native-completed-query-bank-order|{seed}".encode("ascii")
    ).digest()
    random.Random(int.from_bytes(digest, "big")).shuffle(query)
    return train, query

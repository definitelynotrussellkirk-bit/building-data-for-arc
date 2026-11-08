"""Refusal tests using real task examples; fixture labels are Python mirrors."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json

import pytest
from reviewer_support import find_root


TASK_ID = "40e85135fbf8"
ROOT = find_root(__file__)


@pytest.fixture
def checked():
    # task_tests mirrors task workspace files at their library-relative paths.
    home = next(path for path in (ROOT / "generators" / TASK_ID,
                ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID)
                if (path / "generator.py").is_file())
    path = home / "workspace" / "generate_checked_lessons.py"
    spec = importlib.util.spec_from_file_location("checked_lessons_test_helper", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def population(checked):
    gen, source, source_hash = checked.load_generator()
    def episode(seed):
        pairs = []
        for index in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(seed, index)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        return {"task_id": TASK_ID, "train": pairs[:-1], "test": pairs[-1:],
                "executed_rule_hash": gen.RULE_HASH,
                "provenance": {"generator_sha256": source_hash, "reference": "canonical"}}
    return gen, source, source_hash, [episode(0), episode(17)]


def write(checked, population, out, episodes=None, source=None):
    gen, actual_source, source_hash, original = population
    return checked.write_checked(original if episodes is None else episodes, out,
                                 gen=gen, source=source or actual_source,
                                 source_hash=source_hash, count=2, n_test=1)


def test_valid_episodes_are_written_as_unchanged_standard_jsonl(checked, population, tmp_path):
    out = tmp_path / "episodes.jsonl"
    write(checked, population, out)
    assert [json.loads(line) for line in out.read_text().splitlines()] == population[3]


@pytest.mark.parametrize("defect", ("episode_count", "train_count", "query_count",
                                    "source_hash", "missing_gap_lessons", "wrong_label"))
def test_bad_population_is_rejected_before_any_output(checked, population, tmp_path, defect):
    gen, _, _, original = population
    episodes = deepcopy(original)
    if defect == "episode_count":
        episodes.pop()
    elif defect == "train_count":
        episodes[1]["train"] = episodes[1]["train"][:3]
    elif defect == "query_count":
        episodes[1]["test"] = []
    elif defect == "source_hash":
        episodes[1]["provenance"]["generator_sha256"] = "0" * 64
    elif defect == "missing_gap_lessons":
        # A sampler can skip indices. Six accepted inputs alone do not prove
        # that the materialized lesson retains the scheduled gap witnesses.
        episodes[1]["train"] = []
        for index in range(0, gen.EXAMPLES_NEEDED * 3, 3):
            grid = gen.generate(17, index)
            episodes[1]["train"].append({"input": grid, "output": gen.rule_mirror(grid)})
    else:
        output = episodes[1]["train"][0]["output"]
        output[0][0] = (output[0][0] + 1) % 10
    out = tmp_path / "refused.jsonl"
    with pytest.raises(ValueError):
        write(checked, population, out, episodes=episodes)
    assert not out.exists()


def test_changed_source_is_rejected_before_output(checked, population, tmp_path):
    source = tmp_path / "changed_generator.py"
    source.write_bytes(population[1].read_bytes() + b"\n")
    assert hashlib.sha256(source.read_bytes()).hexdigest() != population[2]
    out = tmp_path / "refused.jsonl"
    with pytest.raises(ValueError, match="source"):
        write(checked, population, out, source=source)
    assert not out.exists()


def test_existing_output_is_preserved(checked, population, tmp_path):
    out = tmp_path / "retained.jsonl"
    out.write_text("retained evidence\n")
    with pytest.raises(FileExistsError):
        write(checked, population, out)
    assert out.read_text() == "retained evidence\n"

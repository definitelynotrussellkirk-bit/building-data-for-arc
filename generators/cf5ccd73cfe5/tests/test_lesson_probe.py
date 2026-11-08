"""Focused tests of the bounded ambiguity diagnostic's verdict bookkeeping."""
import importlib.util
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "task_lesson_probe", Path(__file__).resolve().parents[1] / "workspace/lesson_probe.py"
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_demo_fit_and_query_disagreement_are_both_required():
    pairs = [{"input": [[i]], "output": [[i]]} for i in range(4)]
    rivals = {
        "agrees_all": lambda grid: grid,
        "fails_demo": lambda grid: [[9]],
        "query_only": lambda grid: [[8]] if grid == [[3]] else grid,
    }
    assert probe.ambiguous_rivals(pairs, rivals, 3) == {"query_only": [[8]]}
    assert probe.ambiguous_rivals(pairs, rivals, 0) == {}


def test_search_retains_actual_reference_labels_and_consecutive_indices(monkeypatch):
    calls = []

    class Generator:
        @staticmethod
        def generate(seed, index, difficulty=None):
            calls.append((seed, index, difficulty))
            return [[index]]

        @staticmethod
        def self_check(grid, difficulty=None):
            return []

    monkeypatch.setattr(probe, "execute", lambda bridge, text, grid: [[grid[0][0] + 1]])
    rival = lambda grid: [[9 if grid[0][0] == 1 else grid[0][0] + 1]]
    witness, counts = probe.search(
        Generator, {"one": rival}, None, "test", seed_start=7, seeds=2, starts=3, bands=["easy"]
    )
    assert calls == [(7, i, "easy") for i in range(4)]
    assert witness["consecutive_sample_indices"] == [0, 1, 2, 3]
    assert witness["query_sample_index"] == 1
    assert witness["demo_sample_indices"] == [0, 2, 3]
    assert witness["private_query_output"] == [[2]]
    assert witness["public_challenge"]["test"] == [{"input": [[1]]}]
    assert witness["surviving_rival_predictions"] == {"one": [[9]]}
    assert counts["reference_executions"] == 4


def test_no_witness_is_reported_without_fabrication(monkeypatch):
    class Generator:
        generate = staticmethod(lambda seed, index, difficulty=None: [[index]])
        self_check = staticmethod(lambda grid, difficulty=None: [])

    monkeypatch.setattr(probe, "execute", lambda bridge, text, grid: grid)
    witness, counts = probe.search(
        Generator, {"equivalent": lambda grid: grid}, None, "test",
        seed_start=0, seeds=2, starts=3, bands=["easy", "hard"],
    )
    assert witness is None
    assert counts == {"generated_inputs": 24, "reference_executions": 24,
                      "consecutive_windows": 12, "query_rotations_scored": 48}

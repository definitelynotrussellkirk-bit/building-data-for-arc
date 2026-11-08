"""Focused tests of the proposed target-color prototype, not canonical repair gates."""
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace/parametric/prototype.py"
ORIGINAL_RULE = (
    "(rule! (let ((bb (bbox-of-cells (find-color g 9)))) "
    "(subgrid g (first bb) (second bb) (third bb) (fourth bb))))"
)


@lru_cache(maxsize=1)
def prototype():
    assert PROTOTYPE.is_file(), "The task-local runnable prototype is not implemented"
    spec = importlib.util.spec_from_file_location("marker_crop_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_rule_preserves_exact_canonical_expression():
    p = prototype()
    assert p.rule_source() == ORIGINAL_RULE
    for color in (2, 5, 9):
        assert p.rule_source(color) == ORIGINAL_RULE.replace("g 9", f"g {color}")


@pytest.mark.parametrize("color", [True, 0, 1, 10, -1, "9", None])
def test_unsupported_parameter_values_are_rejected(color):
    with pytest.raises(ValueError, match="target_color"):
        prototype().rule_source(color)


def test_seed_picks_one_setting_and_sampling_is_deterministic():
    p = prototype()
    before = random.getstate()
    selection = p.select_seeds(20261019, 1)
    assert {p.target_for_seed(seed) for seed in selection["seeds"]} == {2, 5, 9}
    for seed in selection["seeds"]:
        first = p.sample_episode(seed)
        assert first == p.sample_episode(seed)
        assert first["parameters"] == {"target_color": p.target_for_seed(seed)}
        assert first["program"] == p.rule_source(p.target_for_seed(seed))
        assert len(first["inputs"]) == 4
        for grid in first["inputs"]:
            boxes = [p.bbox(grid, color) for color in (2, 5, 9)]
            assert len(set(boxes)) == 3
            assert len({json.dumps(p.python_crop(grid, color)) for color in (2, 5, 9)}) == 3
    assert random.getstate() == before


def test_inclusive_crop_preserves_every_interior_color():
    p = prototype()
    grid = [
        [0, 0, 2, 1, 2, 0, 0, 0],
        [0, 9, 0, 3, 9, 0, 0, 0],
        [0, 0, 6, 0, 0, 0, 5, 0],
        [0, 9, 4, 0, 9, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    before = json.dumps(grid)
    assert p.python_crop(grid, 9) == [[9, 0, 3, 9], [0, 6, 0, 0], [9, 4, 0, 9]]
    assert p.python_crop(grid, 2) == [[2, 1, 2]]
    assert p.python_crop(grid, 5) == [[5]]
    assert json.dumps(grid) == before


def test_public_challenges_omit_private_fields_and_query_answers():
    p = prototype()
    pairs = [{"input": [[n]], "output": [[n + 1]]} for n in range(4)]
    for query_index in range(4):
        public = p.public_challenge(pairs, query_index)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert public["test"] == [{"input": pairs[query_index]["input"]}]
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        public["test"][0]["input"][0][0] = 99
        assert pairs[query_index]["input"] == [[query_index]]


def test_rotation_scoring_distinguishes_refutation_ambiguity_and_survival():
    p = prototype()
    chosen = [[[9]], [[9]], [[9]], [[9]]]
    predictions = {9: chosen, 2: [[[2]], *chosen[1:]], 5: chosen}
    held_out_witness = p.score_rotation(predictions, 9, 0)
    assert {r["target_color"]: r["status"] for r in held_out_witness["rivals"]} == {
        2: "ambiguous_query", 5: "survived_all"
    }
    retained_witness = p.score_rotation(predictions, 9, 3)
    rows = {r["target_color"]: r for r in retained_witness["rivals"]}
    assert rows[2]["status"] == "refuted_by_demonstrations"
    assert rows[2]["demonstration_mismatches"] == [0]
    assert rows[5]["status"] == "survived_all"


def test_actual_racket_evidence_covers_settings_and_all_query_rotations(tmp_path):
    p = prototype()
    out = tmp_path / "actual-racket"
    report = p.run_evidence(out, base_seed=20261019, per_setting=1)
    assert report["status"] == "pass", report
    assert report["summary"] == {
        "episodes": 3, "episode_pairs": 12, "racket_rule_applications": 36,
        "racket_canaries": 3, "python_mirror_matches": 36,
        "production_rival_checks": 6, "query_rotations": 12,
        "rotation_rival_checks": 24, "refuted_rotation_rivals": 24,
        "ambiguous_rotation_rivals": 0, "survived_rotation_rivals": 0,
    }
    assert len(report["rules"]) == 3
    for row in report["rules"]:
        body = (out / row["path"]).read_bytes()
        assert body.decode() == p.rule_source(row["parameters"]["target_color"])
        assert hashlib.sha256(body).hexdigest() == row["sha256"]
        execution = json.loads((out / row["execution_path"]).read_text())
        assert execution["receipt"]["backend"] == "racket"
        assert execution["receipt"]["status"] == "pass"
        assert len(execution["receipt"]["test_outputs"]) == 12
    for row in report["episodes"]:
        private = json.loads((out / row["private_path"]).read_text())
        public_path = out / row["public_path"]
        public = json.loads(public_path.read_text())
        assert public == p.public_challenge(private["train"] + private["test"], 3)
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == row["public_sha256"]
        assert len(private["rotations"]) == 4
        assert all(rival["status"] == "refuted_by_demonstrations"
                   for rotation in private["rotations"] for rival in rotation["rivals"])
    witness = json.loads((out / "private/cross_setting_witness.json").read_text())
    assert len({json.dumps(row["output"]) for row in witness["settings"]}) == 3


def test_existing_evidence_is_never_overwritten(tmp_path):
    p = prototype()
    out = tmp_path / "occupied"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("original evidence")
    with pytest.raises(FileExistsError):
        p.run_evidence(out, base_seed=0, per_setting=1)
    assert list(out.iterdir()) == [sentinel]
    assert sentinel.read_text() == "original evidence"


def test_unavailable_racket_is_retained_as_error_without_public_labels(tmp_path):
    p = prototype()
    out = tmp_path / "missing-racket"
    report = p.run_evidence(out, base_seed=0, per_setting=1,
                            racket_path=str(tmp_path / "no-such-racket"))
    assert report["status"] == "error"
    assert not list((out / "public").glob("*.json"))
    assert json.loads((out / "report.json").read_text())["status"] == "error"
    failures = list((out / "private/racket").glob("*.json"))
    assert len(failures) == 1
    assert json.loads(failures[0].read_text())["receipt"]["status"] == "fail"

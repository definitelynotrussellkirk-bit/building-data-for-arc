"""Focused contract tests for the task-local repeat-count prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402

TASK_ID = "11c53dabb028"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "repeat-count prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_prototype_11c53dabb028", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_prototype_module_exists_and_exposes_repeat_contract():
    proto = load_prototype()
    assert proto.PARAMETER_NAMES == ("vertical_repeats", "horizontal_repeats")
    assert proto.ALLOWED_REPEATS == (1, 2)
    assert proto.DEFAULT_SETTING == (2, 2)
    assert proto.SETTINGS == ((1, 1), (1, 2), (2, 1), (2, 2))


def canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_default_program_is_exact_canonical_and_alternatives_change_only_repeats():
    proto = load_prototype()
    source = canonical_row()["program_solution"]
    assert proto.program_for(2, 2) == source
    assert normalized_hash(source) == "573d7b5ea64c"
    assert proto.normalized_program_hash(2, 2) == "573d7b5ea64c"

    vertical_once = proto.program_for(1, 2)
    horizontal_once = proto.program_for(2, 1)
    once = proto.program_for(1, 1)
    assert "(* 1 h)" in vertical_once and "(* 2 w)" in vertical_once
    assert "(* 2 h)" in horizontal_once and "(* 1 w)" in horizontal_once
    assert "(* 1 h)" in once and "(* 1 w)" in once
    assert vertical_once.replace("(* 1 h)", "(* 2 h)", 1) == source
    assert horizontal_once.replace("(* 1 w)", "(* 2 w)", 1) == source
    assert once.replace("(* 1 h)", "(* 2 h)", 1).replace("(* 1 w)", "(* 2 w)", 1) == source


def test_default_solver_matches_canonical_pairs_and_repeat_shapes_without_mutation():
    proto = load_prototype()
    row = canonical_row()
    for pair in [*row["train"], *row["test"]]:
        grid = deepcopy(pair["input"])
        assert proto.solve(grid, vertical_repeats=2, horizontal_repeats=2) == pair["output"]
        assert grid == pair["input"]

    grid = [[0, 3, 0], [4, 0, 4]]
    original = deepcopy(grid)
    expected_tile = [[3, 0, 3], [0, 3, 0]]
    for setting in proto.SETTINGS:
        output = proto.solve(
            grid, vertical_repeats=setting[0], horizontal_repeats=setting[1]
        )
        assert len(output) == setting[0] * len(grid)
        assert len(output[0]) == setting[1] * len(grid[0])
        assert output == [
            [expected_tile[r % 2][c % 3] for c in range(setting[1] * 3)]
            for r in range(setting[0] * 2)
        ]
    assert grid == original


def test_repeat_and_seed_validation_are_strict_and_output_bound_is_preserved():
    proto = load_prototype()
    for bad in (None, True, 0, 3, 1.5, "2"):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(bad, 2)
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(2, bad)

    for bad_seed in (True, -1, 1.5, "7"):
        with pytest.raises((TypeError, ValueError)):
            proto.select_setting(bad_seed)

    assert proto.select_setting(12345) == proto.select_setting(12345)
    assert proto.select_setting(12345) in proto.SETTINGS

    boundary = [[7 for _ in range(15)] for _ in range(15)]
    boundary[14][14] = 0
    output = proto.solve(boundary, vertical_repeats=2, horizontal_repeats=2)
    assert (len(output), len(output[0])) == (30, 30)


def all_pairs(episode: dict) -> list[dict]:
    return [*episode["train"], *episode["test"]]


def test_episode_fixes_setting_and_has_three_demos_four_distinct_queries():
    proto = load_prototype()
    episode = proto.generate_episode(
        20261023,
        vertical_repeats=1,
        horizontal_repeats=2,
        n_train=3,
        n_test=4,
    )
    assert episode == proto.generate_episode(
        20261023,
        vertical_repeats=1,
        horizontal_repeats=2,
        n_train=3,
        n_test=4,
    )
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["parameters"] == {
        "vertical_repeats": 1,
        "horizontal_repeats": 2,
    }
    assert episode["program"] == proto.program_for(1, 2)

    pairs = all_pairs(episode)
    input_hashes = [proto.grid_hash(pair["input"]) for pair in pairs]
    assert len(input_hashes) == len(set(input_hashes)) == 7
    assert {tuple(pair["meta"]["setting"]) for pair in pairs} == {(1, 2)}

    intended = (1, 2)
    rivals = [setting for setting in proto.SETTINGS if setting != intended]
    for pair in pairs:
        assert pair["output"] == proto.solve(
            pair["input"], vertical_repeats=1, horizontal_repeats=2
        )
        assert len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30
        assert all(
            proto.solve(
                pair["input"],
                vertical_repeats=rival[0],
                horizontal_repeats=rival[1],
            )
            != pair["output"]
            for rival in rivals
        )

    for rival in rivals:
        assert not all(
            proto.solve(
                demo["input"],
                vertical_repeats=rival[0],
                horizontal_repeats=rival[1],
            )
            == demo["output"]
            for demo in episode["train"]
        )

    partial = proto.generate_episode(20261023, vertical_repeats=2)
    assert partial["parameters"]["vertical_repeats"] == 2
    assert partial["parameters"]["horizontal_repeats"] in proto.ALLOWED_REPEATS

    for field in ("n_train", "n_test"):
        for bad in (True, 0, -1, 1.5, "4"):
            with pytest.raises((TypeError, ValueError)):
                proto.generate_episode(7, **{field: bad})


def test_public_projection_masks_private_fields_and_id_uses_visible_bytes_only():
    proto = load_prototype()
    episode = proto.generate_episode(314159, vertical_repeats=2, horizontal_repeats=1)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    original_bytes = proto.public_bytes(episode)
    original_id = proto.public_id(episode)
    assert hashlib.sha256(original_bytes).hexdigest() == original_id

    changed_private = deepcopy(episode)
    changed_private["parameters"] = {
        "vertical_repeats": 1,
        "horizontal_repeats": 1,
    }
    changed_private["program"] = "private replacement"
    changed_private["meta"]["seed"] = 999999
    for pair in changed_private["test"]:
        pair["output"] = [[9]]
        pair["meta"]["private_note"] = "changed"
    assert proto.public_bytes(changed_private) == original_bytes
    assert proto.public_id(changed_private) == original_id

    changed_visible = deepcopy(episode)
    changed_visible["test"][0]["input"][0][0] = (
        changed_visible["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_id(changed_visible) != original_id

VERIFY_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "verify.py"


def load_verifier():
    assert VERIFY_PATH.is_file(), "repeat-count Racket verifier has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_verify_11c53dabb028", VERIFY_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_racket_verifier_materializes_all_settings_and_opaque_public_files(tmp_path):
    verify = load_verifier()
    artifact_dir = tmp_path / "artifacts"
    report = verify.build_report(seed_base=20261023, artifact_dir=artifact_dir)

    assert report["schema"] == "11c53dabb028-parametric-repeat-count-v1"
    assert report["status"] == "proposed_prototype_not_selected"
    assert report["task_id"] == TASK_ID
    assert report["counts"] == {
        "settings": 4,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
        "pairs": 28,
        "rival_pair_checks": 84,
        "query_rival_checks": 48,
        "boundary_checks": 12,
    }
    assert report["canonical"] == {
        "default_setting": {
            "vertical_repeats": 2,
            "horizontal_repeats": 2,
        },
        "program_exact": True,
        "normalized_rule_hash": "573d7b5ea64c",
        "canonical_pairs_racket_exact": True,
        "canonical_pair_count": 4,
    }
    for key in (
        "all_racket_exact",
        "all_rival_racket_python_exact",
        "all_demos_refute_all_rivals",
        "all_queries_identifiable_from_demos",
        "all_queries_setting_sensitive",
        "all_public_challenges_masked",
        "public_ids_sorted_unique",
        "all_boundary_racket_exact",
    ):
        assert report[key] is True, key

    assert len(report["settings"]) == 4
    assert {
        (
            row["setting"]["vertical_repeats"],
            row["setting"]["horizontal_repeats"],
        )
        for row in report["settings"]
    } == set(load_prototype().SETTINGS)
    assert len(report["public_ids"]) == 4
    assert report["public_ids"] == sorted(report["public_ids"])

    public_files = sorted((artifact_dir / "public").glob("challenge-*.json"))
    private_rules = sorted((artifact_dir / "private" / "rules").glob("*.rkt"))
    private_episodes = sorted((artifact_dir / "private" / "episodes").glob("*.json"))
    assert len(public_files) == len(private_rules) == len(private_episodes) == 4
    for path in public_files:
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        assert path.stem.removeprefix("challenge-") == hashlib.sha256(path.read_bytes()).hexdigest()


def test_prototype_cli_writes_public_three_demo_four_query_challenge(tmp_path):
    out = tmp_path / "challenge.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(PROTOTYPE_PATH),
            "--seed",
            "17",
            "--vertical-repeats",
            "2",
            "--horizontal-repeats",
            "1",
            "--train",
            "3",
            "--test",
            "4",
            "--public",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(out.read_text())
    assert len(payload["train"]) == 3
    assert len(payload["test"]) == 4
    assert all("output" in pair for pair in payload["train"])
    assert all("output" not in pair for pair in payload["test"])

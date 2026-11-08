"""Cyclic lesson checks for the default, unoverridden six-phase sampler.

The broad screen uses independent Python geometry labels and is not reference
execution. The separate Racket test labels 18 inputs through public Catalog.apply.
Run that test through the packet's run_with_racket.py wrapper, which must set an
absolute RACKET_PATH; without that configuration it skips visibly.

Set FRAME_LESSON_SCREEN_DIR to retain compact receipts at a chosen location.
The screen checks defaults only. Exact custom-control geometry is covered in
test_frame_contract.py; custom lessons have no schedule-identifiability claim.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


# Reuse the existing independent component parser without importing its tests
# into this module's namespace or relying on pytest's working directory.
_GEOMETRY_PATH = Path(__file__).resolve().with_name("test_frame_contract.py")
_GEOMETRY_SPEC = importlib.util.spec_from_file_location("frame_lesson_geometry", _GEOMETRY_PATH)
assert _GEOMETRY_SPEC is not None and _GEOMETRY_SPEC.loader is not None
_GEOMETRY = importlib.util.module_from_spec(_GEOMETRY_SPEC)
sys.modules[_GEOMETRY_SPEC.name] = _GEOMETRY
_GEOMETRY_SPEC.loader.exec_module(_GEOMETRY)

from reviewer_support import find_root, normalize_grid

ROOT = find_root(__file__)
if (ROOT / "src" / "arcpuzzles").is_dir():
    sys.path.insert(0, str(ROOT / "src"))
GEN = _GEOMETRY.GEN
SOURCE = Path(GEN.__file__).resolve()
SOURCE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
TASK_ID = "31b8bedd699a"
BANDS = ("easy", "medium", "hard")
DEFAULT_SCOPE = (
    "Only unoverridden default production draws are screened. "
    "No custom-control lesson-identifiability claim is made."
)
PYTHON_LABEL_BASIS = (
    "Independent Python component/geometry oracle from test_frame_contract.py; "
    "not canonical Racket execution."
)


def _grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _predict(solve, grid):
    try:
        return {"output": normalize_grid(solve(deepcopy(grid))), "error": None}
    except Exception as exc:
        return {"output": None, "error": f"{type(exc).__name__}: {exc}"}


@pytest.fixture(scope="module")
def screen_state(tmp_path_factory):
    rivals = getattr(GEN, "LESSON_COMPETITORS", None)
    assert isinstance(rivals, dict) and rivals, "Declare the live lesson competitors"
    assert all(isinstance(name, str) and callable(solve) for name, solve in rivals.items())
    assert getattr(GEN, "EXAMPLES_NEEDED", None) == 5
    assert getattr(GEN, "LESSON_SCHEDULE_PERIOD", None) == 6
    assert callable(getattr(GEN, "schedule_profile", None))
    assert callable(getattr(GEN, "rule_mirror", None))
    configured_output = os.environ.get("FRAME_LESSON_SCREEN_DIR")
    evidence_dir = (Path(configured_output).resolve() if configured_output
                    else tmp_path_factory.mktemp("frame-lesson-screen"))
    state = {"rivals": dict(rivals), "cache": {}, "samples": {}, "screens": [],
             "evidence_dir": evidence_dir, "first_failures": {}, "reference_receipt": None}
    yield state
    failures = Counter()
    for result in state["screens"]:
        for failure in result["ambiguities"]:
            failures[(failure["rival"], failure["query_profile"], failure["query_kind"])] += 1
    receipt = {
        "schema": "frame-lesson-python-screen-v1", "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "argv": list(sys.argv), "cwd": str(Path.cwd()), "scope": DEFAULT_SCOPE,
        "generator_sha256": SOURCE_SHA256,
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "geometry_helper_sha256": hashlib.sha256(_GEOMETRY_PATH.read_bytes()).hexdigest(),
        "source_unchanged_through_run": hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256,
        "label_basis": PYTHON_LABEL_BASIS, "overrides": {},
        "declared_rivals": list(state["rivals"]),
        "screened_seed_band_pairs": [{"seed": result["seed"], "difficulty": result["difficulty"]}
                                     for result in state["screens"]],
        "window_starts": list(range(6)), "query_positions": list(range(6)),
        "counts": {
            "seed_band_pairs": len(state["screens"]),
            "cyclic_windows": 6 * len(state["screens"]),
            "query_holdouts": 36 * len(state["screens"]),
            "production_holdouts": 6 * len(state["screens"]),
            "rotated_holdouts": 30 * len(state["screens"]),
            "unique_cached_inputs": len(state["cache"]),
            "mirror_mismatches": sum(len(result["mirror_mismatches"]) for result in state["screens"]),
            "prediction_errors": sum(len(result["prediction_errors"]) for result in state["screens"]),
            "ambiguities": sum(failures.values()),
        },
        "ambiguities": [{"rival": key[0], "query_profile": key[1], "query_kind": key[2], "count": count}
                        for key, count in sorted(failures.items())],
        "first_failure_receipts": list(state["first_failures"].values()),
        "reference_receipt": state["reference_receipt"],
    }
    _write_json(evidence_dir / f"python-screen-{SOURCE_SHA256[:12]}.json", receipt)


def _sample(state, seed, sample_index, difficulty):
    sample_key = (seed, sample_index, difficulty)
    if sample_key not in state["samples"]:
        # Explicitly no custom overrides: the production schedule is the claim.
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        input_hash = _grid_hash(grid)
        if input_hash not in state["cache"]:
            expected = _GEOMETRY._expected_output(grid)
            state["cache"][input_hash] = {
                "input": grid, "input_sha256": input_hash, "output": expected,
                "output_sha256": _grid_hash(expected),
                "mirror": _predict(GEN.rule_mirror, grid),
                "rivals": {name: _predict(solve, grid) for name, solve in state["rivals"].items()},
            }
        state["samples"][sample_key] = {
            **state["cache"][input_hash], "seed": seed, "sample_index": sample_index,
            "difficulty": difficulty, "profile": GEN.schedule_profile(seed, sample_index, difficulty),
        }
    return state["samples"][sample_key]


def _preserve_first_failure(state, lesson, query_position, rival, *, label_basis, authority=None):
    kind = "canonical-racket" if authority is not None else "python-screen"
    identity = (kind, rival)
    if identity in state["first_failures"]:
        return state["first_failures"][identity]
    rival_suffix = hashlib.sha256(rival.encode()).hexdigest()[:12]
    path = state["evidence_dir"] / f"first-{kind}-{SOURCE_SHA256[:12]}-{rival_suffix}.json"
    query = lesson[query_position]
    receipt = {
        "schema": "frame-lesson-counterexample-v1", "task_id": TASK_ID,
        "generator_sha256": SOURCE_SHA256,
        "source_unchanged_at_capture": hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256,
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": DEFAULT_SCOPE, "overrides": {}, "label_basis": label_basis,
        "reference_identity": authority, "seed": query["seed"], "difficulty": query["difficulty"],
        "start": lesson[0]["sample_index"], "query_position": query_position,
        "query_sample_index": query["sample_index"], "query_profile": query["profile"],
        "query_kind": "production" if query_position == 5 else "rotated",
        "demonstration_positions": [position for position in range(6) if position != query_position],
        "rival": rival,
        "pairs": [{"sample_index": pair["sample_index"], "profile": pair["profile"],
                   "input": pair["input"], "output": pair["output"],
                   "input_sha256": pair["input_sha256"], "output_sha256": _grid_hash(pair["output"]),
                   "rival_output": pair["rivals"][rival]["output"]}
                  for pair in lesson],
    }
    if not path.exists():
        _write_json(path, receipt)
    state["first_failures"][identity] = str(path)
    return str(path)


def _ambiguities(state, lesson, *, label_basis, authority=None):
    failures = []
    for query_position in range(6):
        demo_positions = [position for position in range(6) if position != query_position]
        for name in state["rivals"]:
            if any(pair["rivals"][name]["error"] is not None for pair in lesson):
                continue  # Prediction errors are separately reported as test failures.
            if (all(lesson[position]["rivals"][name]["output"] == lesson[position]["output"]
                    for position in demo_positions)
                    and lesson[query_position]["rivals"][name]["output"] != lesson[query_position]["output"]):
                path = _preserve_first_failure(state, lesson, query_position, name,
                                               label_basis=label_basis, authority=authority)
                failures.append({"rival": name, "start": lesson[0]["sample_index"],
                                 "query_position": query_position,
                                 "query_sample_index": lesson[query_position]["sample_index"],
                                 "query_profile": lesson[query_position]["profile"],
                                 "query_kind": "production" if query_position == 5 else "rotated",
                                 "receipt": path})
    return failures


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(16))
def test_default_cyclic_windows_and_query_holdouts_python_screen(screen_state, seed, difficulty):
    state = screen_state
    samples = [_sample(state, seed, index, difficulty) for index in range(11)]
    result = {"seed": seed, "difficulty": difficulty, "prediction_errors": [],
              "mirror_mismatches": [], "ambiguities": []}
    for pair in samples:
        if pair["mirror"]["error"] is not None:
            result["prediction_errors"].append({"sample_index": pair["sample_index"],
                                                "predictor": "rule_mirror", "error": pair["mirror"]["error"]})
        elif pair["mirror"]["output"] != pair["output"]:
            result["mirror_mismatches"].append(pair["sample_index"])
        for name, prediction in pair["rivals"].items():
            if prediction["error"] is not None:
                result["prediction_errors"].append({"sample_index": pair["sample_index"],
                                                    "predictor": name, "error": prediction["error"]})
    # Complete every window and every holdout before asserting, preserving the
    # real coverage and the first six-pair witness for each failing live rival.
    for start in range(6):
        result["ambiguities"].extend(_ambiguities(state, samples[start:start + 6],
                                                 label_basis=PYTHON_LABEL_BASIS))
    state["screens"].append(result)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256, "Generator changed during screening"
    assert not result["prediction_errors"], result["prediction_errors"]
    assert not result["mirror_mismatches"], result["mirror_mismatches"]
    assert not result["ambiguities"], result["ambiguities"]


def test_canonical_racket_labels_for_one_complete_period_per_band(screen_state):
    racket = os.environ.get("RACKET_PATH")
    if not racket:
        pytest.skip("Canonical Racket check requires RACKET_PATH from the caller's run_with_racket.py wrapper")
    racket_path = Path(racket)
    assert racket_path.is_absolute() and racket_path.is_file() and os.access(racket_path, os.X_OK), \
        "RACKET_PATH must identify the caller-configured local executable"
    from arcpuzzles import Catalog

    state = screen_state
    samples = [_sample(state, 0, index, band) for band in BANDS for index in range(6)]
    catalog = Catalog(find_root(__file__))
    assert catalog.describe(TASK_ID)["generator_sha256"] == SOURCE_SHA256
    applied = catalog.apply(TASK_ID, [pair["input"] for pair in samples], reference="canonical", timeout=180)
    source_unchanged = hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    authority = {key: applied[key] for key in (
        "reference", "executed_rule_hash", "catalog_rule_hash", "rule_hash_matches_catalog",
        "rule_text_sha256", "generator_sha256",
    )}
    path = state["evidence_dir"] / f"canonical-racket-{SOURCE_SHA256[:12]}.json"
    receipt = {
        "schema": "frame-lesson-canonical-racket-v1", "task_id": TASK_ID,
        "scope": DEFAULT_SCOPE, "overrides": {}, "seed": 0,
        "racket_path": str(racket_path), "source_unchanged_through_run": source_unchanged,
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sample_identities": [{"seed": pair["seed"], "difficulty": pair["difficulty"],
                               "sample_index": pair["sample_index"], "profile": pair["profile"]}
                              for pair in samples],
        "reference_receipt": applied,
    }
    _write_json(path, receipt)
    state["reference_receipt"] = str(path)
    assert source_unchanged, "Generator changed during canonical reference execution"
    assert applied["generator_sha256"] == SOURCE_SHA256
    assert applied["rule_hash_matches_catalog"] is True
    assert len(applied["results"]) == len(samples) == 18
    authoritative_samples = []
    for pair, result in zip(samples, applied["results"], strict=True):
        assert result["error"] is None, result
        assert result["valid_output"] is True, result
        assert result["input_sha256"] == pair["input_sha256"]
        assert result["output"] == pair["output"], (pair["difficulty"], pair["sample_index"])
        assert pair["mirror"]["error"] is None
        assert result["output"] == pair["mirror"]["output"]
        assert all(prediction["error"] is None for prediction in pair["rivals"].values())
        authoritative_samples.append({**pair, "output": result["output"]})
    failures = []
    for offset in range(0, 18, 6):
        failures.extend(_ambiguities(state, authoritative_samples[offset:offset + 6],
                                     label_basis="Canonical Racket labels obtained through public Catalog.apply.",
                                     authority=authority))
    receipt["independent_oracle_matches"] = 18
    receipt["diagnostic_mirror_matches"] = 18
    receipt["authoritative_query_holdouts"] = 18
    receipt["authoritative_ambiguities"] = failures
    _write_json(path, receipt)
    assert not failures, failures

#!/usr/bin/env python3
"""Bounded replay of the pinned ad6ae79cd803 rotation-warning audit."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

REPO = Path.cwd().resolve()
sys.path.insert(0, str(REPO / "shared" / "runtime"))
TASK = REPO / "generators" / "ad6ae79cd803"
RETURN_ID = "review-6ee2aa2a9f0ff225:v0001"
EXPECTED = {
    "generator": "f6abdb2cced1dca3690697c622e3f61dad7e97ff45854e09cc15d66ddfa8b920",
    "assets": "95ee6ba57f629b9d3e7bfb7c206214a7204b9441e81ba104939e5f75bfa94f6f",
    "index": "72575ec62be9797f7f32af82dac675712f6a34258d9f4dd4ef873819b0615eca",
    "record": "3665ddf99fc2d6b61389b8e1a622af1838fbdb0fb7a74042445b43d53b50aaf4",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_replay_ad6ae79cd803", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def output_for(generator: Any, grid: list[list[int]]) -> list[list[int]]:
    code = generator._corner_code(grid)
    assert code is not None
    return generator._rotate_grid(generator._crop_without_marker(grid), code)


def main() -> None:
    source = TASK / "generator.py"
    assets_path = TASK / "counterexamples" / "review-6ee2aa2a9f0ff225-v0001" / "audit_assets.json"
    index_path = TASK / "evidence" / "review_index.json"
    retained_path = (
        TASK / "counterexamples" / "review-6ee2aa2a9f0ff225-v0001" / "retained" /
        "checks" / "audit" / "ad6ae79cd803-rotation-required.json"
    )

    assert sha(source) == EXPECTED["generator"]
    assert sha(assets_path) == EXPECTED["assets"]
    assert sha(index_path) == EXPECTED["index"]

    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    assert assets["return_id"] == RETURN_ID
    assert assets["audited_generator_sha256"] == EXPECTED["generator"]
    verified_assets = []
    for row in assets["files"]:
        path = REPO / row["path"]
        assert path.is_file()
        assert path.stat().st_size == row["bytes"]
        assert sha(path) == row["sha256"]
        verified_assets.append(row["path"])

    index = json.loads(index_path.read_text(encoding="utf-8"))
    records = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(records) == 1
    record = records[0]
    assert canonical_hash(record) == EXPECTED["record"]
    assert record["source_sha256"] == EXPECTED["generator"]
    assert record["resolution"] == "needs_triage"

    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    assert retained["generator_sha256"] == EXPECTED["generator"]
    assert retained["declared_rule_hash"] == "6b203391dc52"
    assert retained["summary"]["rotations"] == 15
    assert retained["summary"]["rotation_hook_warnings"] == 9
    assert retained["summary"]["hook_warnings"] == 0

    generator = load_module(source)
    band_rows = {}
    total_rotation_warnings = 0
    total_rotations = 0
    for lesson in retained["lessons"]:
        band = lesson["band"]
        seed = lesson["seed"]
        pairs = []
        for sample_index in range(5):
            grid = generator.generate(seed, sample_index, difficulty=band)
            assert generator.self_check(grid, difficulty=band) == []
            pairs.append({"input": grid, "output": output_for(generator, grid)})

        pinned_pairs = [*lesson["instance"]["train"], *lesson["instance"]["test"]]
        assert pairs == pinned_pairs, f"{band}: regenerated lesson differs from retained witness"
        corners = [generator._corner_code(pair["input"]) for pair in pairs]
        assert corners == [0, 1, 2, 3, 0]
        assert generator.lesson_identifiable(pairs[:4], pairs[4]) == []

        warned = []
        reasons_by_holdout = {}
        for query_index in range(5):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            reasons = generator.lesson_identifiable(demos, pairs[query_index])
            reasons_by_holdout[str(query_index)] = reasons
            if reasons:
                warned.append(query_index)
        assert warned == [1, 2, 3]
        total_rotation_warnings += len(warned)
        total_rotations += 5
        band_rows[band] = {
            "seed": seed,
            "corner_sequence": corners,
            "production_order_identifiable": True,
            "query_corner_repeats_demo0": True,
            "warned_holdouts": warned,
            "reasons_by_holdout": reasons_by_holdout,
            "retained_instance_exactly_regenerated": True,
        }

    assert total_rotation_warnings == 9
    assert total_rotations == 15
    result = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "status": "reproduced",
        "ticket_id": "ticket-16a62c09f4d34023",
        "task_id": "ad6ae79cd803",
        "return_id": RETURN_ID,
        "identity": {
            "generator_sha256": EXPECTED["generator"],
            "assets_manifest_sha256": EXPECTED["assets"],
            "audit_index_sha256": EXPECTED["index"],
            "audit_record_sha256": EXPECTED["record"],
            "retained_assets_verified": len(verified_assets),
        },
        "replay": {
            "lessons": 3,
            "rotations": total_rotations,
            "rotation_hook_warnings": total_rotation_warnings,
            "production_hook_warnings": 0,
            "warned_holdouts_per_lesson": [1, 2, 3],
            "fixed_position_shortcut_reproduced": True,
            "bands": band_rows,
        },
        "scope": "Exact three-lesson retained required-policy witness only; audit remains needs_triage.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

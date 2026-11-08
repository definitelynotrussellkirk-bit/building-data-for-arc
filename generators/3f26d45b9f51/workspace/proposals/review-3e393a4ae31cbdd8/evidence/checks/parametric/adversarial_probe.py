#!/usr/bin/env python3
"""Independent audit of one axis-mode evidence directory."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "3f26d45b9f51"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("axis_mode_probe_target", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(evidence: Path) -> dict:
    prototype = load_prototype()
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    report = read_json(evidence / "report.json")
    manifest = read_json(evidence / "manifest.json")

    manifest_files = 0
    for item in manifest["files"]:
        path = evidence / item["path"]
        if not path.is_file():
            raise ValueError(f"manifest path missing: {item['path']}")
        if path.stat().st_size != item["size_bytes"]:
            raise ValueError(f"manifest size mismatch: {item['path']}")
        if sha256(path.read_bytes()) != item["sha256"]:
            raise ValueError(f"manifest hash mismatch: {item['path']}")
        manifest_files += 1

    public_ids = [row["public_id"] for row in report["episodes"]]
    if public_ids != sorted(public_ids) or len(public_ids) != len(set(public_ids)):
        raise ValueError("public batch IDs must be unique and sorted")

    racket_labels = 0
    python_parity = 0
    rival_demo_comparisons = 0
    rival_query_comparisons = 0
    private_projection_checks = 0
    input_hashes_by_episode = []

    flags = {
        "both_axes": (True, True),
        "horizontal_only": (True, False),
        "vertical_only": (False, True),
    }
    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        for row in report["episodes"]:
            private_path = evidence / row["private_path"]
            public_path = evidence / row["public_path"]
            rule_path = evidence / row["rule_path"]
            private = read_json(private_path)
            public = read_json(public_path)
            mode = private["parameters"]["axis_mode"]
            if mode != row["axis_mode"] or mode not in flags:
                raise ValueError("episode setting mismatch")

            rule_raw = rule_path.read_bytes()
            if rule_raw.decode("utf-8") != private["program"]:
                raise ValueError("private rule text mismatch")
            if sha256(rule_raw) != private["program_sha256"]:
                raise ValueError("private rule hash mismatch")

            expected_public_raw = public_challenge_bytes(public)
            if public_path.read_bytes() != expected_public_raw:
                raise ValueError("public file is not exact canonical visible bytes")
            if public_challenge_id(public) != row["public_id"]:
                raise ValueError("public filename/ID mismatch")
            if public != prototype.public_challenge(private):
                raise ValueError("public projection mismatch")
            private_projection_checks += 1

            tampered_private = copy.deepcopy(private)
            tampered_private["seed"] += 1
            tampered_private["parameters"]["axis_mode"] = "hidden-change"
            tampered_private["program"] = "hidden-change"
            tampered_private["test"][0]["output"][0][0] = (
                tampered_private["test"][0]["output"][0][0] + 1
            ) % 10
            if prototype.public_bytes(tampered_private) != prototype.public_bytes(private):
                raise ValueError("hidden private fields changed visible challenge bytes")

            all_pairs = private["train"] + private["test"]
            input_hashes = [prototype.grid_sha256(pair["input"]) for pair in all_pairs]
            if len(input_hashes) != len(set(input_hashes)):
                raise ValueError("episode contains duplicate inputs")
            input_hashes_by_episode.append(input_hashes)

            horizontal, vertical = flags[mode]
            for pair in all_pairs:
                racket_output = prototype.execute_rule(
                    private["program"], pair["input"], bridge=bridge
                )
                if racket_output != pair["output"]:
                    raise ValueError("stored label differs from stored Racket program")
                racket_labels += 1
                python_output = generator._solve_with_axes(
                    pair["input"], horizontal=horizontal, vertical=vertical
                )
                if python_output != pair["output"]:
                    raise ValueError("Racket label differs from independent Python axis mirror")
                python_parity += 1

            consistent = []
            for rival in prototype.AXIS_MODES:
                demo_predictions = [
                    prototype.execute_rule(
                        prototype.program_for(rival), pair["input"], bridge=bridge
                    )
                    for pair in private["train"]
                ]
                query_predictions = [
                    prototype.execute_rule(
                        prototype.program_for(rival), pair["input"], bridge=bridge
                    )
                    for pair in private["test"]
                ]
                if demo_predictions == [pair["output"] for pair in private["train"]]:
                    consistent.append(rival)
                if rival != mode:
                    rival_demo_comparisons += len(demo_predictions)
                    rival_query_comparisons += len(query_predictions)
                    if any(
                        predicted == pair["output"]
                        for predicted, pair in zip(demo_predictions, private["train"])
                    ):
                        raise ValueError("declared rival survived at least one distinguishing demo")
                    if any(
                        predicted == pair["output"]
                        for predicted, pair in zip(query_predictions, private["test"])
                    ):
                        raise ValueError("declared rival matched at least one query")
            if consistent != [mode]:
                raise ValueError(f"demonstrations leave ambiguous settings: {consistent}")

    if any(hashes != input_hashes_by_episode[0] for hashes in input_hashes_by_episode[1:]):
        raise ValueError("settings were not evaluated on the same episode inputs")

    # Exact numeric validation: bool is an int subclass in Python but is not an ARC color.
    malformed = copy.deepcopy(read_json(evidence / report["episodes"][0]["public_path"]))
    malformed["train"][0]["input"][0][0] = True
    try:
        public_challenge_bytes(malformed)
    except ValueError:
        numeric_bool_rejected = True
    else:
        raise ValueError("public encoder accepted bool as an ARC color")

    return {
        "schema": "arc-parametric-axis-mode-adversarial-probe-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "generator_source": str(generator_path.relative_to(ROOT)),
        "generator_source_sha256": generator_sha256,
        "prototype_sha256": sha256(PROTOTYPE_PATH.read_bytes()),
        "evidence": str(evidence),
        "checks": {
            "manifest_files": manifest_files,
            "episodes": len(report["episodes"]),
            "racket_labels_reexecuted": racket_labels,
            "independent_python_parity": python_parity,
            "rival_demo_comparisons": rival_demo_comparisons,
            "rival_query_comparisons": rival_query_comparisons,
            "private_projection_checks": private_projection_checks,
            "numeric_bool_rejected": numeric_bool_rejected,
            "public_ids_sorted_unique": True,
            "same_inputs_across_settings": True,
        },
        "bounded_findings": [
            "No Racket/Python parity mismatch across 21 stored labels.",
            "No hidden-field influence on visible bytes across all three episodes.",
            "Exact public numeric validation rejected bool; all public IDs were unique and sorted.",
        ],
        "limits": [
            "Finite audit of the three declared settings and the seed-31 evidence bundle only.",
            "Independent Python mirror shares the production generator's lattice parser, so parser-correlated faults remain possible.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.evidence.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

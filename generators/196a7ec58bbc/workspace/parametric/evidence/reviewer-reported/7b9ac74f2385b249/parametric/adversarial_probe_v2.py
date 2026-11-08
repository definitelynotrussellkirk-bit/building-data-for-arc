from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import tempfile

REPO = Path.cwd()
SOURCE = REPO / "generators/196a7ec58bbc/workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("adversarial_parametric_196a7ec58bbc", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not import {SOURCE}")
PROTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTO)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    failures: list[str] = []
    sampler_cases = []

    count_cases = ((1, 1), (3, 4), (8, 8), (63, 1))
    for setting_index, setting in enumerate(PROTO.SETTINGS):
        for case_index, (demos, queries) in enumerate(count_cases):
            seed = 100 + setting_index * 10 + case_index
            try:
                episode = PROTO.generate_episode(
                    seed,
                    handedness=setting,
                    demonstration_count=demos,
                    query_count=queries,
                )
            except Exception as error:  # evidence retains the exact bounded failure
                failures.append(f"{setting}/{demos}/{queries}: {error!r}")
                continue
            pairs = episode["train"] + episode["test"]
            hashes = [PROTO.grid_hash(pair["input"]) for pair in pairs]
            rival = next(value for value in PROTO.SETTINGS if value != setting)
            okay = (
                len(episode["train"]) == demos
                and len(episode["test"]) == queries
                and len(hashes) == len(set(hashes))
                and all(
                    pair["output"] == PROTO.solve(pair["input"], handedness=setting)
                    and pair["output"] != PROTO.solve(pair["input"], handedness=rival)
                    for pair in pairs
                )
            )
            if not okay:
                failures.append(f"{setting}/{demos}/{queries}: contract mismatch")
            sampler_cases.append(
                {
                    "setting": setting,
                    "seed": seed,
                    "demonstrations": demos,
                    "queries": queries,
                    "unique_inputs": len(set(hashes)),
                    "candidate_attempts": episode["meta"]["candidate_attempts"],
                    "passed": okay,
                }
            )

    invalid_rows = []
    invalid_calls = (
        {"demonstration_count": 0},
        {"query_count": 0},
        {"demonstration_count": True},
        {"query_count": 1.0},
        {"demonstration_count": 64, "query_count": 1},
    )
    for kwargs in invalid_calls:
        try:
            PROTO.generate_episode(0, **kwargs)
        except ValueError as error:
            invalid_rows.append({"kwargs": repr(kwargs), "rejected": True, "error": str(error)})
        else:
            invalid_rows.append({"kwargs": repr(kwargs), "rejected": False})
            failures.append(f"invalid count request accepted: {kwargs!r}")

    first = PROTO.generate_episode(301, handedness="clockwise", query_count=4)
    second = PROTO.generate_episode(302, handedness="counterclockwise", query_count=4)
    private_variant = deepcopy(first)
    private_variant["parameters"] = {"handedness": "counterclockwise"}
    private_variant["program"] = "private replacement"
    private_variant["meta"] = {"seed": 999, "private": True}
    for pair in private_variant["test"]:
        pair["output"] = [[9]]
    private_invariant = (
        PROTO.public_id(private_variant) == PROTO.public_id(first)
        and PROTO.public_bytes(private_variant) == PROTO.public_bytes(first)
    )
    if not private_invariant:
        failures.append("private mutation changed public identity")

    visible_demo_variant = deepcopy(first)
    value = visible_demo_variant["train"][0]["output"][0][0]
    visible_demo_variant["train"][0]["output"][0][0] = (value + 1) % 10
    visible_query_variant = deepcopy(first)
    value = visible_query_variant["test"][0]["input"][0][0]
    visible_query_variant["test"][0]["input"][0][0] = (value + 1) % 10
    visible_sensitive = (
        PROTO.public_id(visible_demo_variant) != PROTO.public_id(first)
        and PROTO.public_id(visible_query_variant) != PROTO.public_id(first)
    )
    if not visible_sensitive:
        failures.append("visible mutation did not change public identity")

    with tempfile.TemporaryDirectory() as left_name, tempfile.TemporaryDirectory() as right_name:
        left = PROTO.write_public_batch([first, second], Path(left_name))
        right = PROTO.write_public_batch([second, first], Path(right_name))
        left_projection = [
            (row["public_id"], Path(row["path"]).name, row["public_bytes"])
            for row in left
        ]
        right_projection = [
            (row["public_id"], Path(row["path"]).name, row["public_bytes"])
            for row in right
        ]
        order_independent = left_projection == right_projection
        opaque_names = all(
            re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)
            and "clockwise" not in name
            and "counterclockwise" not in name
            for _, name, _ in left_projection
        )
        if not order_independent:
            failures.append("batch output depends on setting iteration order")
        if not opaque_names:
            failures.append("public filenames are not opaque visible-content IDs")
        try:
            PROTO.write_public_batch([first, deepcopy(first)], Path(left_name))
        except ValueError as error:
            duplicate_rejected = "duplicate public payload" in str(error)
        else:
            duplicate_rejected = False
        if not duplicate_rejected:
            failures.append("duplicate visible payload was not rejected")

    report = {
        "task_id": PROTO.TASK_ID,
        "source_path": str(SOURCE.relative_to(REPO)),
        "surface_1_sampler_count_boundaries": {
            "cases": sampler_cases,
            "invalid_requests": invalid_rows,
        },
        "surface_2_public_private_identity": {
            "private_mutation_invariant": private_invariant,
            "visible_mutations_change_identity": visible_sensitive,
            "batch_order_independent": order_independent,
            "opaque_names": opaque_names,
            "duplicate_visible_payload_rejected": duplicate_rejected,
        },
        "failures": failures,
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

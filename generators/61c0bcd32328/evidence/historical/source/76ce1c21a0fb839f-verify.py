#!/usr/bin/env python3
"""Materialize and exact-Racket-verify the corner-direction prototype.

This verifier also retains one bounded singleton-corner lesson proving the
production sampler repair reaches behavior that the historical ignore-singleton
rival did not teach.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        ROOT = ancestor
        for path in (runtime, ancestor / "src"):
            if path.is_dir() and str(path) not in sys.path:
                sys.path.insert(0, str(path))
        break
else:  # pragma: no cover - a source-bound verifier cannot operate without a root
    raise RuntimeError("could not locate the task source tree")

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402
from reviewer_support import canonical_pairs, public_challenge_bytes  # noqa: E402

REPORT_SCHEMA = "61c0bcd32328-parametric-corner-direction-v1"
EPISODE_SEED = 17


def _load_prototype():
    path = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_61c0bcd32328", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def _relative(path: Path) -> str:
    path = path.resolve()
    if path.is_relative_to(ROOT):
        return str(path.relative_to(ROOT))
    return str(path)


def portable_runtime_identity(identity: dict[str, Any]) -> dict[str, Any]:
    """Remove checkout-specific absolute paths while preserving runtime hashes."""
    portable = deepcopy(identity)
    root = ROOT.resolve()
    for key, value in tuple(portable.items()):
        if not key.endswith("_path") or not isinstance(value, str):
            continue
        path = Path(value)
        if not path.is_absolute():
            portable[key] = path.as_posix()
            continue
        resolved = path.resolve()
        if resolved.is_relative_to(root):
            portable[key] = resolved.relative_to(root).as_posix()
        else:
            portable[key] = resolved.name
    return portable


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _racket_apply_many(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
) -> list[list[list[int]]]:
    body = _program_body(program)
    outputs = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def _public_is_masked(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def _private_mutation_preserves_public_id(proto, episode: dict[str, Any]) -> bool:
    changed = deepcopy(episode)
    changed["parameters"]["direction"] = (
        "counterclockwise"
        if episode["parameters"]["direction"] == "clockwise"
        else "clockwise"
    )
    changed["program"] = "private replacement"
    changed["meta"]["seed"] = 999999
    changed["test"][0]["output"] = [[9]]
    return proto.public_id(changed) == proto.public_id(episode)


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row, (left_row, right_row) in enumerate(zip(left, right, strict=True))
        for col, (left_value, right_value) in enumerate(
            zip(left_row, right_row, strict=True)
        )
        if left_value != right_value
    ]


def _ignore_singleton_rival(proto, grid: list[list[int]]) -> list[list[int]]:
    """Historical rival: copy corner objects except one-cell components."""
    normalized = proto._validate_grid(grid)
    height, width = len(normalized), len(normalized[0])
    output = deepcopy(normalized)
    background = proto._background(normalized)
    for component in proto._components(normalized, background):
        if len(component["cells"]) == 1:
            continue
        corner = proto._corner(component, height, width)
        if corner is None:
            continue
        delta_row, delta_col = proto._translation(
            corner, component["bbox"], height, width, "clockwise"
        )
        for row, col in component["cells"]:
            new_row, new_col = row + delta_row, col + delta_col
            if 0 <= new_row < height and 0 <= new_col < width:
                output[new_row][new_col] = component["color"]
    return output


def _singleton_repair_report(proto, bridge: RacketBridge, evidence_dir: Path):
    generator, source_path, source_sha256 = proto.selected_generator()
    witness = None
    witness_seed = None
    witness_part = None
    for seed in range(128):
        grid = generator.generate(
            seed,
            seed * 19 + 5,
            difficulty="easy",
            scene_profile="single_tl",
        )
        info = generator._analysis(grid)
        singleton = next(
            (
                part
                for corner, part in info["corner_parts"]
                if corner == "tl" and len(part["cells"]) == 1
            ),
            None,
        )
        if singleton is not None:
            witness = grid
            witness_seed = seed
            witness_part = singleton
            break
    if witness is None or witness_seed is None or witness_part is None:
        raise AssertionError("bounded sampler sweep found no singleton corner lesson")

    program = proto.program_for("clockwise")
    racket_output = _racket_apply_many(bridge, program, [witness])[0]
    mirror_output = generator.rule_mirror(witness)
    rival_output = _ignore_singleton_rival(proto, witness)
    differing_cells = _diff_cells(racket_output, rival_output)
    payload = {
        "schema": "61c0bcd32328-singleton-corner-repair-v1",
        "task_id": proto.TASK_ID,
        "seed": witness_seed,
        "sample_index": witness_seed * 19 + 5,
        "difficulty": "easy",
        "scene_profile": "single_tl",
        "singleton_cells": [list(cell) for cell in sorted(witness_part["cells"])],
        "generator_path": _relative(Path(source_path)),
        "generator_sha256": source_sha256,
        "canonical_program_sha256": proto.exact_program_hash("clockwise"),
        "input": witness,
        "racket_output": racket_output,
        "production_mirror_output": mirror_output,
        "ignore_singleton_rival_output": rival_output,
        "self_check": generator.self_check(witness),
        "racket_matches_production_mirror": racket_output == mirror_output,
        "ignore_singleton_rival_refuted": racket_output != rival_output,
        "differing_cells": differing_cells,
        "input_sha256": _sha_json(witness),
        "racket_output_sha256": _sha_json(racket_output),
        "rival_output_sha256": _sha_json(rival_output),
    }
    path = evidence_dir / "singleton-corner-repair.json"
    _write_json(path, payload)
    return {
        **{key: value for key, value in payload.items() if key not in {
            "input", "racket_output", "production_mirror_output",
            "ignore_singleton_rival_output"
        }},
        "evidence_path": _relative(path),
        "evidence_sha256": _sha_bytes(path.read_bytes()),
    }


def build_report() -> dict[str, Any]:
    proto = _load_prototype()
    base = HERE.parent
    programs_dir = base / "programs"
    private_dir = base / "episodes" / "private"
    public_dir = base / "episodes" / "public"
    evidence_dir = base / "evidence"
    for directory in (programs_dir, private_dir, public_dir, evidence_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rows = []
    public_ids: set[str] = set()
    input_hashes_by_setting: dict[str, list[str]] = {}
    canonical = canonical_pairs(proto.TASK_ID, root=ROOT)

    with RacketBridge(max_calls_before_restart=128) as bridge:
        canonical_observed = _racket_apply_many(
            bridge,
            proto.program_for("clockwise"),
            [pair["input"] for pair in canonical],
        )
        canonical_exact = [
            got == pair["output"]
            for got, pair in zip(canonical_observed, canonical, strict=True)
        ]

        for setting in proto.SETTINGS:
            episode = proto.generate_episode(
                EPISODE_SEED,
                direction=setting,
                n_train=3,
                n_test=4,
            )
            public = proto.public_challenge(episode)
            public_id = proto.public_id(episode)
            if public_id in public_ids:
                raise ValueError("duplicate visible public challenge payload")
            public_ids.add(public_id)
            program = proto.program_for(setting)
            rival = next(value for value in proto.SETTINGS if value != setting)
            rival_program = proto.program_for(rival)

            program_path = programs_dir / f"{setting}.rkt"
            private_path = private_dir / f"{setting}-complete.json"
            public_path = public_dir / proto.public_filename(episode)
            program_path.write_text(program, encoding="utf-8")
            _write_json(private_path, episode)
            public_path.write_bytes(public_challenge_bytes(public))

            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            inputs = [pair["input"] for _, _, pair in pairs]
            intended_racket = _racket_apply_many(bridge, program, inputs)
            rival_racket = _racket_apply_many(bridge, rival_program, inputs)
            pair_rows = []
            input_hashes_by_setting[setting] = []
            for (split, index, pair), got, rival_got in zip(
                pairs, intended_racket, rival_racket, strict=True
            ):
                rival_python = proto.solve(pair["input"], direction=rival)
                input_sha256 = _sha_json(pair["input"])
                input_hashes_by_setting[setting].append(input_sha256)
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": input_sha256,
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(got),
                        "racket_matches_stored": got == pair["output"],
                        "rival": rival,
                        "rival_racket_matches_python": rival_got == rival_python,
                        "rival_differs_from_intended": rival_got != pair["output"],
                        "rival_output_sha256": _sha_json(rival_got),
                        "differing_cells": _diff_cells(pair["output"], rival_got),
                    }
                )

            row = {
                "setting": setting,
                "seed": EPISODE_SEED,
                "counts": {"demonstrations": 3, "queries": 4},
                "program_path": _relative(program_path),
                "program_sha256": _sha_bytes(program_path.read_bytes()),
                "normalized_program_sha256": proto.normalized_program_hash(setting),
                "private_episode_path": _relative(private_path),
                "private_episode_sha256": _sha_bytes(private_path.read_bytes()),
                "public_id": public_id,
                "public_episode_path": _relative(public_path),
                "public_episode_sha256": _sha_bytes(public_path.read_bytes()),
                "public_bytes_match_helper": public_path.read_bytes()
                == proto.public_bytes(episode),
                "public_answer_masked": _public_is_masked(public),
                "private_mutation_preserves_public_id": (
                    _private_mutation_preserves_public_id(proto, episode)
                ),
                "pairs": pair_rows,
                "all_racket_exact": all(
                    item["racket_matches_stored"] for item in pair_rows
                ),
                "rival_racket_python_exact": all(
                    item["rival_racket_matches_python"] for item in pair_rows
                ),
                "rival_refuted_by_every_demo": all(
                    item["rival_differs_from_intended"]
                    for item in pair_rows
                    if item["split"] == "train"
                ),
                "all_queries_setting_sensitive": all(
                    item["rival_differs_from_intended"]
                    for item in pair_rows
                    if item["split"] == "test"
                ),
                "distinct_input_count": len(
                    {item["input_sha256"] for item in pair_rows}
                ),
            }
            rows.append(row)

        singleton = _singleton_repair_report(proto, bridge, evidence_dir)
        runtime_identity = portable_runtime_identity(bridge.runtime_identity)

    source_paths = [
        ROOT / "generators" / proto.TASK_ID / "generator.py",
        HERE.with_name("prototype.py"),
        HERE,
    ]
    shared_inputs = (
        input_hashes_by_setting["clockwise"]
        == input_hashes_by_setting["counterclockwise"]
    )
    report = {
        "schema": REPORT_SCHEMA,
        "status": "proposed_prototype_not_selected",
        "task_id": proto.TASK_ID,
        "runtime_identity": runtime_identity,
        "parameter": {
            "name": "direction",
            "allowed_values": list(proto.ALLOWED_DIRECTIONS),
            "original_default": proto.DEFAULT_DIRECTION,
            "selection_scope": "once per complete episode",
            "input_constraint": (
                "one declared single-corner profile per retained input; the two "
                "directions must produce different outputs"
            ),
        },
        "episode_seed": EPISODE_SEED,
        "settings": rows,
        "canonical_default": {
            "exact_source_sha256": proto.exact_program_hash("clockwise"),
            "normalized_source_sha256": proto.normalized_program_hash("clockwise"),
            "expected_normalized_source_sha256": proto.CANONICAL_NORMALIZED_SHA256,
            "pair_count": len(canonical),
            "pair_results": canonical_exact,
            "all_racket_exact": all(canonical_exact),
        },
        "singleton_repair": singleton,
        "source_hashes": {
            _relative(path): _sha_bytes(path.read_bytes()) for path in source_paths
        },
        "all_racket_exact": all(row["all_racket_exact"] for row in rows),
        "all_rival_racket_python_exact": all(
            row["rival_racket_python_exact"] for row in rows
        ),
        "all_rivals_refuted_by_every_demo": all(
            row["rival_refuted_by_every_demo"] for row in rows
        ),
        "all_queries_setting_sensitive": all(
            row["all_queries_setting_sensitive"] for row in rows
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in rows
        ),
        "all_public_bytes_match_helper": all(
            row["public_bytes_match_helper"] for row in rows
        ),
        "all_public_ids_private_invariant": all(
            row["private_mutation_preserves_public_id"] for row in rows
        ),
        "distinct_public_ids": len(public_ids) == len(rows),
        "inputs_shared_across_settings": shared_inputs,
        "shared_distinct_input_count": len(set(input_hashes_by_setting["clockwise"])),
        "singleton_repair_racket_exact": singleton[
            "racket_matches_production_mirror"
        ],
        "singleton_ignore_rival_refuted": singleton[
            "ignore_singleton_rival_refuted"
        ],
        "limitations": [
            "This is a task-local proposal; the selected catalog remains clockwise.",
            "Evidence covers one retained seven-input episode reused for both settings, not all seeds.",
            "The bounded singleton sweep covers seeds 0..127 for single_tl/easy only.",
            "Only adjacent-corner direction varies; component extraction, preservation, and painting order stay canonical.",
        ],
        "replay": {
            "cwd": "WORK/repo",
            "argv": [
                "python3",
                "generators/61c0bcd32328/workspace/parametric/verify.py",
                "--out",
                "../checks/parametric/61c0bcd32328-direction.json",
            ],
        },
    }
    manifest_path = evidence_dir / "manifest.json"
    _write_json(manifest_path, report)
    return report


def _report_passes(report: dict[str, Any]) -> bool:
    return all(
        (
            report["canonical_default"]["all_racket_exact"],
            report["all_racket_exact"],
            report["all_rival_racket_python_exact"],
            report["all_rivals_refuted_by_every_demo"],
            report["all_queries_setting_sensitive"],
            report["all_public_challenges_masked"],
            report["all_public_bytes_match_helper"],
            report["all_public_ids_private_invariant"],
            report["distinct_public_ids"],
            report["inputs_shared_across_settings"],
            report["shared_distinct_input_count"] == 7,
            report["singleton_repair_racket_exact"],
            report["singleton_ignore_rival_refuted"],
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if _report_passes(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())

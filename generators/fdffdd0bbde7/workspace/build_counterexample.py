"""Build the source-bound current-shortcut witness for fdffdd0bbde7."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
ROOT = TASK_DIR.parents[1]
sys.path.insert(0, str(HERE))

from reference_probe import (  # noqa: E402
    canonical_pairs,
    center_col_anchor_output,
    center_row_anchor_output,
    geometry_output,
    grid_sha256,
    isolated_anchor_witness,
    load_generator,
    observed,
    panel_center_output,
    racket_outputs,
)

TASK = "fdffdd0bbde7"
WITNESS = {"seed": 120254, "sample_index": 4833, "difficulty": None, "overrides": {}}
DEFAULT_ARTIFACT = TASK_DIR / "counterexamples/current-shortcut/checks/panel-center-anchor.json"
DEFAULT_MANIFEST = TASK_DIR / "counterexamples/current-shortcut.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_differences(left, right):
    return [
        {"row": row, "col": col, "intended": left[row][col], "rival": right[row][col]}
        for row in range(len(left))
        for col in range(len(left[row]))
        if left[row][col] != right[row][col]
    ]


def build_payload(*, use_racket: bool = True):
    module = load_generator()
    source_path = Path(module.__file__).resolve()
    source_hash = sha256_bytes(source_path.read_bytes())

    rival_functions = {
        "panel_center_anchor": panel_center_output,
        "center_row_anchor": center_row_anchor_output,
        "center_col_anchor": center_col_anchor_output,
    }
    canonical = []
    for index, pair in enumerate(canonical_pairs()):
        rival_outputs = {name: fn(pair["input"]) for name, fn in rival_functions.items()}
        canonical.append({
            "pair_index": index,
            "input_sha256": grid_sha256(pair["input"]),
            "output_sha256": grid_sha256(pair["output"]),
            "rival_output_sha256": {
                name: grid_sha256(output) for name, output in rival_outputs.items()
            },
            "rival_matches": {
                name: output == pair["output"] for name, output in rival_outputs.items()
            },
        })
    if not canonical or not all(
        all(item["rival_matches"].values()) for item in canonical
    ):
        raise RuntimeError("an anchor shortcut no longer fits every canonical pair")

    witness = module.generate(
        WITNESS["seed"], WITNESS["sample_index"],
        difficulty=WITNESS["difficulty"], **WITNESS["overrides"],
    )
    issues = module.self_check(witness)
    if issues:
        raise RuntimeError(f"generated witness failed self_check: {issues}")
    if not isolated_anchor_witness(witness):
        raise RuntimeError("generated witness is not structurally isolated")

    intended = geometry_output(witness)
    rival_outputs = {name: fn(witness) for name, fn in rival_functions.items()}
    differences = {
        name: grid_differences(intended, output)
        for name, output in rival_outputs.items()
    }
    if any(not cells for cells in differences.values()):
        raise RuntimeError("generated witness does not distinguish every anchor shortcut")

    authority = {"status": "not_requested", "checked": 0}
    if use_racket:
        actual = racket_outputs([witness])[0]
        if actual != intended:
            raise RuntimeError("independent oracle disagrees with Racket authority")
        authority = {
            "status": "passed",
            "checked": 1,
            "implementation": "canonical Racket program executed by task runtime",
            "output_sha256": grid_sha256(actual),
        }

    return {
        "schema": f"{TASK}-current-shortcut-witness-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": source_hash,
        "rule_hash": module.RULE_HASH,
        "rivals": {
            "panel_center_anchor": {
                "description": "Ignore both visible anchor coordinates and use the panel center.",
                "canonical_fit": f"{sum(item['rival_matches']['panel_center_anchor'] for item in canonical)}/{len(canonical)}",
            },
            "center_row_anchor": {
                "description": "Use the visible anchor column but assume the panel-center row.",
                "canonical_fit": f"{sum(item['rival_matches']['center_row_anchor'] for item in canonical)}/{len(canonical)}",
            },
            "center_col_anchor": {
                "description": "Use the visible anchor row but assume the panel-center column.",
                "canonical_fit": f"{sum(item['rival_matches']['center_col_anchor'] for item in canonical)}/{len(canonical)}",
            },
        },
        "canonical_pairs": canonical,
        "generated_witness": {
            **WITNESS,
            "observed_axes": observed(witness),
            "validator_errors": issues,
            "isolated_anchor_witness": True,
            "input_sha256": grid_sha256(witness),
            "intended_output_sha256": grid_sha256(intended),
            "rival_output_sha256": {
                name: grid_sha256(output) for name, output in rival_outputs.items()
            },
            "differing_cells": differences,
            "input": witness,
            "intended_output": intended,
            "rival_outputs": rival_outputs,
        },
        "authority": authority,
        "reproduce": {
            "cwd": "repo",
            "command": [
                "python3", "generators/fdffdd0bbde7/workspace/build_counterexample.py"
            ],
        },
        "builder_sha256": sha256_bytes(Path(__file__).read_bytes()),
    }


def write_artifacts(artifact_path: Path, manifest_path: Path, *, use_racket: bool = True):
    payload = build_payload(use_racket=use_racket)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_bytes = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    artifact_path.write_bytes(artifact_bytes)

    relative_artifact = artifact_path.resolve().relative_to(ROOT.resolve()).as_posix()
    text = """# Current shortcut: geometric panel centers

The strongest canonical-fitting shortcut family ignores one or both coordinates
of the visible color-9 anchor and substitutes the panel-center coordinate. All
three variants match the three labeled canonical pairs. The retained generated
witness is validator-clean, makes both anchor coordinates non-central, preserves
an uncontaminated disagreement cell for every rival, and was checked against the
unchanged Racket authority. The lesson census separately checks complete
three-demonstration/one-query lessons against all declared rivals.
"""
    manifest = {
        "schema": "arcpuzzles-current-shortcut-v1",
        "task_id": TASK,
        "generator_sha256": payload["generator_sha256"],
        "text": text,
        "files": [{
            "path": relative_artifact,
            "bytes": len(artifact_bytes),
            "sha256": sha256_bytes(artifact_bytes),
        }],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return payload, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--no-racket", action="store_true",
                        help="build diagnostic evidence without claiming authority parity")
    args = parser.parse_args()
    payload, manifest = write_artifacts(
        args.artifact, args.manifest, use_racket=not args.no_racket
    )
    print(json.dumps({
        "artifact": str(args.artifact),
        "manifest": str(args.manifest),
        "generator_sha256": payload["generator_sha256"],
        "canonical_fit": {
            name: item["canonical_fit"] for name, item in payload["rivals"].items()
        },
        "differing_cells": {
            name: len(cells)
            for name, cells in payload["generated_witness"]["differing_cells"].items()
        },
        "authority": payload["authority"],
        "artifact_sha256": manifest["files"][0]["sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()

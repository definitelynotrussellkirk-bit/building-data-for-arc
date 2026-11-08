#!/usr/bin/env python3
"""Materialize and exact-Racket-verify the output-scale prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any


HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = next(
    (parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir()),
    HERE.parents[4],
)
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402
from reviewer_support import (  # noqa: E402
    canonical_pairs,
    public_challenge_bytes,
    public_challenge_id,
)


REPORT_SCHEMA = "8e6c44aee812-parametric-output-scale-v1"


def _load_prototype():
    path = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_8e6c44aee812", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


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


def _visible_only_id(proto, episode: dict[str, Any], public_id: str) -> bool:
    private_change = deepcopy(episode)
    private_change["parameters"]["output_scale"] = 99
    private_change["meta"]["seed"] = 999999
    private_change["program"] = "private replacement"
    private_change["test"][0]["output"] = [[9]]
    private_stable = (
        public_challenge_id(proto.public_challenge(private_change)) == public_id
    )

    visible_change = proto.public_challenge(episode)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    visible_sensitive = public_challenge_id(visible_change) != public_id
    return private_stable and visible_sensitive


def _clean_artifact_root(artifact_root: Path) -> None:
    artifact_root.mkdir(parents=True, exist_ok=True)
    for child in artifact_root.iterdir():
        if child.name.startswith("episode-") and child.is_dir():
            shutil.rmtree(child)
        elif child.name == "private" and child.is_dir():
            shutil.rmtree(child)


def build_report(*, artifact_root: Path) -> dict[str, Any]:
    proto = _load_prototype()
    artifact_root = Path(artifact_root).resolve()
    _clean_artifact_root(artifact_root)

    candidates = []
    for output_scale, seed in ((2, 20), (3, 21)):
        episode = proto.generate_episode(
            seed,
            output_scale=output_scale,
            demo_count=5,
            query_count=4,
            difficulty="medium",
        )
        public = proto.public_challenge(episode)
        candidates.append(
            {
                "output_scale": output_scale,
                "seed": seed,
                "episode": episode,
                "public": public,
                "public_id": public_challenge_id(public),
            }
        )

    public_ids = [item["public_id"] for item in candidates]
    if len(set(public_ids)) != len(public_ids):
        raise RuntimeError("duplicate visible public challenge IDs")
    candidates.sort(key=lambda item: item["public_id"])

    rows = []
    all_input_hashes: list[str] = []
    bridge = RacketBridge()
    try:
        canonical = list(canonical_pairs(proto.TASK_ID, root=ROOT, labeled_only=True))
        canonical_inputs = [pair["input"] for pair in canonical]
        canonical_racket = _racket_apply_many(
            bridge, proto.program_for(proto.DEFAULT_OUTPUT_SCALE), canonical_inputs
        )
        canonical_exact = all(
            got == pair["output"]
            for got, pair in zip(canonical_racket, canonical, strict=True)
        )
        distinction_input = canonical[0]["input"]
        distinction_outputs = {
            scale: _racket_apply_many(bridge, proto.program_for(scale), [distinction_input])[0]
            for scale in proto.ALLOWED_OUTPUT_SCALES
        }
        parameter_distinction = {
            "input": distinction_input,
            "input_sha256": _sha_json(distinction_input),
            "canonical_pair": {
                "variant": canonical[0]["variant"],
                "split": canonical[0]["split"],
                "pair_index": canonical[0]["pair_index"],
            },
            "scale_2": {
                "shape": [len(distinction_outputs[2]), len(distinction_outputs[2][0])],
                "output": distinction_outputs[2],
                "racket_matches_python": distinction_outputs[2]
                == proto.solve(distinction_input, output_scale=2),
            },
            "scale_3": {
                "shape": [len(distinction_outputs[3]), len(distinction_outputs[3][0])],
                "output": distinction_outputs[3],
                "racket_matches_python": distinction_outputs[3]
                == proto.solve(distinction_input, output_scale=3),
            },
            "outputs_differ": distinction_outputs[2] != distinction_outputs[3],
        }

        for item in candidates:
            output_scale = item["output_scale"]
            episode = item["episode"]
            public = item["public"]
            public_id = item["public_id"]
            program = proto.program_for(output_scale)

            episode_rel = Path(f"episode-{public_id}")
            private_dir = artifact_root / episode_rel / "private"
            public_dir = artifact_root / episode_rel / "public"
            private_dir.mkdir(parents=True, exist_ok=True)
            public_dir.mkdir(parents=True, exist_ok=True)

            program_rel = episode_rel / "private" / "program.rkt"
            private_episode_rel = episode_rel / "private" / "episode.json"
            public_challenge_rel = episode_rel / "public" / "challenge.json"
            (artifact_root / program_rel).write_text(program + "\n", encoding="utf-8")
            (artifact_root / private_episode_rel).write_text(
                json.dumps(episode, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (artifact_root / public_challenge_rel).write_bytes(
                public_challenge_bytes(public)
            )

            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            inputs = [pair["input"] for _, _, pair in pairs]
            racket_outputs = _racket_apply_many(bridge, program, inputs)
            python_outputs = [
                proto.solve(grid, output_scale=output_scale) for grid in inputs
            ]

            pair_rows = []
            for (split, index, pair), racket_output, python_output in zip(
                pairs, racket_outputs, python_outputs, strict=True
            ):
                all_input_hashes.append(_sha_json(pair["input"]))
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(racket_output),
                        "python_output_sha256": _sha_json(python_output),
                        "racket_matches_stored": racket_output == pair["output"],
                        "python_matches_stored": python_output == pair["output"],
                    }
                )

            query_checks = [
                {
                    "query_index": index,
                    "lesson_reasons": proto.lesson_identifiable(
                        episode["train"],
                        {"input": query["input"]},
                        output_scale=output_scale,
                    ),
                }
                for index, query in enumerate(episode["test"])
            ]
            row = {
                "output_scale": output_scale,
                "seed": item["seed"],
                "demo_count": len(episode["train"]),
                "query_count": len(episode["test"]),
                "public_id": public_id,
                "program_path": str(program_rel),
                "private_episode_path": str(private_episode_rel),
                "public_challenge_path": str(public_challenge_rel),
                "program_sha256": _sha_bytes((program + "\n").encode("utf-8")),
                "normalized_program_sha256": proto.normalized_program_hash(output_scale),
                "public_challenge_sha256": _sha_bytes(public_challenge_bytes(public)),
                "pairs": pair_rows,
                "query_checks": query_checks,
                "all_racket_exact": all(
                    pair["racket_matches_stored"] for pair in pair_rows
                ),
                "all_python_exact": all(
                    pair["python_matches_stored"] for pair in pair_rows
                ),
                "lesson_identifiable_for_every_query": all(
                    not check["lesson_reasons"] for check in query_checks
                ),
                "public_answer_masked": _public_is_masked(public),
                "public_id_visible_only": _visible_only_id(
                    proto, episode, public_id
                ),
            }
            rows.append(row)
    finally:
        bridge.shutdown()

    source_paths = [TASK_DIR / "generator.py", HERE.with_name("prototype.py"), HERE]
    report = {
        "schema": REPORT_SCHEMA,
        "status": "proposed_prototype_not_selected",
        "task_id": proto.TASK_ID,
        "parameter": {
            "name": "output_scale",
            "allowed_values": list(proto.ALLOWED_OUTPUT_SCALES),
            "original_default": proto.DEFAULT_OUTPUT_SCALE,
            "selection_scope": "once per complete episode",
            "input_constraint": "lawful side <=10 keeps scale 3 output within 30x30",
        },
        "settings": rows,
        "parameter_distinction": parameter_distinction,
        "canonical_scale_two_exact": canonical_exact,
        "all_racket_exact": all(row["all_racket_exact"] for row in rows),
        "all_python_exact": all(row["all_python_exact"] for row in rows),
        "all_lessons_identifiable": all(
            row["lesson_identifiable_for_every_query"] for row in rows
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in rows
        ),
        "all_public_ids_visible_only": all(
            row["public_id_visible_only"] for row in rows
        ),
        "unique_input_count": len(set(all_input_hashes)),
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
            for path in source_paths
        },
        "limitations": [
            "This is a task-local proposed extension; production remains output scale 2.",
            "Evidence covers one retained five-demo/four-query episode per setting.",
            "Finite declared-rival checks do not prove unique induction against all programs.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/8e6c44aee812/workspace/parametric/verify.py",
                "--artifact-root",
                "../checks/parametric/8e6c44aee812-output-scale-v1",
                "--out",
                "../checks/parametric/8e6c44aee812-output-scale-v1/report.json",
            ],
        },
    }
    private_dir = artifact_root / "private"
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / "summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_report(artifact_root=args.artifact_root)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    ok = all(
        (
            report["canonical_scale_two_exact"],
            report["all_racket_exact"],
            report["all_python_exact"],
            report["all_lessons_identifiable"],
            report["all_public_challenges_masked"],
            report["all_public_ids_visible_only"],
            report["unique_input_count"] == 18,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded adversarial check for the 3a0af56db83e public batch writer."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile


TASK_ID = "3a0af56db83e"
FORBIDDEN_PUBLIC_TOKENS = (
    "lower_band_order",
    "racket",
    "parameters",
    "seed",
    "query_output",
)


def load_prototype(repo: Path):
    path = repo / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    spec = importlib.util.spec_from_file_location("parametric_public_order_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(repo: Path) -> dict:
    proto = load_prototype(repo)
    rows = []
    tamper_result = None
    duplicate_result = None
    with tempfile.TemporaryDirectory(prefix="3a0af56db83e-public-order-") as directory:
        root = Path(directory)
        retained_seed_zero = None
        # Reuse one Racket process for all materializations.  The writer/privacy
        # assertions do not need a fresh interpreter per seed, and the separate
        # final verifier/tamper check below still exercises an independent replay.
        with proto.RacketBridge() as bridge:
            for seed in range(4):
                out = root / f"seed-{seed}"
                observed = []
                real_write_json = proto.write_json

                def recording_write(path, value):
                    candidate = Path(path)
                    if candidate.parent.name == "public":
                        observed.append(candidate.name)
                    real_write_json(candidate, value)

                proto.write_json = recording_write
                try:
                    report = proto.materialize(
                        out,
                        seed=seed,
                        demo_count=2,
                        query_count=4,
                        bridge=bridge,
                    )
                finally:
                    proto.write_json = real_write_json

                public_paths = sorted((out / "public").glob("challenge-*.json"))
                public_text = [path.read_text(encoding="utf-8") for path in public_paths]
                query_shapes_ok = all(
                    set(pair) == {"input"}
                    for path in public_paths
                    for pair in json.loads(path.read_text(encoding="utf-8"))["test"]
                )
                row = {
                    "seed": seed,
                    "settings": [
                        episode["parameters"]["lower_band_order"]
                        for episode in report["episodes"]
                    ],
                    "observed_public_write_order": observed,
                    "sorted_public_write_order": sorted(observed),
                    "public_write_order_is_visible_name_sorted": observed == sorted(observed),
                    "public_file_count": len(public_paths),
                    "public_forbidden_tokens_absent": all(
                        token not in text
                        for text in public_text
                        for token in FORBIDDEN_PUBLIC_TOKENS
                    ),
                    "public_queries_have_inputs_only": query_shapes_ok,
                    "materialize_status": report["status"],
                    "episode_labels_checked": report["counts"]["episode_labels"],
                }
                rows.append(row)
                if seed == 0:
                    retained_seed_zero = out

            if retained_seed_zero is None:
                raise AssertionError("seed-zero evidence was not created")

            duplicate_out = root / "duplicate-visible-id"
            real_public_filename = proto.public_filename
            proto.public_filename = lambda _challenge: "challenge-duplicate-visible-id.json"
            try:
                try:
                    proto.materialize(
                        duplicate_out,
                        seed=0,
                        demo_count=2,
                        query_count=4,
                        bridge=bridge,
                    )
                except ValueError as exc:
                    duplicate_result = {
                        "rejected": str(exc) == "duplicate visible public challenge id",
                        "error": f"{type(exc).__name__}: {exc}",
                        "public_files_written": len(list((duplicate_out / "public").glob("*"))),
                    }
                else:
                    duplicate_result = {
                        "rejected": False,
                        "error": None,
                        "public_files_written": len(list((duplicate_out / "public").glob("*"))),
                    }
            finally:
                proto.public_filename = real_public_filename

        report = json.loads((retained_seed_zero / "report.json").read_text(encoding="utf-8"))
        public_path = retained_seed_zero / report["episodes"][0]["public_path"]
        challenge = json.loads(public_path.read_text(encoding="utf-8"))
        original = challenge["train"][0]["output"][0][0]
        challenge["train"][0]["output"][0][0] = (original + 1) % 10
        proto.write_json(public_path, challenge)
        tampered = proto.verify_tree(retained_seed_zero, root=repo)
        tamper_result = {
            "status": tampered["status"],
            "errors": tampered["errors"],
            "rejected": tampered["status"] == "fail" and bool(tampered["errors"]),
        }

    checks = {
        "all_public_batches_sorted": all(
            row["public_write_order_is_visible_name_sorted"] for row in rows
        ),
        "all_public_views_private_free": all(
            row["public_forbidden_tokens_absent"] and row["public_queries_have_inputs_only"]
            for row in rows
        ),
        "all_clean_materializations_pass": all(
            row["materialize_status"] == "no_ambiguity_found" for row in rows
        ),
        "tampered_public_artifact_rejected": bool(tamper_result and tamper_result["rejected"]),
        "duplicate_visible_id_rejected_before_public_emission": bool(
            duplicate_result
            and duplicate_result["rejected"]
            and duplicate_result["public_files_written"] == 0
        ),
    }
    return {
        "schema": "3a0af56db83e-public-order-adversarial-v1",
        "scope": "four consecutive two-setting materializations using one shared Racket bridge; public emission order, duplicate-ID rejection, private-field masking, and one independent verifier tamper rejection",
        "rows": rows,
        "duplicate_visible_id": duplicate_result,
        "tamper": tamper_result,
        "checks": checks,
        "status": "pass" if all(checks.values()) else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repo.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": result["checks"]}, sort_keys=True))
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())

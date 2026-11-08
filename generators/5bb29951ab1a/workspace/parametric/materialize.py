#!/usr/bin/env python3
"""Materialize Racket-verified evidence for the threshold prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from parametric import threshold_prototype as proto
except ModuleNotFoundError:  # Direct execution from this directory.
    import threshold_prototype as proto

SCHEMA = "arcpuzzles-parametric-threshold-evidence-v1"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def _aggregate_histograms(pairs):
    total = {str(degree): 0 for degree in range(5)}
    for pair in pairs:
        for degree, count in proto.adjacency_histogram(pair["input"]).items():
            total[str(degree)] += count
    return total


def build_bundle(*, seed_base: int = 9400):
    """Build and execute one complete episode for every allowed threshold."""
    if type(seed_base) is not int:
        raise ValueError("seed_base must be an integer")

    prototype_path = Path(proto.__file__).resolve()
    source_sha256 = hashlib.sha256(prototype_path.read_bytes()).hexdigest()
    production_generator_path = proto.TASK_HOME / "generator.py"
    production_generator_sha256 = hashlib.sha256(
        production_generator_path.read_bytes()
    ).hexdigest()
    settings = []

    for threshold in proto.ALLOWED_THRESHOLDS:
        seed = seed_base + threshold
        episode = proto.build_episode(seed, threshold=threshold)
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        program = proto.racket_program(threshold)
        actual = proto.racket_outputs(program, inputs)
        if actual != expected:
            raise AssertionError(f"Racket/Python parity failed for threshold {threshold}")

        rivals = []
        rival_witnesses = {}
        for rival in proto.ALLOWED_THRESHOLDS:
            if rival == threshold:
                continue
            differing = [
                index
                for index, pair in enumerate(episode["train"])
                if proto.apply_python(pair["input"], rival) != pair["output"]
            ]
            if not differing:
                raise AssertionError(
                    f"threshold {threshold} is not distinguished from rival {rival}"
                )
            rivals.append(rival)
            rival_witnesses[str(rival)] = differing

        settings.append(
            {
                "threshold": threshold,
                "seed": seed,
                "canonical_setting": threshold == proto.DEFAULT_THRESHOLD,
                "program": program,
                "program_sha256": _sha256_text(program),
                "episode": episode,
                "episode_sha256": _canonical_json_sha256(episode),
                "challenge": proto.public_challenge(episode),
                "train_adjacency_histogram": _aggregate_histograms(episode["train"]),
                "rivals_distinguished": rivals,
                "rival_witness_train_indices": rival_witnesses,
                "racket_verified": True,
            }
        )

    return {
        "schema": SCHEMA,
        "task_id": proto.TASK_ID,
        "prototype_version": proto.PROTOTYPE_VERSION,
        "prototype_source": str(prototype_path.relative_to(proto.ROOT)),
        "prototype_source_sha256": source_sha256,
        "production_generator_source": str(
            production_generator_path.relative_to(proto.ROOT)
        ),
        "production_generator_sha256": production_generator_sha256,
        "canonical_program_sha256": _sha256_text(proto.canonical_program()),
        "parameter": {
            "name": "orthogonal_neighbor_threshold",
            "allowed": list(proto.ALLOWED_THRESHOLDS),
            "default": proto.DEFAULT_THRESHOLD,
            "selection_scope": "once_per_episode",
            "semantic_effect": (
                "A sparse-color dot becomes the rectangle color exactly when its "
                "original-input orthogonal rectangle-neighbor count meets the threshold; "
                "otherwise it becomes background."
            ),
            "input_constraints": (
                "Each retained pair contains dots with support degrees 0, 1, 2, and "
                "at least one of 3/4, so every allowed threshold has positive and "
                "negative branches and is distinguished from both rivals."
            ),
        },
        "settings": settings,
        "limits": [
            "Prototype only; production generation and canonical approval remain fixed at threshold 2.",
            "Evidence covers three deterministic episodes and finite rival settings, not all lawful grids.",
            "Frequency-based role inference still assumes exactly two nonzero colors and a strictly modal rectangle color.",
        ],
    }


def write_bundle(out_dir: Path, examples_dir: Path, *, seed_base: int = 9400):
    """Write private evidence plus public challenge files; return written paths."""
    bundle = build_bundle(seed_base=seed_base)
    out_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    written = []
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(summary_path)

    for setting in bundle["settings"]:
        threshold = setting["threshold"]
        episode_path = out_dir / f"threshold-{threshold}-episode.json"
        challenge_path = examples_dir / f"threshold-{threshold}-challenge.json"
        episode_path.write_text(
            json.dumps(setting["episode"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        challenge_path.write_text(
            json.dumps(setting["challenge"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.extend((episode_path, challenge_path))

    manifest = {
        "schema": "arcpuzzles-parametric-threshold-files-v1",
        "summary": str(summary_path),
        "files": [
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in written
        ],
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path, bundle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--examples-dir", type=Path, required=True)
    parser.add_argument("--seed-base", type=int, default=9400)
    args = parser.parse_args(argv)

    manifest_path, bundle = write_bundle(
        args.out_dir,
        args.examples_dir,
        seed_base=args.seed_base,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "manifest": str(manifest_path),
                "settings": [row["threshold"] for row in bundle["settings"]],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

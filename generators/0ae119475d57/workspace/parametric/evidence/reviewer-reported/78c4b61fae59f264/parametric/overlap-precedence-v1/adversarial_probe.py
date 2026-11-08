#!/usr/bin/env python3
"""Independent bounded verifier for retained overlap-precedence evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

FORBIDDEN_PUBLIC_TOKENS = (
    "overlap_precedence",
    "lower_wins",
    "upper_wins",
    "query_answers",
    '"seed"',
    "program_sha256",
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_prototype(root: Path):
    path = root / "generators/0ae119475d57/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("retained_overlap_precedence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def expect_rejected(call, label: str) -> str:
    try:
        call()
    except ValueError as exc:
        return f"{label}: {exc}"
    raise AssertionError(f"{label} was accepted")


def verify(evidence: Path) -> dict:
    root = find_root(__file__)
    prototype, prototype_path = load_prototype(root)
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["prototype"]["sha256"] == sha256(prototype_path.read_bytes())
    generator_path = root / manifest["selected_generator"]["file"]
    assert manifest["selected_generator"]["sha256"] == sha256(generator_path.read_bytes())

    for setting, row in manifest["programs"].items():
        path = evidence / row["file"]
        raw = path.read_bytes()
        assert sha256(raw) == row["sha256"]
        assert raw.decode("utf-8") == prototype.materialize_rule(setting, root=root)

    public_rows = []
    for path in sorted((evidence / "public").glob("challenge-*.json")):
        raw = path.read_bytes()
        public = json.loads(raw)
        assert raw == public_challenge_bytes(public)
        public_id = public_challenge_id(public)
        assert path.name == f"challenge-{public_id}.json"
        text = raw.decode("utf-8")
        assert not any(token in text for token in FORBIDDEN_PUBLIC_TOKENS)
        assert all(set(pair) == {"input"} for pair in public["test"])
        public_rows.append({"public_id": public_id, "bytes": len(raw)})
    assert len(public_rows) == 2

    episode_rows = []
    for path in sorted((evidence / "private/episodes").glob("*.json")):
        episode = json.loads(path.read_text(encoding="utf-8"))
        selected = episode["parameter"]["overlap_precedence"]
        rival = "upper_wins" if selected == "lower_wins" else "lower_wins"
        assert episode["demo_count"] == 2
        assert episode["query_count"] == 4
        assert episode["surviving_settings_from_demonstrations"] == [selected]
        assert episode["rival_checks"][selected]["demonstration_disagreements"] == []
        assert episode["rival_checks"][selected]["query_disagreements"] == []
        assert episode["rival_checks"][rival]["demonstration_disagreements"] == [0, 1]
        assert episode["rival_checks"][rival]["query_disagreements"] == [0, 1, 2, 3]
        assert len(set(episode["input_sha256"])) == 6
        episode_rows.append({
            "public_id": episode["public_id"],
            "selected": selected,
            "unique_inputs": len(set(episode["input_sha256"])),
        })
    assert {row["selected"] for row in episode_rows} == {"lower_wins", "upper_wins"}

    boundary_rejections = [
        expect_rejected(lambda: prototype.parameter_for_seed(True), "bool seed"),
        expect_rejected(lambda: prototype.parameter_for_seed(-1), "negative seed"),
        expect_rejected(
            lambda: prototype.episode_inputs(0, demo_count=0, root=root),
            "zero demos",
        ),
        expect_rejected(
            lambda: prototype.episode_inputs(0, query_count=9, root=root),
            "too many queries",
        ),
        expect_rejected(
            lambda: prototype.materialize_rule("separator_wins", root=root),
            "unknown setting",
        ),
    ]

    witness = json.loads(
        (evidence / "private/distinguishing-witness.json").read_text(encoding="utf-8")
    )
    with RacketBridge() as bridge:
        replayed = {
            setting: prototype.execute_rule(
                prototype.materialize_rule(setting, root=root),
                witness["input"],
                bridge=bridge,
                root=root,
            )
            for setting in ("lower_wins", "upper_wins")
        }
    assert replayed == witness["outputs"]
    assert replayed["lower_wins"] != replayed["upper_wins"]

    return {
        "schema": "0ae119475d57-overlap-precedence-adversarial-v1",
        "status": "pass",
        "surfaces": {
            "parameter_racket_parity": {
                "status": "pass",
                "witness_settings_differ": True,
                "canonical_default_sha256": manifest["canonical_source_sha256"],
            },
            "public_private_and_numeric_boundaries": {
                "status": "pass",
                "public_challenges": public_rows,
                "episodes": episode_rows,
                "rejections": boundary_rejections,
            },
        },
        "limits": [
            "finite retained seeds 0 and 1 only",
            "rival family limited to the opposite overlap precedence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

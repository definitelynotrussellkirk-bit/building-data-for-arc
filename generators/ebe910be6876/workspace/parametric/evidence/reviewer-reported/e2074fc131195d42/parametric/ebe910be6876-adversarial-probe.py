#!/usr/bin/env python3
"""Bounded adversarial replay for the ebe910be6876 magnification proposal."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[2]
REPO = WORK / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import find_root  # noqa: E402

ROOT = find_root(HERE)
TASK = ROOT / "generators" / "ebe910be6876"
PROTOTYPE_PATH = TASK / "workspace" / "parametric" / "prototype.py"
VERIFY_PATH = TASK / "workspace" / "parametric" / "verify.py"
REPORT_PATH = WORK / "checks" / "parametric" / "ebe910be6876-magnification.json"
OUTPUT_PATH = WORK / "checks" / "parametric" / "ebe910be6876-adversarial.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_value_error(label: str, call, fragment: str) -> dict[str, str | bool]:
    try:
        call()
    except ValueError as error:
        message = str(error)
        if fragment not in message:
            raise AssertionError(f"{label}: unexpected message {message!r}") from error
        return {"label": label, "rejected": True, "message": message}
    raise AssertionError(f"{label}: expected ValueError")


def main() -> int:
    proto = load_module("adversarial_parametric_ebe910be6876", PROTOTYPE_PATH)
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    boundary_10 = proto._GEN.generate(
        1001, 2001, difficulty="hard", grid_h=10, grid_w=10
    )
    scaled_10 = proto.solve(boundary_10, magnification=3)
    if (len(scaled_10), len(scaled_10[0])) != (30, 30):
        raise AssertionError("10x10 magnification-3 boundary did not produce 30x30")

    boundary_11 = proto._GEN.generate(
        1002, 2002, difficulty="hard", grid_h=11, grid_w=11
    )
    rejections = [
        expect_value_error(
            "11x11-at-m3-exceeds-arc-limit",
            lambda: proto.solve(boundary_11, magnification=3),
            "scaled output exceeds ARC's 30x30 limit",
        ),
        expect_value_error(
            "bool-is-not-magnification",
            lambda: proto.solve(boundary_10, magnification=True),
            "magnification must be one of",
        ),
        expect_value_error(
            "episode-pair-cap",
            lambda: proto.generate_episode(
                7, magnification=2, demo_count=12, query_count=13
            ),
            "must not exceed 24",
        ),
    ]

    intended_exact = 0
    rival_exact = 0
    rival_refutations = 0
    for setting in report["settings"]:
        for pair in setting["pairs"]:
            intended_exact += bool(pair["racket_matches_stored"])
            for rival in pair["rivals"]:
                rival_exact += bool(rival["racket_matches_python"])
                rival_refutations += bool(rival["differs_from_intended"])
    if (intended_exact, rival_exact, rival_refutations) != (21, 42, 42):
        raise AssertionError(
            "unexpected exactness/refutation totals: "
            f"{intended_exact}, {rival_exact}, {rival_refutations}"
        )

    artifact_root = TASK / "workspace" / "parametric" / "evidence" / "retained"
    public_rows = []
    public_files = sorted((artifact_root / "public").glob("challenge-*.json"))
    if len(public_files) != 3:
        raise AssertionError(f"expected 3 retained public challenges, got {len(public_files)}")
    for path in public_files:
        match = re.fullmatch(r"challenge-([0-9a-f]{64})\.json", path.name)
        if match is None:
            raise AssertionError(f"non-opaque public filename: {path.name}")
        data = path.read_bytes()
        file_sha = sha256_bytes(data)
        if file_sha != match.group(1):
            raise AssertionError(f"filename/content hash mismatch for {path.name}")
        public = json.loads(data)
        if set(public) != {"train", "test"}:
            raise AssertionError(f"private top-level key leaked in {path.name}")
        if not all(set(pair) == {"input", "output"} for pair in public["train"]):
            raise AssertionError(f"malformed visible demonstrations in {path.name}")
        if not all(set(pair) == {"input"} for pair in public["test"]):
            raise AssertionError(f"query answer/private field leaked in {path.name}")
        whitespace_mutation_sha = sha256_bytes(data + b" ")
        if whitespace_mutation_sha == file_sha:
            raise AssertionError("content mutation unexpectedly preserved SHA-256")
        public_rows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": file_sha,
                "filename_matches_bytes": True,
                "query_answers_masked": True,
                "mutation_detected": True,
            }
        )

    source_hashes = {
        str(path.relative_to(ROOT)): sha256_bytes(path.read_bytes())
        for path in (
            TASK / "generator.py",
            PROTOTYPE_PATH,
            VERIFY_PATH,
        )
    }
    if source_hashes != report["source_hashes"]:
        raise AssertionError(
            f"source-bound report is stale: {source_hashes} != {report['source_hashes']}"
        )

    result = {
        "schema": "ebe910be6876-parametric-adversarial-v1",
        "passed": True,
        "surfaces": {
            "parameter_boundaries": {
                "m3_10x10_output_dimensions": [30, 30],
                "rejections": rejections,
            },
            "racket_and_rival_replay": {
                "intended_racket_exact": intended_exact,
                "rival_racket_python_exact": rival_exact,
                "rival_outputs_refuting_intended": rival_refutations,
            },
            "public_export_integrity": {
                "files": public_rows,
                "all_content_addressed": True,
                "all_query_answers_masked": True,
                "all_byte_mutations_detected": True,
            },
            "source_binding": {
                "report_matches_current_sources": True,
                "source_hashes": source_hashes,
            },
        },
        "limitations": [
            "This bounded pass replays three retained episodes, not every seed.",
            "It does not broaden the production odd-coordinate support or resolve the retained snapping-shortcut audit.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "../checks/parametric/ebe910be6876-adversarial-probe.py",
            ],
        },
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

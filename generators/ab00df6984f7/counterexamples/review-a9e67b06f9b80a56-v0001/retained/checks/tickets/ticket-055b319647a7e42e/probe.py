from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

TICKET_ID = "ticket-055b319647a7e42e"
TASK_ID = "ab00df6984f7"
EXPECTED_SOURCE_SHA = "22b8362e7f78589ab539b237fd4dfda5300caaf4e070f46dcafc2753c01a9575"
EXPECTED_RULE_HASH = "debb1a8a129a"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid: object) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    started = time.monotonic()
    repo = Path.cwd().resolve()
    out_dir = (repo.parent / "checks/tickets" / TICKET_ID).resolve()
    source = repo / "generators" / TASK_ID / "generator.py"
    source_sha = sha(source)
    assert source_sha == EXPECTED_SOURCE_SHA, source_sha

    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source)
    assert spec and spec.loader
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    canonical_path = repo / "shared/data/canonical/puzzles.jsonl"
    canonical_row = None
    for line in canonical_path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            canonical_row = row
            break
    assert canonical_row is not None
    pairs = list(canonical_row["train"]) + list(canonical_row["test"])
    assert len(pairs) == 5
    pair = pairs[0]
    grid = pair["input"]
    canonical = pair["output"]

    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert gen.self_check(grid) == []
    assert "identity" in gen.CANONICAL_SHORTCUTS
    identity_output = gen.CANONICAL_SHORTCUTS["identity"](grid)
    mirror_output = gen.rule_mirror(grid)
    assert mirror_output == canonical
    assert identity_output != canonical

    input_path = out_dir / "input.json"
    racket_path = out_dir / "racket-receipt.json"
    input_path.write_text(json.dumps(grid, indent=2) + "\n")
    command = [
        sys.executable,
        "-m",
        "arcpuzzles",
        "apply",
        TASK_ID,
        "--input",
        str(input_path),
        "--out",
        str(racket_path),
    ]
    proc = subprocess.run(command, cwd=repo, text=True, capture_output=True, timeout=90)
    if proc.returncode != 0:
        raise AssertionError({"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    receipt = json.loads(racket_path.read_text())
    assert receipt["executed_rule_hash"] == EXPECTED_RULE_HASH
    assert receipt["generator_sha256"] == EXPECTED_SOURCE_SHA
    assert receipt["results"][0]["valid_output"] is True
    racket_output = receipt["results"][0]["output"]
    assert racket_output == canonical
    assert racket_output != identity_output

    fit = []
    for item in pairs:
        fit.append(gen.CANONICAL_SHORTCUTS["identity"](item["input"]) == item["output"])
    assert fit == [False] * 5

    witness = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "status": "finding",
        "finding_id": "A2-CANONICAL-SHORTCUT-CONTRACT",
        "generator_sha256": source_sha,
        "rule_hash": EXPECTED_RULE_HASH,
        "source": "canonical pair 0",
        "plausible_shortcut": "identity",
        "declared_in": "CANONICAL_SHORTCUTS",
        "canonical_fit": {"matches": sum(fit), "pairs": len(fit), "per_pair": fit},
        "belongs_to_documented_domain": gen.self_check(grid) == [],
        "input": grid,
        "authoritative_output": racket_output,
        "shortcut_output": identity_output,
        "rival_disagrees": racket_output != identity_output,
        "input_sha256": grid_sha(grid),
        "authoritative_output_sha256": grid_sha(racket_output),
        "shortcut_output_sha256": grid_sha(identity_output),
        "racket_receipt": "checks/tickets/ticket-055b319647a7e42e/racket-receipt.json",
        "command": command,
        "command_stdout": proc.stdout,
        "command_stderr": proc.stderr,
        "finding": (
            "The current source declares identity as a CANONICAL_SHORTCUTS member, "
            "but identity fits 0/5 canonical pairs. Canonical pair 0 is lawful and the live "
            "Racket authority returns the tight 4x5 crop, not the original 8x9 input."
        ),
        "limits": [
            "One declared shortcut and one live canonical witness were probed.",
            "No peer battery, generated census, source edit, or approval decision was performed.",
            "The finding is source-bound and awaits maintainer assessment."
        ],
        "targeted_probe_count": 1,
        "targeted_probe_elapsed_seconds": time.monotonic() - started,
    }
    witness_path = out_dir / "witness.json"
    witness_path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "finding",
        "finding_id": witness["finding_id"],
        "identity_canonical_fit": witness["canonical_fit"],
        "racket_matches_canonical": True,
        "witness": str(witness_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reproducible adversarial probes for the two assigned audit targets."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs  # noqa: E402

TARGETS = ("9d0a6f959321", "2361d6aa42c3")


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def color_components(grid, color, *, diagonals=False):
    h, w = len(grid), len(grid[0])
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diagonals:
        dirs += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    seen = set()
    groups = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            groups.append(cells)
    return groups


def recolor_border_groups(grid, *, diagonals=False):
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for cells in color_components(grid, 7, diagonals=diagonals):
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            for r, c in cells:
                out[r][c] = 3
    return out


def degree_one_rule(grid):
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3:
                continue
            degree = sum(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == 3
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if degree == 1:
                out[r][c] = 2
    return out


def straight_only_rival(grid):
    out = copy.deepcopy(grid)
    for cells in color_components(grid, 3):
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if len(rows) == 1:
            r = next(iter(rows))
            ordered = sorted(c for _, c in cells)
            out[r][ordered[0]] = 2
            out[r][ordered[-1]] = 2
        elif len(cols) == 1:
            c = next(iter(cols))
            ordered = sorted(r for r, _ in cells)
            out[ordered[0]][c] = 2
            out[ordered[-1]][c] = 2
        # Plausible shortcut: non-straight green components are left unchanged.
    return out


def source_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_rule(task_id: str):
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == task_id:
            src = row["program_solution"]
            digest = hashlib.sha256(" ".join(src.split()).encode()).hexdigest()[:12]
            return src, digest
    raise KeyError(task_id)


def _attach_racket_evidence(task_id: str, record: dict, *, source: str, domain_note: str) -> None:
    """Attach supported apply output and emit one compact intake-ready record."""
    task_dir = PACKET / "checks" / "audit" / task_id
    racket_path = task_dir / "racket.json"
    if not racket_path.is_file():
        return
    payload = json.loads(racket_path.read_text())
    results = payload.get("results") or []
    if len(results) != 1 or results[0].get("error") is not None:
        raise AssertionError(f"unexpected Racket apply result for {task_id}: {results!r}")
    actual = results[0]["output"]
    expected = record["python_intended_output"]
    if actual != expected:
        raise AssertionError(
            f"Racket/Python intended-output mismatch for {task_id}: {actual!r} != {expected!r}"
        )
    record["racket_matches_python_intended"] = True
    record["racket_output"] = actual
    record["counterexample_source"] = source
    record["documented_domain_note"] = domain_note
    compact = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "classification": record["classification"],
        "generator_sha256": record["generator_sha256"],
        "rule_hash": record["rule_hash"],
        "sample_policy": record["sample_policy"],
        "generated_inputs": record["generated_inputs"],
        "counterexample_source": source,
        "counterexample_passes_self_check": record["counterexample_self_check"] == [],
        "counterexample_self_check": record["counterexample_self_check"],
        "documented_domain_note": domain_note,
        "input": json.loads((task_dir / "input.json").read_text()),
        "actual_racket_output": actual,
        "rival_output": record["rival_output"],
        "racket_matches_python_intended": True,
        "apply_command": payload.get("command"),
        "apply_cwd": payload.get("cwd"),
        "racket_evidence_path": str(racket_path.relative_to(PACKET)),
    }
    (task_dir / "counterexample.json").write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    output = {}

    # Audit 1: ordinary generator enforces 8-neighbor separation, so an
    # 8-connected interpretation of orange objects is observationally identical.
    task = "9d0a6f959321"
    gen, path = load_generator(task)
    mismatch = 0
    total = 0
    diagonal_contacts = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(1, 201):
            grid = gen.generate(seed, seed, difficulty=band)
            total += 1
            mismatch += recolor_border_groups(grid) != recolor_border_groups(
                grid, diagonals=True
            )
            groups = color_components(grid, 7)
            diagonal_contacts += any(
                (r + dr, c + dc) in other
                for index, cells in enumerate(groups)
                for other in groups[index + 1 :]
                for r, c in cells
                for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1))
            )

    counterexample_9d = [
        [7, 7, 0, 0, 0, 0],
        [7, 0, 7, 7, 0, 0],
        [0, 0, 7, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    intended_9d = recolor_border_groups(counterexample_9d)
    rival_9d = recolor_border_groups(counterexample_9d, diagonals=True)
    (PACKET / "checks" / "audit" / task / "input.json").write_text(
        json.dumps(counterexample_9d, indent=2) + "\n"
    )
    (PACKET / "checks" / "audit" / task / "rival.json").write_text(
        json.dumps(rival_9d, indent=2) + "\n"
    )
    _, rule_hash = canonical_rule(task)
    output[task] = {
        "classification": "reproduced curriculum shortcut and 8-neighbor support restriction",
        "generator_sha256": source_sha(path),
        "rule_hash": rule_hash,
        "sample_policy": "bands easy/medium/hard; seed=sample_index=1..200",
        "generated_inputs": total,
        "eight_connected_rival_mismatches_on_generated": mismatch,
        "generated_inputs_with_diagonal_orange_component_contact": diagonal_contacts,
        "counterexample_self_check": gen.self_check(copy.deepcopy(counterexample_9d)),
        "python_intended_output": intended_9d,
        "rival_output": rival_9d,
        "unknown_override_silently_accepted": (
            gen.generate(11, 7, difficulty="medium", typo_axis=True)
            == gen.generate(11, 7, difficulty="medium")
        ),
    }

    # Audit 2: ordinary support contains only straight components, despite the
    # selected degree-1 rule and every canonical pair containing bends.
    task = "2361d6aa42c3"
    gen, path = load_generator(task)
    mismatch = 0
    total = 0
    nonstraight_components = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(1, 201):
            grid = gen.generate(seed, seed, difficulty=band)
            total += 1
            intended = degree_one_rule(grid)
            rival = straight_only_rival(grid)
            mismatch += intended != rival
            nonstraight_components += sum(
                len({r for r, _ in cells}) > 1 and len({c for _, c in cells}) > 1
                for cells in color_components(grid, 3)
            )

    pair = canonical_pairs(task, root=REPO, labeled_only=True)[0]
    counterexample_2361 = pair["input"]
    intended_2361 = degree_one_rule(counterexample_2361)
    rival_2361 = straight_only_rival(counterexample_2361)
    (PACKET / "checks" / "audit" / task / "input.json").write_text(
        json.dumps(counterexample_2361, indent=2) + "\n"
    )
    (PACKET / "checks" / "audit" / task / "rival.json").write_text(
        json.dumps(rival_2361, indent=2) + "\n"
    )
    _, rule_hash = canonical_rule(task)
    output[task] = {
        "classification": "reproduced canonical-domain restriction and shortcut",
        "generator_sha256": source_sha(path),
        "rule_hash": rule_hash,
        "sample_policy": "bands easy/medium/hard; seed=sample_index=1..200",
        "generated_inputs": total,
        "straight_only_rival_mismatches_on_generated": mismatch,
        "nonstraight_components_in_generated": nonstraight_components,
        "counterexample_source": "canonical train[0]",
        "counterexample_self_check": gen.self_check(copy.deepcopy(counterexample_2361)),
        "python_intended_matches_canonical": intended_2361 == pair["output"],
        "python_intended_output": intended_2361,
        "rival_output": rival_2361,
        "declared_non_straight_texture_is_validator_accepted": not bool(
            gen.self_check(gen.generate(1, 1, texture="non_straight"))
        ),
        "unknown_override_silently_accepted": (
            gen.generate(11, 7, difficulty="medium", typo_axis=True)
            == gen.generate(11, 7, difficulty="medium")
        ),
    }

    _attach_racket_evidence(
        "9d0a6f959321",
        output["9d0a6f959321"],
        source="constructed 6x6 validator-accepted 4-connected-domain counterexample",
        domain_note=(
            "Passes self_check and is lawful for the selected 4-connected rule; "
            "ordinary generate() excludes it through stricter 8-neighbor clearance."
        ),
    )
    _attach_racket_evidence(
        "2361d6aa42c3",
        output["2361d6aa42c3"],
        source="canonical train[0]",
        domain_note=(
            "Canonical and validator-accepted; ordinary generate() emits only straight "
            "segments, while the accepted non_straight texture and canonical data contain bends."
        ),
    )

    out_path = PACKET / "checks" / "audit" / "probe-summary.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""Focused, findings-only audit. Run from this packet's repo via run_with_racket.py."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

TASK = "144e23365d4b"
EXPECTED_SOURCE = "2fcae7fb489a44b4891b8d56c3f28498ecfa382a5a572d899a46188a0a2d682a"
OUT = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

ROOT = find_root(ROOT)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid):
    data = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def components(grid):
    """Independent measurements, not an authoritative implementation."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                 if v not in (0, 9)}
    found = []
    while remaining:
        first = min(remaining)
        cells = {first}
        remaining.remove(first)
        pending = [first]
        while pending:
            r, c = pending.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in remaining:
                    remaining.remove(q)
                    cells.add(q)
                    pending.append(q)
        cur, depth = set(cells), 0
        while cur:
            boundary = {p for p in cur if any(q not in cur for q in
                        ((p[0] - 1, p[1]), (p[0] + 1, p[1]),
                         (p[0], p[1] - 1), (p[0], p[1] + 1)))}
            cur -= boundary
            depth += 1
        rs, cs = [p[0] for p in cells], [p[1] for p in cells]
        found.append({"area": len(cells), "max_onion_depth": depth,
                      "bbox": [min(rs), min(cs), max(rs), max(cs)],
                      "colors": sorted({grid[r][c] for r, c in cells}),
                      "cells": sorted(cells)})
    return sorted(found, key=lambda x: (x["bbox"][1], x["bbox"][0]))


def largest_area(grid, comps):
    winner = max(comps, key=lambda c: c["area"])
    result = [[0] * len(grid[0]) for _ in grid]
    for r, c in winner["cells"]:
        result[r][c] = 8
    return result


def main():
    if (OUT / "result.json").exists() or (OUT / "racket.json").exists():
        raise RuntimeError("Refusing to overwrite prior audit results")
    source = ROOT / "generators" / TASK / "generator.py"
    source_before = sha(source)
    assert source_before == EXPECTED_SOURCE, ("unexpected source", source_before)
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    bound_files = [source, source.parent / "notes.md",
                   source.parent / "evidence/review_index.json",
                   source.parent / "evidence/associated_notes.jsonl",
                   ROOT / "shared/runtime/reviewer_support.py",
                   ROOT / "shared/runtime/puzzle_generators/base.py"]
    hashes_before = {str(p.relative_to(ROOT)): sha(p) for p in bound_files}
    selected_rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                selected_rows.append(row)
    assert len(selected_rows) == 1
    save("canonical.json", selected_rows)
    manifest = {"task_id": TASK, "source_sha256": source_before,
                "source_files": hashes_before, "probe_sha256": sha(Path(__file__)),
                "canonical_path": str(canonical_path(ROOT)),
                "canonical_rule_text_sha256": hashlib.sha256(
                    selected_rows[0]["program_solution"].encode()).hexdigest(),
                "scope": "3 canonical pairs; 6 default draws per band; 2 small refuters; focused overrides",
                "notes": "Existing review index reports the same area/depth shortcut as needs_triage."}
    cases = []

    def add(name, kind, grid, replay=None, expected=None):
        grid = normalize_grid(grid)
        comps = components(grid)
        case = {"name": name, "kind": kind, "input": grid,
                "input_sha256": grid_sha(grid), "replay": replay,
                "self_check": generator.self_check(copy.deepcopy(grid), difficulty=(replay or {}).get("difficulty")),
                "components": comps,
                "largest_area_prediction": largest_area(grid, comps)}
        if expected is not None:
            case["expected"] = expected
        cases.append(case)
        return case

    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        add(f"canonical-v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
            "canonical", pair["input"],
            {k: pair[k] for k in ("variant", "split", "pair_index")}, pair["output"])
    for band in ("easy", "medium", "hard"):
        for index in range(6):
            replay = {"seed": 0, "sample_index": index, "difficulty": band, "overrides": {}}
            add(f"default-{band}-{index}", "generated",
                generator.generate(0, index, difficulty=band), replay)

    minimal = [[0, 2, 0, 0, 3, 3, 3],
               [2, 2, 2, 0, 3, 3, 3],
               [0, 2, 0, 0, 0, 0, 0]]
    expected = [[8 if v == 2 else 0 for v in row] for row in minimal]
    add("minimal-depth2-area5-v-depth1-area6", "fixture", minimal, expected=expected)
    padded = [[0] * 10 for _ in range(9)]
    for r, row in enumerate(minimal):
        padded[r + 2][1:8] = row
    add("padded-depth2-area5-v-depth1-area6", "fixture", padded,
        expected=[[8 if v == 2 else 0 for v in row] for row in padded])

    base = next(c for c in cases if c["name"] == "default-easy-0")
    override_rows = []
    requests = [(key, value) for key in ("n_distractors", "palette_size", "n_distinct_colors")
                for value in ((2, 3) if key == "n_distractors" else (3, 4))]
    requests += [(key, value) for key in ("palette_kind", "texture")
                 for value in ("default", "warm", "cool", "varied")]
    for key, value in requests:
        replay = {"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": {key: value}}
        grid = generator.generate(0, 0, difficulty="easy", **{key: value})
        case = add(f"override-{key}-{value}", "override", grid, replay)
        n_colors = len({v for row in grid for v in row if v != 0})
        observed = len(case["components"]) - 1 if key == "n_distractors" else n_colors
        override_rows.append({"name": case["name"], "replay": replay,
                              "input_sha256": case["input_sha256"],
                              "same_grid_as_default_easy_0": grid == base["input"],
                              "observed_component_count": len(case["components"]),
                              "observed_nonzero_color_count": n_colors,
                              "requested_count_honored": observed == value
                              if key in ("n_distractors", "palette_size", "n_distinct_colors") else None})
    for key, value in (("grid_h", 9), ("grid_h", 20), ("grid_w", 10), ("grid_w", 24)):
        replay = {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": {key: value}}
        row = {"name": f"declared-valid-{key}-{value}", "replay": replay,
               "declared_axis": generator.AXES[key]}
        try:
            grid = generator.generate(0, 0, **{key: value})
            case = add(row["name"], "override", grid, replay)
            row.update({"input_sha256": case["input_sha256"], "shape": [len(grid), len(grid[0])]})
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        override_rows.append(row)
    save("override_results.json", override_rows)
    save("cases.json", cases)
    save("inputs.json", [c["input"] for c in cases])
    manifest["case_count"] = len(cases)
    manifest["case_names"] = [c["name"] for c in cases]
    save("probe_manifest.json", manifest)
    assert len(cases) <= 64

    argv = [sys.executable, "-m", "arcpuzzles", "--library", str(ROOT),
            "apply", TASK, "--input", str(OUT / "inputs.json"),
            "--out", str(OUT / "racket.json"), "--timeout", "180"]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / p) for p in ("src", "shared/runtime", "."))
    command = {"argv": argv, "cwd": str(ROOT), "exit": None,
               "environment": {k: env[k] for k in
                               ("PYTHONPATH", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "TMPDIR")
                               if k in env}}
    save("apply.command.json", command)
    stdout, stderr = b"", b""
    try:
        completed = subprocess.run(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, timeout=240)
        stdout, stderr = completed.stdout, completed.stderr
        command["exit"] = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        command["error"] = "TimeoutExpired"
        raise
    finally:
        (OUT / "apply.stdout").write_bytes(stdout)
        (OUT / "apply.stderr").write_bytes(stderr)
        save("apply.command.json", command)
    assert completed.returncode == 0, (completed.returncode, stderr.decode(errors="replace"))
    receipt = json.loads((OUT / "racket.json").read_text())
    assert receipt["schema"] == "arcpuzzles-apply-v1"
    assert receipt["task_id"] == receipt["rule_task_id"] == TASK
    assert receipt["reference"] == "canonical" and receipt["rule_hash_matches_catalog"]
    assert receipt["generator_sha256"] == source_before
    assert receipt["rule_text_sha256"] == manifest["canonical_rule_text_sha256"]
    rows = receipt["results"]
    assert len(rows) == len(cases) and [row["index"] for row in rows] == list(range(len(cases)))
    for case, row in zip(cases, rows):
        assert row["input"] == case["input"]
        assert row["valid_output"] and row.get("error") is None, (case["name"], row.get("error"))
        case["reference"] = {"receipt": "racket.json", "index": row["index"], "output": row["output"],
                             "output_sha256": row["output_sha256"]}
        case["largest_area_matches_reference"] = case["largest_area_prediction"] == row["output"]
        if "expected" in case:
            assert case["expected"] == row["output"], case["name"]
    save("cases.json", cases)
    hashes_after = {str(p.relative_to(ROOT)): sha(p) for p in bound_files}
    assert hashes_before == hashes_after, "Audited source or notes changed during probe"
    groups = {}
    for kind in ("canonical", "generated", "fixture", "override"):
        group = [c for c in cases if c["kind"] == kind]
        groups[kind] = {"total": len(group),
                        "largest_area_fit": sum(c["largest_area_matches_reference"] for c in group),
                        "self_check_rejected": sum(bool(c["self_check"]) for c in group)}
    result = {"task_id": TASK, "status": "evidence_collected", "source_sha256": source_before,
              "source_sha256_after": sha(source), "source_files_after": hashes_after,
              "probe_sha256": sha(Path(__file__)), "groups": groups,
              "per_band": {band: {"total": 6, "largest_area_fit": sum(
                  c["largest_area_matches_reference"] for c in cases
                  if c["kind"] == "generated" and c["replay"]["difficulty"] == band)}
                  for band in ("easy", "medium", "hard")},
              "apply_receipt": "racket.json", "apply_sha256": sha(OUT / "racket.json"),
              "apply_exit": command["exit"], "executed_rule_hash": receipt["executed_rule_hash"],
              "rule_text_sha256": receipt["rule_text_sha256"],
              "ignored_override_draws_identical": sum(r.get("same_grid_as_default_easy_0", False)
                                                       for r in override_rows),
              "count_override_violations": [r["name"] for r in override_rows
                                            if r.get("requested_count_honored") is False],
              "declared_valid_size_errors": [r for r in override_rows if "error" in r]}
    save("counterexample.json", {"source_sha256": source_before,
         "rule_receipt": "racket.json", "cases": [c for c in cases
         if c["kind"] == "fixture" or c["name"] in ("canonical-v0-test-0", "default-easy-0")]})
    save("result.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    command = {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "exit": None}
    try:
        main()
        command["exit"] = 0
    except Exception as exc:
        command["exit"] = 1
        command["error"] = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    finally:
        save("audit.command.json", command)
    raise SystemExit(command["exit"])

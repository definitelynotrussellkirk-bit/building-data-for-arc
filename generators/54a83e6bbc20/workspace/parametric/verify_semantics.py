"""Focused actual-Racket verification; run with --out PATH (no fallback/skip)."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

TASK = "54a83e6bbc20"
MODES = ("top_to_bottom", "bottom_to_top")
HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(value).hexdigest()


def reconstruction(grid, order):
    """Independent row-cut/count oracle: no generator geometry helpers."""
    h, w = len(grid), len(grid[0])
    assert w == 11 and (h - 1) % 4 == 0
    n = (h - 1) // 4
    assert n in (2, 3, 4) and all(len(row) == w for row in grid)
    assert all(v == 7 for r in range(0, h, 4) for v in grid[r])
    cuts, candidates = [], []
    for top in range(1, h, 4):
        cut = tuple(sum(v == 8 for v in grid[top + j][:5]) for j in range(3))
        assert all(1 <= k <= 4 for k in cut)
        assert all(grid[top + j][:5] == [8] * k + [7] * (5 - k) for j, k in enumerate(cut))
        right = [grid[top + j][5:] for j in range(3)]
        colors = {v for row in right for v in row if v != 7}
        assert len(colors) == 1 and 8 not in colors
        color = next(iter(colors))
        widths = tuple(sum(v == color for v in row) for row in right)
        assert all(1 <= k <= 4 for k in widths)
        assert all(row == [7] * (6 - k) + [color] * k for row, k in zip(right, widths))
        cuts.append(cut)
        candidates.append((widths, color))
    assert len({c for widths, c in candidates}) == n
    result = [[7] * w for _ in range(h)]
    matches = []
    for i, cut in enumerate(cuts):
        matching = [(j, color) for j, (widths, color) in enumerate(candidates)
                    if widths == tuple(5 - k for k in cut)]
        assert len(matching) == 1, (cut, candidates)
        slot, color = matching[0]
        matches.append(slot)
        top = 1 + 4 * (i if order == "top_to_bottom" else n - 1 - i)
        for j, k in enumerate(cut):
            result[top + j][:5] = [8] * k + [color] * (5 - k)
    assert len(set(matches)) == n
    return result


def swap_blocks(grid, start, stop):
    result = [row[:] for row in grid]
    for j in range(3):
        result[1 + j][start:stop], result[5 + j][start:stop] = (
            result[5 + j][start:stop], result[1 + j][start:stop])
    return result


def run(report):
    from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK, root=root)
    prototype_path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_local_54a83e6bbc20_prototype", prototype_path)
    assert spec and spec.loader
    prototype = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = prototype
    spec.loader.exec_module(prototype)
    assert Path(prototype.__file__).resolve() == prototype_path
    assert tuple(prototype.ALLOWED_ASSEMBLY_ORDERS) == MODES
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    authority = [row for row in rows if row.get("task_id") == TASK]
    assert len(authority) == 1
    canonical_rule = authority[0]["program_solution"]
    cases = []
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    for pair in pairs:
        cases.append({"id": f"canonical-v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
                      "input": pair["input"], "canonical_label": pair["output"]})
    for band, count in (("easy", 2), ("medium", 3), ("hard", 4)):
        for index in (0, 1):
            grid = gen.generate(18, index, difficulty=band)
            assert len(grid) == 4 * count + 1
            cases.append({"id": f"seed18-{band}-{index}", "input": grid})
    base_index = next(i for i, c in enumerate(cases) if c["id"] == "seed18-hard-0")
    base = cases[base_index]["input"]
    cyan_swap, right_swap = swap_blocks(base, 0, 5), swap_blocks(base, 5, 11)
    assert all(a[5:] == b[5:] for a, b in zip(base, cyan_swap))
    assert all(a[:5] == b[:5] for a, b in zip(base, right_swap))
    cases.extend([{"id": "counterfactual-cyan-blocks-0-1-swapped", "input": cyan_swap},
                  {"id": "counterfactual-right-slots-0-1-swapped", "input": right_swap}])
    for case in cases:
        errors = gen.self_check(case["input"])
        case["self_check_errors"] = errors
        assert not errors, (case["id"], errors)
    report.update(generator_sha256=source_sha, generator_source=str(source_path.relative_to(root)),
                  prototype_sha256=digest(prototype_path.read_bytes()),
                  canonical_raw_rule_sha256=digest(canonical_rule.encode()), cases=cases)
    report["modes"] = {}
    for mode in MODES:
        source = prototype.racket_source(mode, root=root)
        expected_source = (canonical_rule if mode == MODES[0] else canonical_rule.replace(
            "(r0 (obj-r1 left))", "(r0 (- h 1 (obj-r2 left)))"))
        assert canonical_rule.count("(r0 (obj-r1 left))") == 1
        assert source == expected_source, "Mode changes exceed the declared row-origin edit"
        info = {"rule_source_sha256": digest(source.encode()),
                "rule_hash": digest(" ".join(source.split()).encode())[:12]}
        report["modes"][mode] = info
        outputs = prototype._racket_outputs(source, [case["input"] for case in cases])
        assert len(outputs) == len(cases), "Missing actual Racket outputs"
        info["actual_racket_cases"] = len(outputs)
        for case, actual in zip(cases, outputs):
            expected = reconstruction(case["input"], mode)
            case.setdefault("actual_outputs", {})[mode] = actual
            assert actual == expected, (mode, case["id"], "Racket disagrees with independent cut/color oracle")
            assert prototype.python_transform(case["input"], mode, root=root) == expected
            if mode == MODES[0] and "canonical_label" in case:
                assert actual == case["canonical_label"], case["id"]
        assert outputs[base_index] != outputs[-2], "Cyan swap failed to defeat right-only shortcut"
        assert outputs[base_index] == outputs[-1], "Candidate location changed shape-match semantics"
        info.update(cyan_only_swap_changes_output=True, right_slot_swap_preserves_output=True,
                    internal_row_orientation_preserved=True, background_and_dimensions_preserved=True)
    report.update(status="completed", canonical_labeled_pairs=len(pairs),
                  generated_samples=6, counterfactuals=2, actual_racket_evaluations=2 * len(cases))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    report = {"schema": "jigsaw-assembly-focused-semantics-v1", "task_id": TASK,
              "status": "blocked", "command": [sys.executable, *sys.argv],
              "scope": "All labeled canonical fixtures; seed18 indices0,1 at easy/medium/hard; two lawful counterfactuals; actual Racket batch per mode.",
              "limitations": ["Focused verification, not exhaustive generation or rival census.",
                              "Python helper parity supplements actual Racket; missing Racket fails."]}
    try:
        run(report)
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "actual_racket_evaluations": report["actual_racket_evaluations"]}))


if __name__ == "__main__":
    main()

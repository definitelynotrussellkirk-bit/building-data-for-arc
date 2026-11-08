"""Findings-only audit; public canonical apply supplies all retained labels."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK = "e51bd0fdbc36"
OUT = Path(__file__).resolve().parent
for ancestor in OUT.parents:
    helper = ancestor / "repo/shared/runtime/reviewer_support.py"
    if helper.is_file():
        sys.path.insert(0, str(helper.parent))
        break
from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arcpuzzles import Catalog


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def direction(grid):
    if all(value == 9 for value in grid[0]):
        return "top", -1, 0
    if all(value == 9 for value in grid[-1]):
        return "bottom", 1, 0
    if all(row[0] == 9 for row in grid):
        return "left", 0, -1
    return "right", 0, 1


def neighbors(grid, r, c):
    return [grid[nr][nc] for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0])]


def transform(grid, mode="canonical"):
    """Independent source-based reconstruction, checked against public Racket."""
    _edge, dr, dc = direction(grid)
    output = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            nearby = neighbors(grid, r, c)
            nr, nc = r + dr, c + dc
            inside = 0 <= nr < len(grid) and 0 <= nc < len(row)
            if mode == "canonical":
                enclosed = bool(nearby) and all(v in (2, 8) for v in nearby)
            elif mode == "forward_red_collision":
                enclosed = inside and grid[nr][nc] == 2
            elif mode == "touch_any_red":
                enclosed = 2 in nearby
            elif mode == "always_extend":
                enclosed = False
            else:
                raise ValueError(mode)
            if enclosed:
                output[r][c] = 2
            elif inside:
                output[nr][nc] = 8
    return output


RIVALS = ("forward_red_collision", "touch_any_red", "always_extend")


def facts(grid):
    edge, dr, dc = direction(grid)
    cyan, enclosed, boundary, blocked = [], [], [], []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            cyan.append([r, c])
            nearby = neighbors(grid, r, c)
            is_enclosed = bool(nearby) and all(v in (2, 8) for v in nearby)
            if is_enclosed:
                enclosed.append([r, c])
            if r in (0, len(grid) - 1) or c in (0, len(row) - 1):
                boundary.append([r, c])
            nr, nc = r + dr, c + dc
            if not is_enclosed and 0 <= nr < len(grid) and 0 <= nc < len(row) and grid[nr][nc] == 2:
                blocked.append({"cyan": [r, c], "red_destination": [nr, nc]})
    return {"height": len(grid), "width": len(grid[0]), "edge": edge,
            "cyan": cyan, "enclosed_cyan": enclosed, "boundary_cyan": boundary,
            "free_cyan_with_red_destination": blocked,
            "red_count": sum(v == 2 for row in grid for v in row)}


def main():
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    metadata = Catalog(root=root).get(TASK)
    rules = [variant["program_solution"] for variant in metadata["variants"]]
    normalized = {" ".join(rule.split()) for rule in rules}
    if len(normalized) != 1:
        raise ValueError("Canonical variants have different reference rules")
    rule_hash = hashlib.sha256(next(iter(normalized)).encode()).hexdigest()
    (OUT / "generator_source.py").write_bytes(source.read_bytes())
    (OUT / "reference.rkt").write_text(rules[0] + "\n")
    subjects = []
    for pair in canonical:
        subjects.append({"kind": "canonical", "variant": pair["variant"], "split": pair["split"],
                         "pair_index": pair["pair_index"], "input": pair["input"], "retained_output": pair["output"]})

    population, counts, first_special = [], {}, {}
    for band in ("easy", "medium", "hard"):
        tally = Counter()
        for i in range(1000):
            recipe = {"seed": 150000 + i, "sample_index": i * 31 + 7, "difficulty": band, "overrides": {}}
            grid = gen.generate(recipe["seed"], recipe["sample_index"], difficulty=band)
            observed = facts(grid)
            errors = gen.self_check(grid)
            row = {"recipe": recipe, "input_sha256": sha(grid), "facts": observed, "self_check": errors}
            population.append(row)
            tally["draws"] += 1
            tally["self_check_rejections"] += bool(errors)
            tally["with_enclosed_cyan"] += bool(observed["enclosed_cyan"])
            tally["with_red_destination"] += bool(observed["free_cyan_with_red_destination"])
            tally["boundary_cyan"] += bool(observed["boundary_cyan"])
            tally["edge_" + observed["edge"]] += 1
            if i < 6:
                subjects.append({"kind": "production_sample", "recipe": recipe, "input": grid})
            for feature in ("enclosed_cyan", "free_cyan_with_red_destination"):
                key = band + ":" + feature
                if observed[feature] and key not in first_special:
                    first_special[key] = row
                    subjects.append({"kind": "production_feature", "feature": feature, "recipe": recipe, "input": grid})
        counts[band] = dict(tally)

    enclosed_grid = [[7] * 13 for _ in range(13)]
    enclosed_grid[0] = [9] * 13
    for r, c in ((3, 3), (6, 6), (9, 4), (9, 9)):
        enclosed_grid[r][c] = 8
    for r, c in ((5, 6), (7, 6), (6, 5), (6, 7)):
        enclosed_grid[r][c] = 2
    subjects.append({"kind": "constructed_counterexample", "name": "accepted_enclosure_hard_profile",
                     "recipe": {"seed": None, "sample_index": None, "overrides": None,
                                "construction": "13x13 orange; top row9; cyan (3,3),(6,6),(9,4),(9,9); red (5,6),(7,6),(6,5),(6,7)"},
                     "input": enclosed_grid})

    lesson = None
    for seed in range(1000):
        grids = [gen.generate(seed, i, difficulty="medium") for i in range(5)]
        if len({direction(g)[0] for g in grids[:4]}) != 4:
            continue
        true = [transform(g) for g in grids]
        guessed = [transform(g, "forward_red_collision") for g in grids]
        if true[:4] == guessed[:4] and true[4] != guessed[4]:
            lesson = {"seed": seed, "sample_indices": list(range(5)), "difficulty": "medium",
                      "overrides": {}, "train_indices": list(range(4)), "query_index": 4,
                      "demo_edges": [direction(g)[0] for g in grids[:4]]}
            for i, grid in enumerate(grids):
                subjects.append({"kind": "ambiguous_lesson", "split": "train" if i < 4 else "test",
                                 "recipe": {"seed": seed, "sample_index": i, "difficulty": "medium", "overrides": {}},
                                 "input": grid})
            break
    if lesson is None:
        raise ValueError("No bounded four-edge lesson counterexample found")
    if len(subjects) > 64:
        raise ValueError("Public apply batch exceeds64 subjects")
    for subject in subjects:
        subject["input_sha256"] = sha(subject["input"])
        subject["facts"] = facts(subject["input"])
        subject["self_check"] = gen.self_check(subject["input"])
    (OUT / "population.json").write_text(json.dumps(population, separators=(",", ":")) + "\n")
    (OUT / "subjects.json").write_text(json.dumps(subjects, indent=2) + "\n")
    input_path = OUT / "inputs.json"
    input_path.write_text(json.dumps({"inputs": [row["input"] for row in subjects]}) + "\n")
    label_path = OUT / "racket_labels.json"
    command = [sys.executable, "-m", "arcpuzzles", "apply", TASK, "--input", str(input_path),
               "--reference", "canonical", "--check-generator-domain", "--timeout", "120", "--out", str(label_path)]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=180)
    command_record = {"command": command, "cwd": str(root), "exit_code": result.returncode,
                      "stdout": result.stdout, "stderr": result.stderr,
                      "probe_command": [sys.executable, *sys.argv], "probe_cwd": str(Path.cwd())}
    (OUT / "command.json").write_text(json.dumps(command_record, indent=2) + "\n")
    if result.returncode:
        raise RuntimeError(result.stderr + result.stdout)
    labels = json.loads(label_path.read_text())["results"]
    if len(labels) != len(subjects):
        raise ValueError("Public apply label count mismatch")
    for subject, label in zip(subjects, labels):
        expected = label["output"]
        if label["error"] or transform(subject["input"]) != expected:
            raise ValueError("Independent reconstruction disagrees with Racket")
        if subject["kind"] == "canonical" and subject["retained_output"] != expected:
            raise ValueError("Retained canonical labels disagree with Racket")
        subject["output"] = expected
        subject["rivals"] = {mode: {"output": transform(subject["input"], mode),
                                    "matches": transform(subject["input"], mode) == expected}
                             for mode in RIVALS}
    canon_rows = [row for row in subjects if row["kind"] == "canonical"]
    episode_rows = [row for row in subjects if row["kind"] == "ambiguous_lesson"]
    assert all(row["rivals"]["forward_red_collision"]["matches"] for row in episode_rows[:4])
    assert not episode_rows[4]["rivals"]["forward_red_collision"]["matches"]
    assert not any(row["self_check"] for row in episode_rows)
    summary = {"task_id": TASK, "generator_sha256": source_sha,
               "rule_normalized_sha256": rule_hash, "rule_hash": metadata["rule_hash"],
               "rule_source_sha256": hashlib.sha256(rules[0].encode()).hexdigest(),
               "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "canonical_labeled_pairs": len(canon_rows), "canonical_unique_inputs": len({row["input_sha256"] for row in canon_rows}),
               "canonical_rejected_by_self_check": sum(bool(row["self_check"]) for row in canon_rows),
               "canonical_fitting_rivals": {mode: all(row["rivals"][mode]["matches"] for row in canon_rows) for mode in RIVALS},
               "population": counts, "first_special": first_special, "ambiguous_lesson": lesson,
               "racket_inputs_executed": len(subjects), "racket_command_exit": result.returncode,
               "open_audits_before": {key: metadata[key] for key in ("audit_unresolved", "audit_unresolved_count", "audit_pending_triage_count")},
               "generator_unchanged": hashlib.sha256(source.read_bytes()).hexdigest() == source_sha,
               "scope": "Findings-only. 3000 default input feature inspections; only retained subjects executed in Racket. One bounded same-seed consecutive five-input lesson search; no full battery or universal teachability claim."}
    (OUT / "scored_subjects.json").write_text(json.dumps(subjects, indent=2) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

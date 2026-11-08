"""Bounded default-lesson self-review; run through this packet's review.py."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

TASK = "a4d31efd3a2f"
NAMES = ("bottom_right", "rightmost", "minimum_bbox_area", "lowest_color")


def sha(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def components(grid):
    seen, result = set(), []
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if not color or (row, col) in seen:
                continue
            cells, todo = [], [(row, col)]
            seen.add((row, col))
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = r + dr, c + dc
                    if (0 <= p[0] < len(grid) and 0 <= p[1] < len(grid[0])
                            and p not in seen and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        todo.append(p)
            result.append({"cells": cells, "color": color,
                           "bbox": [min(r for r, c in cells), min(c for r, c in cells),
                                    max(r for r, c in cells), max(c for r, c in cells)]})
    return result


def predict(grid, name):
    objs = components(grid)
    def key(obj):
        r1, c1, r2, c2 = obj["bbox"]
        score = {"bottom_right": -(r2 + c2), "rightmost": -c2,
                 "minimum_bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
                 "lowest_color": obj["color"]}[name]
        return score, obj["color"]
    selected = min(objs, key=key)
    r1, c1, r2, c2 = selected["bbox"]
    output = [[0] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]
    for row, col in selected["cells"]:
        output[row - r1][col - c1] = selected["color"]
    return output


def program(canonical, name):
    old = "(if (= (obj-size a) (obj-size b)) (< (obj-color a) (obj-color b)) (< (obj-size a) (obj-size b)))"
    if canonical.count(old) != 1:
        raise ValueError("Exact canonical selection expression changed")
    def score(obj):
        bb = f"(bbox-of-cells (obj-cells {obj}))"
        if name == "bottom_right":
            return f"(+ (third {bb}) (fourth {bb}))"
        if name == "rightmost":
            return f"(fourth {bb})"
        if name == "minimum_bbox_area":
            return f"(* (+ 1 (- (third {bb}) (first {bb}))) (+ 1 (- (fourth {bb}) (second {bb}))))"
        return f"(obj-color {obj})"
    a, b = score("a"), score("b")
    relation = ">" if name in ("bottom_right", "rightmost") else "<"
    replacement = f"(if (= {a} {b}) (< (obj-color a) (obj-color b)) ({relation} {a} {b}))"
    return canonical.replace(old, replacement)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=32)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or not 1 <= args.count <= 32:
        raise ValueError("Use a fresh destination and a bounded count in 1..32")
    root = Path.cwd()
    catalog = Catalog(root)
    descriptor = catalog.describe(TASK)
    canonical = next(iter({v["program_solution"] for v in catalog.get(TASK)["variants"]}))
    programs = {name: program(canonical, name) for name in NAMES}
    request = {"count": args.count, "seed": args.seed, "n_train": None,
               "n_test": 1, "allow_unapproved": True, "timeout": 60}
    episodes = catalog.generate(TASK, **request)
    summary = {name: {"demo_fits": 0, "query_disagreements_after_demo_fit": 0} for name in NAMES}
    candidates, lessons = {}, []
    for index, episode in enumerate(episodes):
        record = {"index": index, "sample_index": episode.get("sample_index"),
                  "train_count": len(episode["train"]), "test_count": len(episode["test"]),
                  "input_sha256": {split: [sha(p["input"]) for p in episode[split]] for split in ("train", "test")},
                  "rivals": {}}
        for name in NAMES:
            fits = all(predict(pair["input"], name) == pair["output"] for pair in episode["train"])
            record["rivals"][name] = {"fits_demonstrations": fits}
            if not fits:
                continue
            summary[name]["demo_fits"] += 1
            disagreements = [i for i, pair in enumerate(episode["test"])
                             if predict(pair["input"], name) != pair["output"]]
            record["rivals"][name]["query_disagreements"] = disagreements
            if disagreements:
                summary[name]["query_disagreements_after_demo_fit"] += len(disagreements)
                candidates.setdefault(name, (index, episode, disagreements))
        lessons.append(record)
    findings, runtime_identity, evaluations = [], None, 0
    if candidates:
        runtime = root / "shared/runtime"
        with _local_imports(runtime, root / "generators" / TASK / "workspace"):
            apply, runtime_identity, bridge = _real_evaluator(runtime)
            try:
                for name, (index, episode, disagreements) in candidates.items():
                    observed = {"train": [], "test": []}
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            correct = _grid(apply(canonical, pair["input"]))
                            rival = _grid(apply(programs[name], pair["input"]))
                            evaluations += 2
                            assert correct == pair["output"]
                            assert rival == predict(pair["input"], name)
                            observed[split].append(rival)
                    assert all(out == pair["output"] for out, pair in zip(observed["train"], episode["train"]))
                    assert all(observed["test"][i] != episode["test"][i]["output"] for i in disagreements)
                    findings.append({"rival": name, "lesson_index": index,
                                     "sample_index": episode.get("sample_index"),
                                     "train": episode["train"], "test": episode["test"],
                                     "rival_outputs": observed, "query_disagreements": disagreements,
                                     "canonical_program": canonical, "rival_program": programs[name],
                                     "status": "protected_racket_confirmed"})
            finally:
                bridge.close()
    current = hashlib.sha256((root / descriptor["generator"]).read_bytes()).hexdigest()
    assert current == descriptor["generator_sha256"]
    report = {"schema": "arcpuzzles-bounded-peer-rival-probe-v1", "task_id": TASK,
              "status": "findings" if findings else "finite_no_finding",
              "request": request, "command": list(sys.argv),
              "generator_sha256": current, "rule_hash": descriptor["rule_hash"],
              "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "approved_at_probe": descriptor["approved"], "approval_reasons": descriptor["approval_reasons"],
              "review_index_present": (root / "generators" / TASK / "evidence/review_index.json").exists(),
              "summary": summary, "lessons": lessons, "findings": findings,
              "racket": runtime_identity, "protected_counterexample_evaluations": evaluations,
              "default_pairs_materialized": sum(len(e["train"]) + len(e["test"]) for e in episodes),
              "limitations": "32 default lessons and four finite rivals only; public generation supplies Racket labels. Python screens rivals; retained finding lessons are replayed with both complete programs through protected Racket. No production edit, approval, admission, or full battery."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "lessons": len(episodes), "summary": summary,
                      "protected_findings": len(findings), "protected_counterexample_evaluations": evaluations,
                      "generator_sha256": current, "out": str(args.out)}))


if __name__ == "__main__":
    main()

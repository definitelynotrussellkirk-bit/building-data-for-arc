"""Bounded default-lesson search, followed by exact protected-Racket replay."""
from pathlib import Path
import hashlib
import json
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import load_selected_generator, canonical_path, normalize_grid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
TASK = "16296fabf4b4"


def components(grid):
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            h = max(x[0] for x in cells) - min(x[0] for x in cells) + 1
            w = max(x[1] for x in cells) - min(x[1] for x in cells) + 1
            result.append((cells, h, w))
    return result


def mirror(grid, predicate):
    out = [row[:] for row in grid]
    for cells, h, w in components(grid):
        if predicate(h, w):
            for r, c in cells:
                out[r][c] = 8
    return out


def execute(bridge, source, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


def main():
    generator, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
    sources = {r["program_solution"] for r in map(json.loads, canonical_path(ROOT).read_text().splitlines())
               if r.get("task_id") == TASK and r.get("program_solution")}
    assert len(sources) == 1
    canonical = sources.pop()
    needle = "(> (comp-h comp) (comp-w comp))"
    assert canonical.count(needle) == 1
    rivals = {
        "height_at_least_three": (lambda h, w: h >= 3, "(>= (comp-h comp) 3)"),
        "height_at_least_width": (lambda h, w: h >= w, "(>= (comp-h comp) (comp-w comp))"),
    }
    candidates, tested, errors = {}, 0, []
    # One bounded 32-seed scope, fixed first-three-demos/next-query schedule.
    for seed in range(32):
        try:
            grids = [generator.generate(seed, i) for i in range(4)]
        except Exception as exc:
            errors.append({"seed": seed, "error": str(exc)})
            continue
        tested += 1
        gold = [mirror(g, lambda h, w: h > w) for g in grids]
        for name, (predicate, replacement) in rivals.items():
            other = [mirror(g, predicate) for g in grids]
            if name not in candidates and other[:3] == gold[:3] and other[3] != gold[3]:
                candidates[name] = {"seed": seed, "grids": grids, "gold": gold,
                                    "other": other, "program": canonical.replace(needle, replacement)}

    findings = []
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        for name, case in candidates.items():
            actual = [execute(bridge, canonical, g) for g in case["grids"]]
            other = [execute(bridge, case["program"], g) for g in case["grids"]]
            assert actual == case["gold"] and other == case["other"]
            assert actual[:3] == other[:3] and actual[3] != other[3]
            findings.append({"rival": name, "seed": case["seed"], "difficulty": None,
                             "sample_indices": {"demonstrations": [0, 1, 2], "query": 3},
                             "canonical_program": canonical, "rival_program": case["program"],
                             "train": [{"input": g, "output": a, "rival_output": b}
                                       for g, a, b in zip(case["grids"][:3], actual[:3], other[:3])],
                             "query": {"input": case["grids"][3], "output": actual[3], "rival_output": other[3]},
                             "query_component_bboxes": [{"height": h, "width": w, "size": len(cells)}
                                                        for cells, h, w in components(case["grids"][3])],
                             "validator_errors": [generator.self_check(g) for g in case["grids"]],
                             "demonstration_mismatch_indices": [], "query_mismatch_indices": [0]})
        # The old validator finding is separate, and explicitly replayed here.
        prior = ROOT / f"generators/{TASK}/counterexamples/review-72d07f8d7ac14001-v0001/retained/checks/audit/{TASK}/input.json"
        grid = json.loads(prior.read_text())
        legacy = {"input_path": str(prior.relative_to(ROOT)), "validator_errors": generator.self_check(grid),
                  "racket_preserves_input": execute(bridge, canonical, grid) == grid}
    report = {"schema": "arcpuzzles-bounded-lesson-audit-v1", "task_id": TASK,
              "generator_sha256": source_sha, "canonical_source_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "racket": identity, "scope": {"seeds": [0, 31], "difficulty": None, "episodes": tested,
                                             "demonstrations": 3, "queries": 1, "rivals": list(rivals)},
              "findings": findings, "generation_errors": errors, "retained_validator_replay": legacy,
              "status": "supported_demo_query_ambiguity" if findings else "finite_no_finding",
              "limits": "Bounded direct-generator four-draw schedule only; no claim about every exported lesson. "
                        "Canonical approval and existing validator audit status remain unchanged."}
    (HERE / "learnability.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "episodes": tested, "generation_errors": len(errors),
                      "findings": [{"rival": f["rival"], "seed": f["seed"]} for f in findings],
                      "generator_sha256": source_sha, "protected": identity["protected"]}))


if __name__ == "__main__":
    main()

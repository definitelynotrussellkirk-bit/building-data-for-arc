"""Source-bound audit probe; run from repo via review.py run.

Search uses the generator mirror only to locate a candidate. Reported semantic
findings must then survive public Catalog.apply execution of canonical Racket.
The audited generator and its declared competitors are never modified.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys


TASK = "37348ddf20d0"
EXPECTED_SOURCE = "222bb3faed0e93a1ef53073874042a3e63e7e150fff1b49564f0735996448ba6"


def component_manhattan(grid):
    """Nearest seed in the same component, using Manhattan instead of path length."""
    h, w = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells, queue = [start], deque([start])
        while queue:
            r, c = queue.popleft()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.append(neighbor)
                    queue.append(neighbor)
        seeds = {color: [(r, c) for r, c in cells if grid[r][c] == color]
                 for color in (2, 3)}
        for r, c in cells:
            if grid[r][c] != 0:
                continue
            distances = {
                color: min((abs(r - sr) + abs(c - sc) for sr, sc in positions),
                           default=h * w + 1)
                for color, positions in seeds.items()
            }
            if distances[2] < distances[3]:
                result[r][c] = 2
            elif distances[3] < distances[2]:
                result[r][c] = 3
    return result


def changed_cells(expected, actual):
    return [{"row": r, "col": c, "canonical": value, "rival": actual[r][c]}
            for r, row in enumerate(expected) for c, value in enumerate(row)
            if value != actual[r][c]]


def scalar_probe(gen):
    cases = [
        ("seed_bool", True, 0, {}),
        ("seed_float", 1.75, 0, {}),
        ("seed_string", "1", 0, {}),
        ("index_bool", 1, True, {}),
        ("index_float", 1, 1.75, {}),
        ("index_string", 1, "1", {}),
        ("index_negative", 1, -1, {}),
        ("height_fractional", 1, 0, {"grid_h": 11.75}),
        ("height_string", 1, 0, {"grid_h": "11"}),
        ("width_fractional", 1, 0, {"grid_w": 12.75}),
        ("red_bool", 1, 0, {"n_red": True}),
        ("red_fractional", 1, 0, {"n_red": 2.75}),
        ("green_string", 1, 0, {"n_green": "2"}),
    ]
    records = []
    for name, seed, index, overrides in cases:
        row = {"case": name, "seed": seed, "sample_index": index,
               "overrides": overrides}
        try:
            grid = gen.generate(seed, index, **overrides)
        except Exception as exc:
            row.update(status="rejected", exception=type(exc).__name__, message=str(exc))
        else:
            row.update(status="accepted", observed=gen.observe_overrides(grid),
                       self_check=gen.self_check(grid))
        records.append(row)
    return records


def search(gen, limit):
    examined = 0
    for difficulty in ("easy", "medium", "hard"):
        for ordinal in range(limit):
            seed = 1 + 5 * ordinal
            demo = gen.generate(seed, 0, difficulty=difficulty)
            query = gen.generate(seed, 5, difficulty=difficulty)
            examined += 1
            if component_manhattan(demo) == gen.rule_mirror(demo) and \
                    component_manhattan(query) != gen.rule_mirror(query):
                grids = [gen.generate(seed, i, difficulty=difficulty) for i in range(6)]
                if all(component_manhattan(g) == gen.rule_mirror(g) for g in grids[:5]):
                    return {"assembly": "ordered_five_demos_one_query", "seed": seed,
                            "difficulty": difficulty, "indices": list(range(6)),
                            "query_position": 5, "searched_detour_pairs": examined}, grids
    # Conditional diagnostic only: a unique detour profile can be held out.
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(5):
            grids = [gen.generate(seed, i, difficulty=difficulty) for i in range(6)]
            for query_position in range(6):
                query = grids[query_position]
                demos = [g for i, g in enumerate(grids) if i != query_position]
                if all(component_manhattan(g) == gen.rule_mirror(g) for g in demos) and \
                        component_manhattan(query) != gen.rule_mirror(query):
                    return {"assembly": "query_rotation_only", "seed": seed,
                            "difficulty": difficulty, "indices": list(range(6)),
                            "query_position": query_position,
                            "searched_detour_pairs": examined}, grids
    return {"assembly": "no_candidate", "searched_detour_pairs": examined}, []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--search-limit", type=int, default=500)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path[:0] = [str(root / "shared/runtime"), str(root / "src")]
    from reviewer_support import canonical_pairs, load_selected_generator
    from arcpuzzles import Catalog

    gen, source, source_sha = load_selected_generator(TASK, root=root)
    if source_sha != EXPECTED_SOURCE:
        raise ValueError(f"source changed: {source_sha}; expected {EXPECTED_SOURCE}")
    records = scalar_probe(gen)
    candidate, generated = search(gen, args.search_limit)
    canonical = canonical_pairs(TASK, root=root)
    payload = {
        "schema": "37348ddf20d0-adversarial-audit-v1", "task_id": TASK,
        "generator_sha256": source_sha, "declared_rule_hash": gen.RULE_HASH,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "invocation": {"argv": sys.argv, "cwd": str(Path.cwd()),
                       "python": sys.executable, "source": str(source)},
        "scalar_cases": records, "candidate_search": candidate,
        "rival": "component_manhattan",
        "rival_description": "Respect connected components, but compare Manhattan seed distances inside each component.",
        "limits": ["Finite candidate search; not an ambiguity-rate estimate.",
                   "Mirrors screen candidates only; retained semantic verdict uses canonical Racket labels.",
                   "Query rotation is conditional unless assembly is explicitly ordered.",
                   "No generator, rule, approval, or training-admission changes."],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    inputs = [pair["input"] for pair in canonical] + generated
    try:
        applied = Catalog(root).apply(TASK, inputs, reference="canonical",
                                      allow_unapproved=True, timeout=180,
                                      check_generator_domain=True)
    except Exception as exc:
        payload["racket_failure"] = {"type": type(exc).__name__, "message": str(exc),
                                     "run": getattr(exc, "run", None)}
        args.out.write_text(json.dumps(payload, indent=2) + "\n")
        raise
    payload["racket_application"] = applied
    outputs = [row["output"] for row in applied["results"]]
    if any(output is None for output in outputs):
        payload["status"] = "racket_application_error"
        args.out.write_text(json.dumps(payload, indent=2) + "\n")
        return 2
    payload["canonical_pair_checks"] = [
        {"pair_index": i, "stored_label_matches_racket": pair["output"] == outputs[i],
         "rival_matches_racket": component_manhattan(pair["input"]) == outputs[i]}
        for i, pair in enumerate(canonical)
    ]
    if generated:
        answers = outputs[len(canonical):]
        pairs = [{"input": grid, "output": answer}
                 for grid, answer in zip(generated, answers, strict=True)]
        qi = candidate["query_position"]
        demos = [pair for i, pair in enumerate(pairs) if i != qi]
        rival_outputs = [component_manhattan(grid) for grid in generated]
        payload["lesson"] = {
            "profiles": [gen.observe_overrides(g)["texture"] for g in generated],
            "pairs": pairs, "query_position": qi,
            "rival_outputs": rival_outputs,
            "rival_fits_every_demo": all(rival_outputs[i] == answers[i]
                                          for i in range(6) if i != qi),
            "query_difference": changed_cells(answers[qi], rival_outputs[qi]),
            "declared_lesson_hook": gen.lesson_identifiable(demos, pairs[qi]),
            "self_checks": [gen.self_check(g) for g in generated],
            "mirror_parity": [gen.rule_mirror(g) == answer
                              for g, answer in zip(generated, answers, strict=True)],
        }
    payload["status"] = "completed"
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    lesson = payload.get("lesson", {})
    print(json.dumps({"status": payload["status"], "source": source_sha,
                      "accepted_invalid_calls": sum(r["status"] == "accepted" for r in records),
                      "candidate": candidate,
                      "canonical_rival_fits": sum(r["rival_matches_racket"]
                                                  for r in payload["canonical_pair_checks"]),
                      "rival_fits_every_demo": lesson.get("rival_fits_every_demo"),
                      "query_differences": len(lesson.get("query_difference", [])),
                      "declared_hook": lesson.get("declared_lesson_hook"),
                      "receipt": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

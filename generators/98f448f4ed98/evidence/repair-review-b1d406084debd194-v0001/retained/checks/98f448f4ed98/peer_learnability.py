"""Bounded source-bound audit; run through outer review.py run (protected Racket).

The reflected and canonical queries are transfer probes, not claimed native draws.
No approval, acceptance, or selected generator bytes are changed.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))
from reviewer_support import canonical_pairs, load_selected_generator
from arcpuzzles.catalog import Catalog

TASK = "98f448f4ed98"


def frames(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    boxes = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for q in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if q in remaining:
                    remaining.remove(q)
                    cells.add(q)
                    stack.append(q)
        boxes.append((min(r for r,c in cells), min(c for r,c in cells),
                      max(r for r,c in cells), max(c for r,c in cells)))
    return boxes


def rival_leftmost(grid):
    out = [row[:] for row in grid]
    r0, c0, r1, c1 = min(frames(grid), key=lambda b: b[1])
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = 8
    return out


def main():
    module, source, digest = load_selected_generator(TASK, root=REPO)
    demos = [module.generate(17, i, difficulty="medium") for i in range(3)]
    native_query = module.generate(17, 3, difficulty="medium")
    reflected = [row[::-1] for row in native_query]
    canonical = canonical_pairs(TASK, root=REPO, labeled_only=True)
    inputs = demos + [native_query, reflected] + [p["input"] for p in canonical]
    applied = Catalog(REPO).apply(TASK, inputs, timeout=60)
    assert applied["generator_sha256"] == digest
    assert applied["rule_hash_matches_catalog"]
    outputs = [r["output"] for r in applied["results"]]
    assert all(o is not None for o in outputs)
    assert all(not module.self_check(g) for g in demos + [native_query, reflected])
    assert all(rival_leftmost(g) == o for g, o in zip(demos, outputs[:3]))
    assert rival_leftmost(native_query) == outputs[3]
    assert rival_leftmost(reflected) != outputs[4]
    assert all(p["output"] == o for p, o in zip(canonical, outputs[5:]))
    assert rival_leftmost(canonical[0]["input"]) != outputs[5]
    try:
        module.generate(17, 0, difficulty="medium", k=6)
    except ValueError as error:
        override_error = str(error)
    else:
        raise AssertionError("Expected documented k=6 override to be rejected")
    report = {
        "schema": "bounded-peer-learnability-v1", "task_id": TASK,
        "source_path": str(source.relative_to(REPO)), "source_sha256": digest,
        "status": "unverified_owner_integration_needed", "approval_changed": False,
        "rival": "Fill the interior of the leftmost yellow frame, ignoring red markers.",
        "visible_demo_draws": [{"seed": 17, "sample_index": i, "difficulty": "medium"} for i in range(3)],
        "demo_fit": [True] * 3, "native_query_rival_agrees": True,
        "reflected_query_rival_agrees": False,
        "reflected_query_self_check": module.self_check(reflected),
        "canonical_exact_label_checks": len(canonical),
        "canonical_leftmost_rival_agrees": [rival_leftmost(p["input"]) == o for p, o in zip(canonical, outputs[5:])],
        "documented_k6_override_error": override_error,
        "public_transfer_episode": {"train": [{"input": g, "output": o} for g,o in zip(demos, outputs[:3])], "test": [{"input": reflected}]},
        "private_transfer_query": {"canonical_output": outputs[4], "rival_output": rival_leftmost(reflected)},
        "limits": ["Three visible demos and one native query; no full battery or exhaustive rival search.", "Reflected query is a documented self_check-valid counterfactual outside the selected generator's native placement support.", "This establishes transfer undercoverage, not a native generated episode whose query breaks the rival.", "No selected-source repair, owner acceptance, or parameterized qualification attempted."],
        "protected_racket_apply": applied,
    }
    target = Path(__file__).with_name("peer_learnability_report.json")
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("task_id", "source_sha256", "demo_fit", "native_query_rival_agrees", "reflected_query_rival_agrees", "canonical_exact_label_checks", "canonical_leftmost_rival_agrees", "documented_k6_override_error")}))


if __name__ == "__main__":
    main()

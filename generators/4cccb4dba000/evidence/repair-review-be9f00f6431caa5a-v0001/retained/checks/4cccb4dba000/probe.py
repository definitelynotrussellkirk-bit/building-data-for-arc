"""One source-bound replay of the retained 4-versus-8 connectivity lesson."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "4cccb4dba000"
HERE = Path(__file__).resolve().parent
ROOT = Path(find_root(Path.cwd()))
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
RETAINED = ROOT / "generators" / TASK_ID / "counterexamples" / "review-40979aa5b9514c87-v0001" / "retained" / "checks" / "audit" / TASK_ID / "evidence.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def components(grid, connectivity):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    offsets = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
               if (dr or dc) and (connectivity == 8 or abs(dr) + abs(dc) == 1)]
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, cells = [start], []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in offsets:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        rs, cs = zip(*cells)
        result.append({"bbox": [min(rs), min(cs), max(rs), max(cs)],
                       "red_count": sum(grid[r][c] == 2 for r, c in cells),
                       "cell_count": len(cells)})
    return result


def execute(bridge, program, grid):
    bridge.define_grid("peer_connectivity_grid", grid)
    expression = strip_rule_wrapper(strip_line_comments(program))
    return bridge.eval_text(f"({expression} peer_connectivity_grid)")


def main():
    retained = json.loads(RETAINED.read_text())
    assert SOURCE_SHA == retained["generator_sha256"], "retained witness is stale"
    rows = [json.loads(line) for line in canonical_path(ROOT).open() if line.strip()]
    selected = [row for row in rows if row.get("task_id") == TASK_ID
                and row.get("source") == "training" and row.get("parent_hash") is None]
    assert len(selected) == 1
    record = selected[0]
    canonical = record["program_solution"]
    original = "(objects-multicolor g 0)"
    replacement = "(objects (map-grid g (lambda (r c v) (if (= v 0) 0 1))) 0)"
    assert canonical.count(original) == 1
    rival = canonical.replace(original, replacement, 1)
    query = GEN.generate(retained["seed"], retained["sample_index"],
                         difficulty=retained["difficulty"], **retained["overrides"])
    assert query == retained["input"], "retained query did not regenerate"
    demos = record["train"]
    assert len(demos) == 3
    public = {"train": demos, "test": [{"input": query}]}
    public_bytes = encode(public)
    public_name = digest(public_bytes) + ".json"
    public_dir = HERE / "public"
    public_dir.mkdir(exist_ok=True)
    (public_dir / public_name).write_bytes(public_bytes + b"\n")

    with RacketBridge(timeout=20, max_calls_before_restart=64) as bridge:
        runtime = bridge.runtime_identity
        assert runtime.get("backend") == "racket" and runtime.get("protected") is True, runtime
        demo_checks = []
        for index, pair in enumerate(demos):
            intended = execute(bridge, canonical, pair["input"])
            alternative = execute(bridge, rival, pair["input"])
            demo_checks.append({"index": index,
                                "canonical_matches_visible_output": intended == pair["output"],
                                "rival_matches_visible_output": alternative == pair["output"]})
        intended_query = execute(bridge, canonical, query)
        rival_query = execute(bridge, rival, query)

    assert all(check["canonical_matches_visible_output"] and check["rival_matches_visible_output"]
               for check in demo_checks)
    assert intended_query == retained["actual_racket_output"]
    assert rival_query == retained["rival_output"]
    assert intended_query != rival_query
    validation = GEN.self_check(query)
    c8, c4 = components(query, 8), components(query, 4)
    assert validation == [] and len(c8) == 1 and len(c4) == 2
    evidence = {
        "schema": "arcpuzzles-peer-visible-lesson-replay-v1",
        "task_id": TASK_ID,
        "finding": "retained connectivity ambiguity reproduced; no new generator repair",
        "status": "finding_reproduced_unresolved",
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA,
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "canonical_record_sha256": digest(encode(record)),
        "canonical_record_selection": "Unique original training row, excluding the augmented variant.",
        "retained_evidence": str(RETAINED.relative_to(ROOT)),
        "retained_evidence_sha256": digest(RETAINED.read_bytes()),
        "public_challenge": "public/" + public_name,
        "public_challenge_sha256": digest((public_dir / public_name).read_bytes()),
        "programs": {
            "canonical_8connected": {"program": canonical, "sha256": digest(canonical.encode())},
            "rival_4connected": {"program": rival, "sha256": digest(rival.encode())}},
        "racket": runtime,
        "demonstrations": demo_checks,
        "query_provenance": {key: retained[key] for key in ("seed", "sample_index", "difficulty", "overrides")},
        "query": {"canonical_output": intended_query, "rival_output": rival_query,
                  "outputs_differ": True, "self_check": validation,
                  "components_8": c8, "components_4": c4},
        "scope": {"new_draws": 1, "new_search": False, "visible_demonstrations": 3,
                  "query_count": 1, "rivals_tested": 1, "protected_racket_applications": 8},
        "domain": {"helpful_overrides": True, "validator_accepts": True,
                   "documented_semantic_domain": False,
                   "reason": "Only one 8-connected cluster; the generator promises at least two separated clusters."},
        "command": ["WORK/.venv/bin/python", "review.py", "run", "python3", "../checks/4cccb4dba000/probe.py"],
        "preflight_correction": "Initial probe stopped before Racket execution because it assumed one ledger row per task; selected the original training row explicitly after observing the augmented row.",
        "limitations": [
            "Reuses a known source-bound counterexample; no new distribution-frequency estimate.",
            "Canonical demonstrations plus one generated query form an audit lesson, not a sampled production episode.",
            "The connectivity and red-count-clipping findings remain unresolved; generator and authority are unchanged.",
            "Two executable rules are retained for the same visible lesson; no approval or training admission is claimed."]}
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": evidence["status"], "demo_matches": "3/3 for both Racket programs",
                      "query_outputs": {"canonical_shape": [len(intended_query), len(intended_query[0])],
                                        "rival_shape": [len(rival_query), len(rival_query[0])]},
                      "protected": runtime["protected"], "generator_sha256": SOURCE_SHA}))


if __name__ == "__main__":
    main()

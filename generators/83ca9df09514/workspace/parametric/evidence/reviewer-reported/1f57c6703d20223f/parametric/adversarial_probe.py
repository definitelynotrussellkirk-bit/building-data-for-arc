from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/83ca9df09514/workspace/parametric/prototype.py"
OUT = ROOT.parent / "checks/parametric/duplicate-precedence-adversarial.json"

spec = importlib.util.spec_from_file_location("duplicate_precedence_probe", PROTOTYPE)
assert spec and spec.loader
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

canonical = p.canonical_source(root=ROOT)
alternate = p.materialize_rule("leftmost_wins", root=ROOT)
expected_alternate = canonical.replace(
    p.CANONICAL_MAPPING_LOOP, p.LEFTMOST_MAPPING_LOOP, 1
)
assert alternate == expected_alternate
assert canonical.count(p.CANONICAL_MAPPING_LOOP) == 1
assert alternate.count(p.LEFTMOST_MAPPING_LOOP) == 1
assert p.CANONICAL_MAPPING_LOOP not in alternate

rejections = {}
for name, source in {
    "trailing_newline": canonical + "\n",
    "unrelated_body_change": canonical.replace("(rows g)", "(+ 0 (rows g))", 1),
    "double_alternate_loop": alternate.replace(
        p.LEFTMOST_MAPPING_LOOP,
        p.LEFTMOST_MAPPING_LOOP + " " + p.LEFTMOST_MAPPING_LOOP,
        1,
    ),
}.items():
    try:
        if name == "double_alternate_loop":
            p.rule_setting(source, root=ROOT)
        else:
            p.materialize_rule(root=ROOT, source=source)
    except ValueError as exc:
        rejections[name] = str(exc)
    else:
        raise AssertionError(f"guard accepted tampered source: {name}")

inputs0 = p.episode_inputs(0, demo_count=8, query_count=8, root=ROOT)
inputs1 = p.episode_inputs(1, demo_count=8, query_count=8, root=ROOT)
assert inputs0 == inputs1
fingerprints = [p._grid_fingerprint(grid) for grid in inputs0]
assert len(fingerprints) == len(set(fingerprints)) == 16

conflict_rows = []
for grid in inputs0:
    template_row = p._template_row(grid)
    key_rows = [
        index
        for index, row in enumerate(grid)
        if index != template_row and any(row)
    ]
    conflicts = p._conflicting_key_rows(grid)
    assert conflicts == key_rows
    conflict_rows.append(len(conflicts))

with RacketBridge(max_calls_before_restart=128) as bridge:
    predictions = {
        setting: p.execute_rule_many(
            p.materialize_rule(setting, root=ROOT),
            inputs0,
            bridge=bridge,
            root=ROOT,
        )
        for setting in p.ALLOWED_PRECEDENCE
    }
    assert all(
        right != left
        for right, left in zip(
            predictions["rightmost_wins"],
            predictions["leftmost_wins"],
            strict=True,
        )
    )
    boundary_episodes = {}
    for seed in (0, 1):
        public, private = p.generate_episode(
            seed,
            demo_count=1,
            query_count=8,
            bridge=bridge,
            root=ROOT,
        )
        selected = private["parameter"]["duplicate_precedence"]
        rival = next(value for value in p.ALLOWED_PRECEDENCE if value != selected)
        assert private["rival_checks"][rival]["demonstration_disagreements"] == [0]
        assert private["rival_checks"][rival]["query_disagreements"] == list(range(8))
        boundary_episodes[str(seed)] = {
            "selected": selected,
            "public_sha256": hashlib.sha256(
                json.dumps(public, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "query_answer_sha256": hashlib.sha256(
                json.dumps(
                    private["query_answers"],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
        }

report = {
    "schema": "83ca9df09514-duplicate-precedence-adversarial-v1",
    "status": "passed",
    "surfaces": {
        "guarded_rule_materialization": {
            "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "alternate_sha256": hashlib.sha256(alternate.encode()).hexdigest(),
            "unified_diff": list(
                difflib.unified_diff(
                    canonical.splitlines(),
                    alternate.splitlines(),
                    fromfile="rightmost_wins.rkt",
                    tofile="leftmost_wins.rkt",
                    lineterm="",
                )
            ),
            "tamper_rejections": rejections,
        },
        "sampler_and_lesson_boundaries": {
            "paired_inputs": True,
            "input_count": 16,
            "distinct_input_count": len(set(fingerprints)),
            "all_inputs_separate_settings_in_racket": True,
            "key_rows_with_conflicts_per_input": conflict_rows,
            "dimensions": [[len(grid), len(grid[0])] for grid in inputs0],
            "boundary_episodes": boundary_episodes,
        },
    },
    "limits": [
        "bounded to paired seed block 0 and the two declared settings",
        "sampler boundary uses 8 demonstrations plus 8 queries; configured maximums are tested",
        "does not test arbitrary Racket mutations or universal program identifiability",
    ],
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))

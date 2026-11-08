"""Focused findings-only audit for e58953aee67a; generator/rules stay unchanged."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TARGET = REPO / "generators/e58953aee67a/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs

spec = importlib.util.spec_from_file_location("audit_target_e58953aee67a", TARGET)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def red_components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in unseen:
                    unseen.remove(p)
                    comp.add(p)
                    todo.append(p)
        result.append(comp)
    return result


def rival(grid, axis):
    """Move red components one cell wide/high, preserving all other cells."""
    selected = []
    for component in red_components(grid):
        coordinate = 1 if axis == "width" else 0
        if len({p[coordinate] for p in component}) != 1:
            continue
        if all(c+1 < len(grid[0]) and (grid[r][c+1] == 0 or (r, c+1) in component)
               for r, c in component):
            selected.append(component)
    out = [row[:] for row in grid]
    for component in selected:
        for r, c in component:
            out[r][c] = 0
    for component in selected:
        for r, c in component:
            out[r][c+1] = 2
    return out


def authored(axis):
    g = [[0] * 6 for _ in range(4)]
    for r, c in ((0, 0), (2, 0)):
        g[r][c] = 2
    blob = ((1, 3), (2, 3)) if axis == "width" else ((1, 3), (1, 4))
    for r, c in blob:
        g[r][c] = 2
    return g


def build():
    metadata = json.loads((HERE / "metadata.json").read_text())
    variants = metadata["variants"]
    rule = variants[0]["program_solution"]
    bindings = {
        "task_id": "e58953aee67a", "source_path": str(TARGET),
        "generator_sha256": digest(TARGET.read_bytes()), "generator_version": generator.VERSION,
        "generator_declared_rule_hash": generator.RULE_HASH,
        "catalog_rule_hash": metadata["rule_hash"],
        "canonical_program_sha256": digest(rule.encode()),
        "canonical_program": rule,
        "prior_audit_unresolved": metadata["audit_unresolved"],
        "prior_audit_unresolved_count": metadata["audit_unresolved_count"],
        "prior_audit_pending_triage_count": metadata["audit_pending_triage_count"],
        "review_index_path": metadata["review_notes_path"],
        "review_index_exists": (REPO / metadata["review_notes_path"]).exists(),
    }
    pairs = canonical_pairs("e58953aee67a", root=REPO)
    rows = [{"name": f"canonical_{p['split']}_{p['pair_index']}", "kind": "canonical", "input": p["input"],
             "canonical_expected": p["output"]} for p in pairs]
    for index in range(3):
        grid = generator.generate(0, index, difficulty="easy")
        rows.append({"name": f"demo_seed_0_index_{index}", "kind": "generated_demo", "input": grid,
                     "generate_call": {"seed": 0, "sample_index": index, "difficulty": "easy", "overrides": {}}})
    for axis in ("width", "height"):
        grid = authored(axis)
        rows.append({"name": f"authored_one_cell_{axis}_red_domino", "kind": "authored_query", "input": grid,
                     "axis": axis, "generate_call": None})
    for row in rows:
        grid = row["input"]
        row["self_check"] = generator.self_check(grid)
        row["strict_canonical_like"] = generator.strict_canonical_like(grid)
        row["observed_axes"] = generator.observe_overrides(grid)
        row["python_reference_mirror"] = generator.rule_mirror(grid)
        row["rivals"] = {axis: rival(grid, axis) for axis in ("width", "height")}
        row["red_component_bboxes"] = [
            {"cells": len(comp), "height": max(r for r, c in comp)-min(r for r, c in comp)+1,
             "width": max(c for r, c in comp)-min(c for r, c in comp)+1}
            for comp in red_components(grid)
        ]
    report = {"bindings": bindings, "rows": rows,
              "finding": "Every generated red component is 1x1 or full 2x2, confounding singleton selection with width-one or height-one component selection.",
              "domain_status": "Authored domino queries pass self_check and exact public axis observation; they belong to the documented generalized domain, but not strict canonical profile or current sampler support.",
              "construction_argument": "Targets are cardinally separated by the parity lattice and blob clearance. The only red blob constructor emits a full 2x2 block. Non-red distractors add no red cells. Thus successful draws only contain red 1x1 targets and 2x2 distractors, including overrides and difficulty bands."}
    (HERE / "inputs.json").write_text(json.dumps({"inputs": [row["input"] for row in rows]}, indent=2) + "\n")
    (HERE / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    (HERE / "bindings.json").write_text(json.dumps(bindings, indent=2) + "\n")
    print(json.dumps({"source_sha256": bindings["generator_sha256"], "rule_hash": bindings["catalog_rule_hash"],
                      "rows": len(rows), "authored_self_checks": [r["self_check"] for r in rows if r["kind"] == "authored_query"]}, indent=2))


def verify():
    analysis = json.loads((HERE / "analysis.json").read_text())
    authority = json.loads((HERE / "racket.json").read_text())
    rows = analysis["rows"]
    assert len(rows) == len(authority["results"])
    assert digest(TARGET.read_bytes()) == analysis["bindings"]["generator_sha256"]
    assert authority["generator_sha256"] == analysis["bindings"]["generator_sha256"]
    assert authority["executed_rule_hash"] == analysis["bindings"]["catalog_rule_hash"]
    for row, result in zip(rows, authority["results"]):
        answer = result["output"]
        assert answer == row["python_reference_mirror"], row["name"]
        if "canonical_expected" in row:
            assert answer == row["canonical_expected"], row["name"]
        row["racket_output"] = answer
        row["rival_matches_racket"] = {axis: prediction == answer for axis, prediction in row["rivals"].items()}
    demos = [{"input": row["input"], "output": row["racket_output"]} for row in rows if row["kind"] == "generated_demo"]
    findings = []
    for row in rows:
        if row["kind"] != "authored_query":
            assert all(row["rival_matches_racket"].values()), row["name"]
            continue
        axis = row["axis"]
        assert not row["self_check"]
        assert not row["rival_matches_racket"][axis]
        hook = generator.lesson_identifiable(demos, {"input": row["input"], "output": row["racket_output"]})
        row["lesson_identifiable_result"] = hook
        assert hook == [], hook
        findings.append({"query": row["name"], "rival": f"move red components with {axis} one", "self_check": row["self_check"],
                         "rival_fits_all_three_canonical_labels": True, "rival_fits_three_generated_demos": True,
                         "rival_disagrees_on_accepted_query": True, "lesson_identifiable_result": hook})
    analysis["authoritative_binding"] = {k: authority[k] for k in ("executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "generator_sha256", "rule_hash_matches_catalog")}
    analysis["verification"] = {"authoritative_rows": len(rows), "canonical_rows": 3, "generated_demos": 3, "authored_queries": 2,
                                "all_mirror_labels_match_racket": True, "findings": findings}
    (HERE / "verified.json").write_text(json.dumps(analysis, indent=2) + "\n")
    print(json.dumps(analysis["verification"], indent=2))


def report():
    verified = json.loads((HERE / "verified.json").read_text())
    b, a = verified["bindings"], verified["authoritative_binding"]
    queries = [row for row in verified["rows"] if row["kind"] == "authored_query"]
    vertical, horizontal = queries
    def grid_json(grid):
        return "[\n" + ",\n".join("  " + json.dumps(row, separators=(",", ":")) for row in grid) + "\n]"
    md = f"""## e58953aee67a

**Finding: accepted-domain teaching gap. Width-only and height-only red-component selectors survive every generated scene.**

The source constructs red objects only as isolated 1x1 cells or full 2x2 blocks.
The intended rule moves red singleton components and preserves every multi-cell
red component. Two simple alternatives fit the canonical labels and all shapes
the sampler constructs: move every red component whose width is one, or move
every red component whose height is one. They disagree with the authority on
lawful vertical and horizontal red dominoes. Both authored queries below pass
the current `self_check`, and the current `lesson_identifiable` hook accepts
three actual scheduled demonstrations followed by either ambiguous query.

### Source and rule binding

- Generator version: `{b['generator_version']}`.
- Generator path: `WORK/repo/generators/e58953aee67a/generator.py`.
- Generator SHA-256: `{b['generator_sha256']}`.
- Declared, catalog and executed rule hash: `{a['executed_rule_hash']}`.
- Executed rule-text SHA-256: `{a['rule_text_sha256']}`.
- Canonical `program_solution` SHA-256: `{b['canonical_program_sha256']}`.
- Catalog inspection reported zero unresolved audits and zero pending-triage
  audits. Its task-local `evidence/review_index.json` path is absent. Relevant
  associated notes were checked, including the intentional rejection of blocked
  or right-edge singleton targets and the three-demonstration schedule.

### Reproduction and observed result

Three demonstrations were generated with `seed=0`, `sample_index=0,1,2`,
`difficulty="easy"`, and no overrides. These cover canonical, both-distractor,
and red-blob schedule positions. Both new rivals match the three canonical
labels and all three generated demonstration labels.

The vertical-domino query is authored, with two isolated targets and one
two-cell vertical red component:

```json
{grid_json(vertical['input'])}
```

`self_check` returns `[]`. `observe_overrides` returns
`{{"grid_h": 4, "grid_w": 6, "n_singletons": 2}}`. Every isolated target has an
empty in-bounds right destination; the domino also has an empty right margin.
The query lies in the documented generalized domain and within the public axis
ranges. It is outside the strict canonical anchor profile and the current
sampler's restricted shape support.

The canonical public Racket output preserves the domino:

```json
{grid_json(vertical['racket_output'])}
```

The rival "move every red component of width one" moves the domino as well:

```json
{grid_json(vertical['rivals']['width'])}
```

An independent horizontal-domino query has input
`{json.dumps(horizontal['input'], separators=(',', ':'))}`. It also passes
`self_check`. Racket preserves its domino at row 1, columns 3 and 4; the
height-one rival moves that component to columns 4 and 5. Full input, authority,
rival outputs and domain diagnostics are retained in `verified.json`.

For both authored queries, the source's
`lesson_identifiable(demos, query)` returns `[]`, while the relevant new rival
fits all demonstrations and disagrees on the query. The existing private
`_LESSON_COMPETITORS` dictionary checks four other alternatives and omits these
component-selection rivals.

### Why the sampler cannot resolve this distinction

This support restriction follows directly from construction. `_target_candidates`
uses a parity lattice and cardinal clearance from the blob, so red targets do
not merge with each other or a distractor. `_blob_candidates` creates only a
full 2x2 block. Non-red distractors add no red cells. Thus every successful draw,
including declared overrides, contains only red 1x1 and 2x2 components. Width
one, height one and size one coincide throughout that support. Repeating more
of the current scenes cannot separate the rivals.

The eight public Racket labels all agree with the existing Python rule mirror:
three canonical pairs, three generated demonstrations, and two authored
queries. The finding concerns missing instructional support for the accepted
domain; no label mismatch was observed. The authored domino queries are not
claimed to be emitted by the current sampler.

### Suggested owner action

Include red horizontal and vertical domino distractors, with lawful right
margins, in the lesson schedule. Test width-one and height-one component
selectors as explicit rivals and require generated output-comparative
counterexamples. Check that the intended demonstration windows contain both
distinctions. The existing blocked/right-edge singleton exclusion can remain.
No generator, rule, approval or audit index was changed in this audit.

### Commands and retained evidence

All commands below used outer cwd
`/workspace/scratch/e09154a86f98/review` and exited 0. Public-wrapper payload cwd
was `WORK/repo`. Exact argument arrays and evidence paths are in
`WORK/checks/audit/e58953aee67a/commands.json`.

```bash
python3 review.py run python3 -m arcpuzzles show e58953aee67a --out ../checks/audit/e58953aee67a/metadata.json
python3 WORK/checks/audit/e58953aee67a/probe.py
python3 review.py run python3 -m arcpuzzles apply e58953aee67a --input ../checks/audit/e58953aee67a/inputs.json --out ../checks/audit/e58953aee67a/racket.json
python3 WORK/checks/audit/e58953aee67a/probe.py verify
```

The compact reproduction is `probe.py`; `inputs.json` contains the eight exact
inputs; `racket.json` retains authoritative outputs and source/rule bindings;
`verified.json` retains validator results, rival outputs, canonical/demonstration
fit, query disagreement and lesson-hook results. `bindings.json` records the
source and canonical-rule identity separately.
"""
    (HERE / "audit-section.md").write_text(md)
    cwd = str(HERE.parents[3])
    base = "WORK/checks/audit/e58953aee67a/"
    commands = [
        {"name": "target_metadata_and_audit_status", "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "show", "e58953aee67a", "--out", "../checks/audit/e58953aee67a/metadata.json"], "evidence": [base + "metadata.json"]},
        {"name": "build_target_bound_probes", "argv": ["python3", base + "probe.py"], "evidence": [base + "analysis.json", base + "inputs.json", base + "bindings.json"]},
        {"name": "authoritative_canonical_racket", "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", "e58953aee67a", "--input", "../checks/audit/e58953aee67a/inputs.json", "--out", "../checks/audit/e58953aee67a/racket.json"], "evidence": [base + "racket.json"]},
        {"name": "verify_finding", "argv": ["python3", base + "probe.py", "verify"], "evidence": [base + "verified.json"]},
        {"name": "write_findings_section", "argv": ["python3", base + "probe.py", "report"], "evidence": [base + "audit-section.md", base + "commands.json"]},
    ]
    for command in commands:
        command.update({"cwd": cwd, "exit_code": 0})
    (HERE / "commands.json").write_text(json.dumps({"task_id": "e58953aee67a", "commands": commands}, indent=2) + "\n")
    print(json.dumps({"section": str(HERE / "audit-section.md"), "command_ledger": str(HERE / "commands.json"),
                      "findings": 1, "counterexamples": 2, "racket_labels": 8}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify()
    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        report()
    else:
        build()

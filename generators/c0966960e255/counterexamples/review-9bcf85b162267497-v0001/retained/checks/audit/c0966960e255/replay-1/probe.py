"""One bounded, source-pinned symmetry-shortcut audit.

Run from the packet root:
  WORK/.venv-review/bin/python WORK/checks/audit/c0966960e255/run_audit.py

The driver uses public review.py/apply commands; no private reference runner.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path


TASK = "c0966960e255"
GENERATOR_SHA = "45df359d3e79a21762f9906ba590a6213d22741e7864924ef861939bda7e3694"
RULE_HASH = "4199c1ecbb19"
ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "generators" / TASK / "generator.py"


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    result = []
    while unseen:
        pending = [min(unseen)]
        unseen.remove(pending[0])
        cells = []
        for r, c in pending:
            cells.append((r, c))
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    pending.append(p)
        result.append(cells)
    return result


def top_bottom(cells):
    rows = [r for r, _ in cells]
    total = min(rows) + max(rows)
    points = set(cells)
    return {(total - r, c) for r, c in points} == points


def left_right(cells):
    cols = [c for _, c in cells]
    total = min(cols) + max(cols)
    points = set(cells)
    return {(r, total - c) for r, c in points} == points


def rival(grid):
    """Recolor a red component iff it is not top-bottom symmetric."""
    output = copy.deepcopy(grid)
    for cells in components(grid):
        if not top_bottom(cells):
            for r, c in cells:
                output[r][c] = 3
    return output


def load_subject():
    actual = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert actual == GENERATOR_SHA, (actual, GENERATOR_SHA)
    spec = importlib.util.spec_from_file_location("audited_c0966960e255", SOURCE)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    assert gen.RULE_HASH == RULE_HASH
    return gen


def prepare():
    gen = load_subject()
    seed = 20261008
    calls = [dict(seed=seed, sample_index=i, difficulty="easy", overrides={}) for i in range(4)]
    generated = [gen.generate(seed, i, difficulty="easy") for i in range(4)]
    for grid in generated:
        assert gen.self_check(grid) == []
        assert rival(grid) == gen.rule_mirror(grid)

    # Change one 3x3 selected component into a plus. The other selected
    # component retains the same-size and LR-only contrast controls.
    donor = generated[3]
    selected = next(cells for cells in components(donor) if left_right(cells))
    top = min(r for r, _ in selected)
    left = min(c for _, c in selected)
    query = copy.deepcopy(donor)
    for r, c in selected:
        query[r][c] = 0
    plus = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    for r, c in plus:
        assert query[top + r][left + c] in {0, 2}
        query[top + r][left + c] = 2
    assert gen.self_check(query) == []
    assert gen.strict_canonical_like(query) == []
    assert gen.observe_overrides(query) == gen.observe_overrides(donor)
    assert all(witness(query) for witness in gen.SEMANTIC_WITNESSES.values())
    assert rival(query) != gen.rule_mirror(query)

    # This is the complete fixed template family, including each allowed
    # vertical flip and its contrast rotation, not a seed search.
    grammar_checks = []
    for index, template in enumerate(gen._LR_ONLY_PATTERNS):
        for flipped in (False, True):
            selected_shape = gen._flip_vertical(template) if flipped else template
            unselected_shape = gen._rotate_once(selected_shape)
            assert left_right(selected_shape) and not top_bottom(selected_shape)
            assert not left_right(unselected_shape) and top_bottom(unselected_shape)
            grammar_checks.append(dict(template=index, vertical_flip=flipped))

    canonical = canonical_pairs(TASK, root=ROOT)
    canonical_rival_matches = sum(rival(pair["input"]) == pair["output"] for pair in canonical)
    rule_hashes = set()
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = " ".join(row["program_solution"].split())
                rule_hashes.add(hashlib.sha256(program.encode()).hexdigest()[:12])
    assert rule_hashes == {RULE_HASH}

    inputs = generated[:3] + [query]
    write_json("input.json", inputs)
    write_json("rival.json", [rival(grid) for grid in inputs])
    write_json("python-mirror.json", [gen.rule_mirror(grid) for grid in inputs])
    write_json("source-hashes.json", {
        "task_id": TASK,
        "generator_sha256": GENERATOR_SHA,
        "rule_hash": RULE_HASH,
        "generator_path": str(SOURCE.relative_to(ROOT)),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    write_json("witness.json", {
        "task_id": TASK,
        "generator_sha256": GENERATOR_SHA,
        "rule_hash": RULE_HASH,
        "rival_name": "recolor_unless_top_bottom_symmetric",
        "classification": "reproduced distribution shortcut; not a canonical-fit rival",
        "generated_calls": calls,
        "input_order": ["demo0", "demo1", "demo2", "query_mutated_from_sample3"],
        "query_mutation": {
            "donor_input_sha256": digest(donor),
            "remove_red_cells": selected,
            "add_red_cells": [(top + r, left + c) for r, c in plus],
            "description": "Replace the first selected 3x3 component with a five-cell cross at the same bounding-box origin.",
        },
        "observed_query_axes": gen.observe_overrides(query),
        "query_self_check": gen.self_check(query),
        "query_strict_canonical_like": gen.strict_canonical_like(query),
        "query_semantic_witnesses": {name: witness(query) for name, witness in gen.SEMANTIC_WITNESSES.items()},
        "query_belongs_to_documented_grammar": True,
        "query_is_unmodified_generate_output": False,
        "canonical_rival_matches": canonical_rival_matches,
        "canonical_pairs_checked": len(canonical),
        "complete_template_pairs_checked": grammar_checks,
        "input_sha256": [digest(grid) for grid in inputs],
    })
    print(json.dumps({"prepared_inputs": len(inputs), "canonical_rival_matches": canonical_rival_matches,
                      "canonical_pairs": len(canonical), "template_pairs": len(grammar_checks)}))


def verify():
    gen = load_subject()
    result = json.loads((OUT / "racket.json").read_text())
    write_json("racket-top-level-keys.json", list(result) if isinstance(result, dict) else {"type": type(result).__name__})
    print(json.dumps({"racket_result_type": type(result).__name__,
                      "keys": list(result) if isinstance(result, dict) else None}))


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()

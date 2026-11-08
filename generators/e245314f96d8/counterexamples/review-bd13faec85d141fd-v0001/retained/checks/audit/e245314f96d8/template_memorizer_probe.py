#!/usr/bin/env python3
"""Demonstrate a finite-template shortcut over e245314f96d8's full sampler.

The rival never constructs a contact graph or counts degree.  It memorizes the
binary occupancy/output masks of the four fixed scene morphologies (chain,
two stars, all_degrees), augmented by D4 transforms, then normalizes translation
and ignores input colors.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
GEN_PATH = REPO / "generators" / "e245314f96d8" / "generator.py"
for p in (REPO / "shared" / "runtime", REPO / "src"):
    sys.path.insert(0, str(p))

spec = importlib.util.spec_from_file_location("audit_e245", GEN_PATH)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def crop_pair(inp, out):
    cells = [(r, c) for r, row in enumerate(inp) for c, v in enumerate(row) if v]
    top = min(r for r, _ in cells); bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells); right = max(c for _, c in cells)
    binary = [[1 if inp[r][c] else 0 for c in range(left, right + 1)] for r in range(top, bottom + 1)]
    labels = [[out[r][c] if inp[r][c] else 0 for c in range(left, right + 1)] for r in range(top, bottom + 1)]
    return binary, labels, (top, left)


def rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def d4(grid):
    for reflected in (False, True):
        current = flip_lr(grid) if reflected else copy.deepcopy(grid)
        for _ in range(4):
            yield current
            current = rot90(current)


def key(grid):
    return tuple(tuple(row) for row in grid)


def add_template(table, inp, out):
    binary, labels, _ = crop_pair(inp, out)
    for b, lab in zip(d4(binary), d4(labels)):
        k = key(b)
        v = key(lab)
        prior = table.get(k)
        if prior is not None and prior != v:
            raise AssertionError("occupancy symmetry maps to conflicting memorized labels")
        table[k] = v


def predict(table, inp):
    dummy = [[0 for _ in row] for row in inp]
    binary, _, (top, left) = crop_pair(inp, dummy)
    labels = table.get(key(binary))
    if labels is None:
        return None
    out = [[0 for _ in row] for row in inp]
    for dr, row in enumerate(labels):
        for dc, value in enumerate(row):
            if value:
                out[top + dr][left + dc] = value
    return out


def main():
    # Four occupancy morphologies exhaust the generator: chain, star-train,
    # star-test, and all_degrees.  D4 augmentation handles its transform axis.
    training_specs = [
        ("chain", "easy", 11),
        ("star_train", "easy", 12),
        ("star_test", "hard", 13),
        ("all_degrees", "medium", 14),
    ]
    table = {}
    training = []
    for name, band, seed in training_specs:
        profile = "star" if name.startswith("star_") else name
        grid = GEN.generate(seed, 0, difficulty=band, scene_profile=profile)
        target = GEN.rule_mirror(grid)
        add_template(table, grid, target)
        training.append({"name": name, "band": band, "seed": seed, "input_hash": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()})

    total = exact = unknown = 0
    unique_inputs = set()
    unique_normalized_masks = set()
    first_failure = None
    per_band = {}
    for band in ("easy", "medium", "hard"):
        row = {"tested": 0, "exact": 0, "unknown": 0}
        for seed in range(100):
            for profile in GEN.SCENE_PROFILES:
                sample_index = seed * 3 + GEN.SCENE_PROFILES.index(profile)
                grid = GEN.generate(10000 + seed, sample_index, difficulty=band, scene_profile=profile)
                expected = GEN.rule_mirror(grid)
                predicted = predict(table, grid)
                total += 1; row["tested"] += 1
                unique_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
                binary, _, _ = crop_pair(grid, expected)
                unique_normalized_masks.add(key(binary))
                if predicted is None:
                    unknown += 1; row["unknown"] += 1
                    if first_failure is None:
                        first_failure = {"band": band, "seed": seed, "profile": profile, "kind": "unknown_template"}
                elif predicted == expected:
                    exact += 1; row["exact"] += 1
                elif first_failure is None:
                    first_failure = {"band": band, "seed": seed, "profile": profile, "kind": "wrong_output", "input": grid, "expected": expected, "predicted": predicted}
        per_band[band] = row

    result = {
        "schema": "arcpuzzles-audit-template-shortcut-v1",
        "task_id": GEN.TASK_ID,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "rule_hash": GEN.RULE_HASH,
        "shortcut": "translation/color-invariant lookup over four fixed binary scene templates with D4 augmentation",
        "shortcut_uses_contact_graph_or_degree": False,
        "training_templates": training,
        "stored_d4_keys": len(table),
        "tested": total,
        "exact": exact,
        "unknown": unknown,
        "accuracy": exact / total,
        "unique_inputs": len(unique_inputs),
        "unique_normalized_masks_observed": len(unique_normalized_masks),
        "per_band": per_band,
        "first_failure": first_failure,
        "domain_statement": "All ordinary scene_profile overrides across easy/medium/hard, 100 deterministic seeds per profile and band.",
        "limitation": "The probe demonstrates a sampler shortcut, not an error in the selected Racket rule. A novel contact topology outside the four memorized occupancy templates is intentionally untested and may fail.",
    }
    out = Path(__file__).with_name("template_memorizer_result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("tested", "exact", "unknown", "accuracy", "unique_inputs", "stored_d4_keys")}, sort_keys=True))
    return 0 if exact == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

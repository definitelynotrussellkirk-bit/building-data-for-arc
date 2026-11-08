#!/usr/bin/env python3
"""Verify sequential public projections and hidden-field invariance."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TASK_ID = 'public_eval_da515329'


def load_adapter():
    path = BASE / "adapter.py"
    key = "_export_audit_" + TASK_ID + "_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def raw(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value) -> str:
    return hashlib.sha256(raw(value)).hexdigest()


def mutate_cell(grid):
    out = copy.deepcopy(grid)
    out[0][0] = (out[0][0] + 1) % 10
    return out


def audit() -> dict:
    adapter = load_adapter()
    rows = []
    view_count = hidden_mutations = positive_controls = 0
    for seed in (0, 17, 43, 97):
        for setting in adapter.SETTINGS:
            for demos in (2, 6):
                episode = adapter.generate(seed, dict(setting), demos, 4)
                bank_hashes = [digest(pair["input"]) for pair in episode["private_query_bank"]]
                if len(set(bank_hashes)) != 4:
                    raise AssertionError("private query bank contains duplicate inputs")
                firsts = set()
                for presentation_seed in range(8):
                    sequence = []
                    views = []
                    for turn in range(4):
                        view = adapter.public_view(episode, turn=turn, presentation_seed=presentation_seed)
                        if set(view) != {"train", "test"} or len(view["test"]) != 1:
                            raise AssertionError("public view schema mismatch")
                        if set(view["test"][0]) != {"input"}:
                            raise AssertionError("query answer or metadata leaked")
                        if view["train"] != episode["train"]:
                            raise AssertionError("demonstrations changed in public projection")
                        encoded = raw(view)
                        for forbidden in (b'program_solution', b'private_query_bank', b'"settings"', b'"seed"'):
                            if forbidden in encoded:
                                raise AssertionError(f"private field leaked: {forbidden!r}")
                        sequence.append(digest(view["test"][0]["input"]))
                        views.append(view)
                        view_count += 1
                    if set(sequence) != set(bank_hashes) or len(sequence) != 4:
                        raise AssertionError("presentation does not reveal each private query exactly once")
                    firsts.add(sequence[0])
                    baseline = raw(views[0])

                    # Settings, rule bytes, seed, and every answer are private.
                    hidden = copy.deepcopy(episode)
                    hidden["settings"] = {"private_mutation": True}
                    hidden["program_solution"] = "private-mutated-program"
                    hidden["seed"] = seed + 999_999
                    for split in ("train", "test", "private_query_bank"):
                        for pair in hidden[split]:
                            if "output" in pair:
                                pair["output"] = [[9]]
                    # Train answers are intentionally visible, so restore them; query answers stay mutated.
                    hidden["train"] = copy.deepcopy(episode["train"])
                    if raw(adapter.public_view(hidden, turn=0, presentation_seed=presentation_seed)) != baseline:
                        raise AssertionError("private metadata or answers changed visible first turn")
                    hidden_mutations += 1

                    selected = sequence[0]
                    for index, pair in enumerate(episode["private_query_bank"]):
                        if digest(pair["input"]) == selected:
                            continue
                        changed = copy.deepcopy(episode)
                        changed["private_query_bank"][index]["input"] = mutate_cell(pair["input"])
                        if raw(adapter.public_view(changed, turn=0, presentation_seed=presentation_seed)) != baseline:
                            raise AssertionError("future query input leaked into first turn")
                        hidden_mutations += 1

                    changed = copy.deepcopy(episode)
                    selected_index = next(i for i, pair in enumerate(changed["private_query_bank"])
                                          if digest(pair["input"]) == selected)
                    changed["private_query_bank"][selected_index]["input"] = mutate_cell(
                        changed["private_query_bank"][selected_index]["input"])
                    if raw(adapter.public_view(changed, turn=0, presentation_seed=presentation_seed)) == baseline:
                        raise AssertionError("positive control did not change visible selected query")
                    positive_controls += 1
                    rows.append({
                        "seed": seed,
                        "settings": setting,
                        "demos": demos,
                        "presentation_seed": presentation_seed,
                        "query_sequence": sequence,
                    })
                if len(firsts) < 2:
                    raise AssertionError("presentation seed never changes first query")
    return {
        "schema": "arcpuzzles-public-projection-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "views": view_count,
        "hidden_field_mutations": hidden_mutations,
        "positive_controls": positive_controls,
        "rows": rows,
        "limits": "Projection and invariance checks only; no owner acceptance or training admission.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit()
    text = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()

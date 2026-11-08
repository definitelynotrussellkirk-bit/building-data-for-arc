"""Reproducible, bounded protected-Racket teaching audit and example writer.

Run through review.py; use a fresh --out directory. This tool writes authoring
evidence, not acceptance records. It never treats a rival error as rejection.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def load_adapter():
    spec = importlib.util.spec_from_file_location("_audited_order_adapter", HOME / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(program, old, new):
    if program.count(old) != 1:
        raise ValueError(f"rival mutation no longer has a unique target: {old}")
    return program.replace(old, new)


def rivals(adapter, settings):
    program = adapter.program(settings)
    decoder = "(if (zero? (at g 0 s)) 1 2)"
    types = ("(map piece-type pieces)" if settings["read_order"] == "forward"
             else "(reverse (map piece-type pieces))")
    return {
        "opposite_order": adapter.program({"read_order": "reverse" if settings["read_order"] == "forward" else "forward"}),
        "top_right_decoder": replace_once(program, decoder, "(if (zero? (at g 0 e)) 2 1)"),
        "top_right_same_polarity": replace_once(program, decoder, "(if (zero? (at g 0 e)) 1 2)"),
        "any_upper_zero": replace_once(program, decoder,
            "(if (or (zero? (at g 0 s)) (zero? (at g 0 e))) 1 2)"),
        "bottom_left_decoder": replace_once(program, decoder, "(if (zero? (at g 1 s)) 1 2)"),
        "swapped_turns": replace_once(program, decoder, "(if (zero? (at g 0 s)) 2 1)"),
        "all_bends_left": replace_once(program, decoder, "1"),
        "all_bends_right": replace_once(program, decoder, "2"),
        "reset_column": replace_once(program, "(cur (third state))", "(cur 3)"),
        "reset_row": replace_once(program, "(row (second state))", "(row 1)"),
        "unit_straight_advance": replace_once(program, "(+ row 2)", "(+ row 1)"),
        "skip_first_symbol": replace_once(program, f"(types {types})", f"(types (rest {types}))"),
    }


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run(output):
    if output.exists():
        raise FileExistsError("choose a fresh audit destination")
    adapter = load_adapter()
    started = time.monotonic()
    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("the teaching audit requires protected Racket")
    wrapped, cache = {}, {}

    def execute(program, grid):
        key = (program, json.dumps(grid))
        if key not in cache:
            wrapped.setdefault(program, wrap_rule(program))
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            result = bridge.eval_text(f"({wrapped[program]} {literal})")
            # The public serializer's strict grid contract rejects bools/floats,
            # ragged outputs and out-of-range values before we compare labels.
            public_challenge_bytes({"train": [{"input": grid, "output": result}],
                                    "test": [{"input": grid}]})
            cache[key] = result
        return cache[key]

    records, examples, rival_sources, public_files, turn_files = [], [], {}, {}, {}
    try:
        for order in adapter.ORDERS:
            settings = {"read_order": order}
            programs = rivals(adapter, settings)
            rival_sources[order] = {name: {"program": text, "sha256": sha(text.encode())}
                                    for name, text in programs.items()}
            for seed, demos in ((0, 2), (1, 2), (2, 2), (167, 6)):
                episode = adapter.generate(seed, settings, demos, 4)
                chosen = adapter.program(settings)
                for split in ("train", "test"):
                    for pair in episode[split]:
                        actual = execute(chosen, pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError(f"Python/Racket label mismatch: {order}/{seed}/{split}")
                        pair["output"] = actual
                eliminated = {}
                for name, rival in programs.items():
                    demo_outputs = [execute(rival, p["input"]) for p in episode["train"]]
                    query_outputs = [execute(rival, p["input"]) for p in episode["test"]]
                    distinguishers = [i for i, (p, value) in enumerate(zip(episode["train"], demo_outputs))
                                      if p["output"] != value]
                    if not distinguishers:
                        raise AssertionError(f"uneliminated declared rival: {order}/{seed}/{name}")
                    first = distinguishers[0]
                    eliminated[name] = {"distinguishing_demo": first,
                        "input": episode["train"][first]["input"],
                        "output": episode["train"][first]["output"],
                        "rival_output": demo_outputs[first],
                        "query_disagreements": [i for i, (p, value) in enumerate(zip(episode["test"], query_outputs))
                                                if p["output"] != value]}
                first, second = episode["train"][:2]
                parse = adapter._source()._parse
                t1 = sorted(p[2] for p in parse(first["input"])[0])
                t2 = sorted(p[2] for p in parse(second["input"])[0])
                if t1 != t2 or first["output"] == second["output"]:
                    raise AssertionError("count-only teaching contrast missing")
                one = adapter.generate(seed, settings, demos, 1)
                if adapter.public_turn(episode, 0) != adapter.public_turn(one, 0):
                    raise AssertionError("multi-query first turn differs from single-query evaluation")
                visible = public_challenge_bytes(episode)
                public_id = public_challenge_id(episode)
                if public_id in public_files:
                    raise AssertionError("duplicate visible episode")
                public_files[public_id] = visible
                for index in range(4):
                    turn = adapter.public_turn(episode, index)
                    turn_files[sha(turn)] = turn
                examples.append({"public_id": public_id, "seed": seed, **episode})
                records.append({"settings": settings, "seed": seed, "demos": demos, "queries": 4,
                    "input_shape": [2, 12], "output_shape": [8, 7],
                    "labels_checked": demos + 4, "eliminated_rivals": eliminated,
                    "equal_counts_different_paths": True, "first_turn_equal_to_single_query": True})
    finally:
        bridge.close()

    # Cheap bounded reliability, without pretending these additional Python
    # draws were independently Racket-labelled.
    reliability = {"attempted": 0, "successful": 0, "label_basis": "Python claims; protected cases above"}
    for seed in range(24):
        for order in adapter.ORDERS:
            for demos in (2, 3, 6):
                reliability["attempted"] += 1
                episode = adapter.generate(seed, {"read_order": order}, demos, 4)
                keys = [json.dumps(p["input"]) for split in ("train", "test") for p in episode[split]]
                if len(keys) != len(set(keys)):
                    raise AssertionError("reliability draw repeats an input")
                reliability["successful"] += 1
    sources = [ROOT / "generators/f0f2806877da/generator.py", *sorted(HOME.glob("*.py")),
               *sorted(HOME.glob("*.rkt")), HOME / "promotion.json"]
    report = {"schema": "arcpuzzles-f0f2806877da-teaching-audit-v1", "status": "passed",
        "source_hashes": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources},
        "racket": identity, "racket_evaluations": len(cache), "episodes": records,
        "reliability": reliability, "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": "Twelve declared executable rivals plus same-command-count contrast; no universal uniqueness. Exact 2x12-to-8x7 grammar, no lawful 30x30 stress. Canonical sampler unchanged; its old shortcut finding stays open.",
        "training_admitted": False, "owner_acceptance": "not_performed"}
    output.mkdir(parents=True)
    write_json(output / "audit.json", report)
    write_json(output / "rivals.private.json", rival_sources)
    write_json(output / "examples.private.json", examples)
    for folder, files in (("public", public_files), ("turns", turn_files)):
        (output / folder).mkdir()
        for identity, data in sorted(files.items()):
            (output / folder / f"{identity}.json").write_bytes(data)
    print(json.dumps({"status": "passed", "racket_evaluations": len(cache),
                      "episodes": len(records), "rivals_per_episode": 12,
                      "sampler_success": reliability, "out": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)

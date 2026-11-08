#!/usr/bin/env python3
"""Bounded private Racket verification and public projection for this prototype.

Run through review.py's bundled-Racket wrapper. This is authoring evidence,
not native qualification or owner acceptance. public/ holds controller-side
multiquery challenges; expose only one turns/ challenge at a time to a model.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "85de426e8683"


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False, ensure_ascii=False) + "\n").encode()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def load_adapter():
    path = HERE / "adapter.py"
    body = path.read_bytes()
    name = "_arc_85de_parametric_" + digest(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def source_hashes():
    sources = [HERE.parents[1] / "generator.py"]
    sources += [p for p in sorted(HERE.rglob("*"))
                if p.is_file() and p.suffix in {".py", ".rkt", ".json"}
                and not any(part in {"evidence", "examples", "__pycache__"}
                            for part in p.relative_to(HERE).parts)]
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sources}


def content_summary(grid, adapter):
    h, w = len(grid), len(grid[0])
    occupied = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    targets = adapter.target_components(grid)
    gray = sum(value == 5 for row in grid for value in row)
    return {
        "shape": [h, w], "target_count": len(targets),
        "gray_cells": gray, "gray_nontarget_cells": gray - 3 * len(targets),
        "nongray_distractor_cells": sum(value not in (0, 5) for row in grid for value in row),
        "nonzero_cells": len(occupied), "density": len(occupied) / (h * w),
        "occupied_quadrants": sorted({(2 * r // h) * 2 + (2 * c // w) for r, c in occupied}),
        "touches_boundary": any(r in (0, h - 1) or c in (0, w - 1) for r, c in occupied),
        "occupied_bbox": ([min(r for r, c in occupied), min(c for r, c in occupied),
                            max(r for r, c in occupied), max(c for r, c in occupied)]
                           if occupied else None),
        "colors": sorted({value for row in grid for value in row}),
    }


def verify(output, *, seeds, demos, queries):
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    if output.exists():
        raise FileExistsError(f"Refusing existing output: {output}")
    if type(demos) is not int or type(queries) is not int or not 2 <= demos <= 6 or not 1 <= queries <= 4:
        raise ValueError("Support is 2..6 demos and 1..4 queries independently")
    if not isinstance(seeds, (list, tuple)) or not 1 <= len(seeds) <= 8 or any(type(s) is not int or not 0 <= s < 2**63 for s in seeds):
        raise ValueError("Use 1..8 distinct exact integer seeds in 0..2**63-1")
    if len(set(seeds)) != len(seeds):
        raise ValueError("Duplicate seeds are not an independent bounded check")
    output.mkdir(parents=True)
    failures, records, public_rows = [], [], []
    initial_hashes = source_hashes()
    report = {"schema": "85de426e8683-bounded-parametric-verification-v1",
              "task_id": TASK_ID, "seeds": seeds, "demos": demos, "queries": queries,
              "source_sha256": initial_hashes, "training_admitted": False,
              "native_qualification": False, "failures": failures,
              "projection": "public/ is controller-only; turns/ contains one query input per challenge, no count hints. First-turn bytes equal a single-query projection.",
              "scope": "Finite seeds/settings and declared rivals only; no universal identifiability or learning-benefit claim."}
    runtime = ROOT / "shared/runtime"
    evaluations = 0
    bridge = None
    try:
        with _local_imports(runtime, HERE):
            from reviewer_support import public_challenge_bytes, public_challenge_id
            adapter = load_adapter()
            settings_space = tuple(copy.deepcopy(adapter.SETTINGS))
            if settings_space != ({"ink_rule": "fixed_yellow"}, {"ink_rule": "target_parity"}):
                raise ValueError("Unexpected task parameter space")
            report["attempted_episode_count"] = len(seeds) * len(settings_space)
            apply, identity, bridge = _real_evaluator(runtime)
            report["racket"] = identity
            matched_inputs = {}
            seen_public = set()

            def execute(program, grid, context):
                nonlocal evaluations
                evaluations += 1
                try:
                    return _grid(apply(program, copy.deepcopy(grid)))
                except Exception as exc:
                    failures.append({"kind": "racket_error", "context": context,
                                     "error": f"{type(exc).__name__}: {exc}"})
                    return None

            for seed in seeds:
                for settings in settings_space:
                    episode = adapter.generate(seed, copy.deepcopy(settings), demos, queries)
                    selected = adapter.program(copy.deepcopy(settings))
                    if episode.get("program_solution") != selected:
                        failures.append({"kind": "program_mismatch", "seed": seed, "settings": settings})
                    splits = {}
                    for split, count in (("train", demos), ("test", queries)):
                        pairs = episode.get(split)
                        if not isinstance(pairs, list) or len(pairs) != count:
                            raise ValueError(f"Wrong {split} count for seed {seed}: expected {count}")
                        splits[split] = [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in pairs]
                    inputs = [pair["input"] for split in ("train", "test") for pair in splits[split]]
                    serialized = [raw(grid) for grid in inputs]
                    if len(serialized) != len(set(serialized)):
                        failures.append({"kind": "duplicate_input", "seed": seed, "settings": settings})
                    prior = matched_inputs.setdefault(seed, serialized)
                    if prior != serialized:
                        failures.append({"kind": "setting_input_mismatch", "seed": seed, "settings": settings})

                    programs = {"setting:" + raw(s).decode().strip(): adapter.program(copy.deepcopy(s))
                                for s in settings_space}
                    optional = getattr(adapter, "rival_programs", None)
                    if callable(optional):
                        programs.update({"shortcut:" + name: program for name, program in optional(settings).items()})
                    if any(type(p) is not str or not p.strip() for p in programs.values()):
                        raise ValueError("Every finite setting/rival must provide nonempty Racket source")
                    candidates = []
                    for name, program in programs.items():
                        demo_outputs = [execute(program, p["input"], {"seed": seed, "settings": settings,
                                        "program": name, "split": "train", "pair": i})
                                        for i, p in enumerate(splits["train"])]
                        fits = all(got == pair["output"] for got, pair in zip(demo_outputs, splits["train"]))
                        candidates.append({"name": name, "program": program, "fits_demonstrations": fits,
                                           "demonstration_outputs": demo_outputs})
                    selected_names = [c["name"] for c in candidates if c["program"] == selected]
                    if not selected_names or any(not c["fits_demonstrations"] for c in candidates if c["program"] == selected):
                        failures.append({"kind": "selected_demo_label_mismatch", "seed": seed, "settings": settings})
                    setting_survivors = [c["name"] for c in candidates if c["name"].startswith("setting:") and c["fits_demonstrations"]]
                    if len(setting_survivors) != 1:
                        failures.append({"kind": "finite_setting_ambiguity", "seed": seed, "settings": settings,
                                         "survivors": setting_survivors})
                    per_query = []
                    for i, pair in enumerate(splits["test"]):
                        actual = execute(selected, pair["input"], {"seed": seed, "settings": settings, "split": "test", "pair": i})
                        if actual != pair["output"]:
                            failures.append({"kind": "query_label_mismatch", "seed": seed, "settings": settings, "pair": i})
                        rival_outputs = {c["name"]: execute(c["program"], pair["input"],
                                         {"seed": seed, "settings": settings, "program": c["name"], "split": "test", "pair": i})
                                         for c in candidates if c["fits_demonstrations"] and c["program"] != selected}
                        disagreements = [name for name, got in rival_outputs.items() if got != actual]
                        if disagreements:
                            failures.append({"kind": "surviving_rival_disagreement", "seed": seed,
                                             "settings": settings, "pair": i, "rivals": disagreements})
                        per_query.append({"index": i, "racket_output": actual,
                                          "surviving_rival_outputs": rival_outputs,
                                          "surviving_query_disagreements": disagreements})
                    teaching = adapter.lesson_report({**episode, **splits}, settings)
                    if teaching.get("surviving_query_disagreements"):
                        failures.append({"kind": "mirror_rival_disagreement", "seed": seed,
                                         "settings": settings, "rivals": teaching["surviving_query_disagreements"]})
                    public = {"train": splits["train"], "test": [{"input": p["input"]} for p in splits["test"]]}
                    body = public_challenge_bytes(public)
                    public_id = public_challenge_id(public)
                    if public_id in seen_public:
                        failures.append({"kind": "duplicate_visible_payload", "public_id": public_id})
                    seen_public.add(public_id)
                    turns = []
                    for pair in splits["test"]:
                        turn = {"train": splits["train"], "test": [{"input": pair["input"]}]}
                        turns.append(public_challenge_bytes(turn))
                    single_query = adapter.generate(seed, copy.deepcopy(settings), demos, 1)
                    first_invariant = turns[0] == public_challenge_bytes(single_query)
                    if not first_invariant:
                        failures.append({"kind": "first_turn_differs_from_single_query", "seed": seed, "settings": settings})
                    coverage = [content_summary(grid, adapter) for grid in inputs]
                    if queries == 4 and not any(c["shape"] == [30, 30] for c in coverage):
                        failures.append({"kind": "missing_30x30_stress", "seed": seed, "settings": settings})
                    records.append({"public_id": public_id, "seed": seed, "settings": settings,
                                    **splits, "program": selected, "program_sha256": digest(selected.encode()),
                                    "racket": identity, "finite_rivals": candidates,
                                    "queries": per_query, "mirror_teaching_report": teaching,
                                    "content_coverage": coverage,
                                    "first_turn_equals_single_query": first_invariant})
                    public_rows.append((public_id, body, turns))
    except Exception as exc:
        failures.append({"kind": "verification_error", "error": f"{type(exc).__name__}: {exc}"})
    finally:
        if bridge is not None:
            bridge.close()
    if source_hashes() != initial_hashes:
        failures.append({"kind": "source_changed_during_verification"})
    records.sort(key=lambda row: row["public_id"])
    (output / "private.jsonl").write_bytes(b"".join(raw(row) for row in records))
    # Never publish duplicate or partial public batches; private failures remain reviewable.
    if not failures:
        (output / "public").mkdir()
        (output / "turns").mkdir()
        index = []
        for public_id, body, turns in sorted(public_rows):
            (output / "public" / (public_id + ".json")).write_bytes(body)
            turn_ids = []
            for turn_body in turns:
                turn_id = digest(turn_body)
                (output / "turns" / (turn_id + ".json")).write_bytes(turn_body)
                turn_ids.append(turn_id)
            index.append({"public_id": public_id, "turn_ids": turn_ids})
        (output / "controller.private.json").write_bytes(raw(index))
        (output / "public.jsonl").write_bytes(b"".join(body for _, body, _ in sorted(public_rows)))
    report.update({"status": "passed" if not failures else "failed", "episode_count": len(records),
                   "failed_findings": len(failures),
                   "racket_evaluations": evaluations,
                   "public_ids": sorted(row["public_id"] for row in records),
                   "files": {p.relative_to(output).as_posix(): digest(p.read_bytes())
                             for p in sorted(output.rglob("*")) if p.is_file()}})
    (output / "report.json").write_bytes(raw(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--demos", type=int, default=3, choices=range(2, 7))
    parser.add_argument("--queries", type=int, default=4, choices=range(1, 5))
    args = parser.parse_args(argv)
    result = verify(args.out, seeds=args.seed or [0, 17], demos=args.demos, queries=args.queries)
    print(json.dumps({k: result[k] for k in ("status", "episode_count", "racket_evaluations", "failed_findings")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

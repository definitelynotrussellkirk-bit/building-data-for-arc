"""Execute the prototype and finite rivals, then publish private review evidence.

Run through the packet's run_with_racket.py/review.py wrapper. This command does
not require or grant native qualification, owner acceptance, or training admission.
Only hash-named files under turns/ are individual model-visible challenges;
controller_public/ contains complete query batches for the controller alone.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

TASK_ID = "f283b8535697"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STRESS = ((10, 10, "corner"), (10, 30, "band_v"),
          (30, 10, "band_h"), (30, 30, "corner"))


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _digest(value):
    return hashlib.sha256(_raw(value)).hexdigest()


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _load_exact(path, prefix):
    body = path.read_bytes()
    name = prefix + hashlib.sha256(str(path).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    _check(spec is not None and spec.loader is not None, f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        # Execute the bytes just read, avoiding a stale same-size bytecode cache.
        exec(compile(body, str(path), "exec"), module.__dict__)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def _source_files():
    names = ["adapter.py", "prototype.py", "promotion.json", "canonical.rkt",
             "verify_and_export.py"]
    paths = [HERE / name for name in names]
    paths += [ROOT / f"generators/{TASK_ID}/generator.py",
              ROOT / "shared/runtime/reviewer_support.py",
              ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
              ROOT / "shared/runtime/arc_repl/racket_bridge.py",
              ROOT / "shared/tools/comment_solutions.py",
              ROOT / "src/arcpuzzles/parametric_worker.py"]
    return [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(paths)]


def _write_public(folder, episode, support, *, query_index=None):
    """The actual writer used by both publication and invariance checks."""
    if query_index is None:
        tests = episode["test"]
    else:
        _check(type(query_index) is int and 0 <= query_index < len(episode["test"]),
               "Invalid private query index")
        tests = [episode["test"][query_index]]
    visible = {"train": episode["train"], "test": tests}
    raw = support.public_challenge_bytes(visible)
    identifier = support.public_challenge_id(visible)
    _check(identifier == hashlib.sha256(raw).hexdigest(), "Visible hash differs")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (identifier + ".json")
    with path.open("xb") as handle:
        handle.write(raw)
    saved = path.read_bytes()
    value = json.loads(saved)
    _check(saved == raw and saved == support.public_challenge_bytes(value),
           "Saved public bytes differ from their canonical projection")
    _check(set(value) == {"train", "test"}
           and all(set(pair) == {"input", "output"} for pair in value["train"])
           and all(set(pair) == {"input"} for pair in value["test"]),
           "Public projection contains private fields")
    if query_index is not None:
        _check(len(value["test"]) == 1, "A model turn must contain one query only")
    return {"id": identifier, "filename": path.name, "bytes": saved}


def _changed_grid(grid):
    result = deepcopy(grid)
    result[0][0] = (result[0][0] + 1) % 10
    return result


def _writer_checks(adapter, support, seed, settings, demos):
    """Exercise the disk writer, including its filenames, not just a serializer."""
    one = adapter.generate(seed, deepcopy(settings), demos, 1)
    four = adapter.generate(seed, deepcopy(settings), demos, 4)
    with tempfile.TemporaryDirectory(prefix="f283-public-writer-") as temporary:
        base = Path(temporary)
        first = _write_public(base / "first", four, support, query_index=0)
        prefix = _write_public(base / "prefix", one, support, query_index=0)
        _check(first == prefix, "One-query and four-query first turns differ")

        altered = deepcopy(four)
        altered.update(seed=-999, settings={"hidden": "changed"},
                       program_solution="private program changed",
                       private_sampling={"hidden": "changed"},
                       query_index=999, query_count=999, final_turn=True)
        for pair in altered["test"]:
            pair["output"] = _changed_grid(pair["output"])
            pair.update(private_note="changed", query_count=999)
        full = _write_public(base / "full", four, support)
        altered_full = _write_public(base / "altered-full", altered, support)
        altered_first = _write_public(base / "altered-first", altered, support,
                                      query_index=0)
        _check(full == altered_full and first == altered_first,
               "Private metadata or query answers changed public bytes/names")

        future = deepcopy(four)
        future["test"][1]["input"] = _changed_grid(future["test"][1]["input"])
        future_first = _write_public(base / "future-first", future, support,
                                     query_index=0)
        future_full = _write_public(base / "future-full", future, support)
        _check(first == future_first, "A future query changed the first turn")
        _check(full != future_full, "Changed visible batch input kept its identity")
    return {"seed": seed, "settings": settings, "demos": demos,
            "actual_disk_writer": True, "private_metadata_and_answer_invariance": True,
            "one_vs_four_query_first_turn_equal": True,
            "future_query_change_first_turn_equal": True,
            "future_query_change_batch_identity_differs": True,
            "first_turn_sha256": first["id"]}


def _coverage(grid):
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    quadrants = []
    for r0, r1 in ((0, h // 2), (h // 2, h)):
        for c0, c1 in ((0, w // 2), (w // 2, w)):
            quadrants.append({"rows": [r0, r1], "cols": [c0, c1],
                              "foreground_cells": sum(r0 <= r < r1 and c0 <= c < c1
                                                      for r, c in cells)})
    return {"shape": [h, w], "foreground_cells_excluding_marker": len(cells),
            "marker_cells": sum(v == 1 for row in grid for v in row),
            "foreground_colors": sorted({grid[r][c] for r, c in cells}),
            "foreground_rows": len({r for r, _ in cells}),
            "foreground_columns": len({c for _, c in cells}),
            "foreground_bbox": ([min(r for r, _ in cells), min(c for _, c in cells),
                                  max(r for r, _ in cells), max(c for _, c in cells)]
                                 if cells else None),
            "quadrants": quadrants}


def _verify_episode(adapter, execute, grid, seed, settings, demos, queries, programs):
    mode = settings["output_mode"]
    episode = adapter.generate(seed, deepcopy(settings), demos, queries)
    chosen = adapter.program(deepcopy(settings))
    _check(episode.get("program_solution") == chosen, "Generated program differs")
    rivals = adapter.core.rival_programs(mode)
    _check(type(rivals) is dict and bool(rivals), "No declared rivals")
    refuted = {name: [] for name in rivals}
    disagreements = {name: [] for name in rivals}
    candidates = {key: True for key in programs}
    inputs, pair_shapes = [], []
    rival_labels = {"train": [], "test": []}
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        _check(type(pairs) is list and len(pairs) == count,
               f"{mode}/{seed}: incorrect {split} count")
        for index, pair in enumerate(pairs):
            _check(type(pair) is dict and {"input", "output"} <= set(pair),
                   "Each private pair needs input/output")
            inp, expected = grid(pair["input"]), grid(pair["output"])
            _check(not adapter.core.validate_input(inp), "Input violates declared grammar")
            inputs.append(_digest(inp))
            actual = execute(chosen, inp)
            context = f"{mode}/seed={seed}/{split}/{index}"
            _check(actual == expected, context + ": Python label differs from Racket")
            claims = adapter.core.rival_outputs(deepcopy(inp), mode)
            _check(type(claims) is dict and set(claims) == set(rivals),
                   context + ": Python and Racket rival names differ")
            executed = {chosen: actual}
            labels = {}
            for name, text in rivals.items():
                prediction = execute(text, inp)
                _check(prediction == grid(claims[name]),
                       context + f": rival {name} Python/Racket disagreement")
                executed[text] = prediction
                labels[name] = prediction
                if prediction != expected:
                    (refuted if split == "train" else disagreements)[name].append(index)
            rival_labels[split].append(labels)
            if split == "train":
                for key, text in programs.items():
                    prediction = executed[text] if text in executed else execute(text, inp)
                    candidates[key] = candidates[key] and prediction == expected
            pair_shapes.append({"split": split, "index": index,
                                "input": [len(inp), len(inp[0])],
                                "output": [len(expected), len(expected[0])]})
    _check(len(set(inputs)) == len(inputs), f"{mode}/{seed}: duplicate inputs")
    _check(all(refuted.values()), f"{mode}/{seed}: unrefuted rivals: "
           + ", ".join(name for name, indices in refuted.items() if not indices))
    survivors = [json.loads(key) for key, fits in candidates.items() if fits]
    _check(survivors == [settings], f"{mode}/{seed}: demos do not identify chosen setting")
    report = {"seed": seed, "settings": settings,
              "counts": {"demos": demos, "queries": queries},
              "program_sha256": hashlib.sha256(chosen.encode()).hexdigest(),
              "rival_program_sha256": {name: hashlib.sha256(text.encode()).hexdigest()
                                       for name, text in rivals.items()},
              "rival_demo_refutations": refuted, "rival_query_disagreements": disagreements,
              "demo_candidates": survivors, "pair_shapes": pair_shapes,
              "private_sampling": episode.get("private_sampling", {})}
    private = {"seed": seed, "settings": settings, **episode,
               "rival_programs": rivals, "rival_outputs": rival_labels}
    return report, private


def _audit(adapter, support, grid, apply, identity, settings, seeds, demos, queries, stage):
    evaluations = 0

    def execute(program, inp):
        nonlocal evaluations
        _check(type(program) is str and bool(program.strip()), "Empty Racket program")
        evaluations += 1
        return grid(apply(program, deepcopy(inp)))

    programs = {_raw(setting).decode().strip(): adapter.program(deepcopy(setting))
                for setting in settings}
    rows, private_rows, writer_checks = [], [], []
    matched = {}
    seen_batch, seen_turn = set(), set()
    for seed in seeds:
        for setting in settings:
            row, private = _verify_episode(adapter, execute, grid, seed, setting,
                                            demos, queries, programs)
            sequence = [pair["input"] for split in ("train", "test") for pair in private[split]]
            if seed in matched:
                _check(sequence == matched[seed], "Inputs/order depend on the private setting")
            else:
                matched[seed] = sequence
            batch = _write_public(stage / "controller_public", private, support)
            _check(batch["id"] not in seen_batch, "Duplicate visible controller batch")
            seen_batch.add(batch["id"])
            turn_paths = []
            for index in range(queries):
                turn = _write_public(stage / "turns", private, support, query_index=index)
                _check(turn["id"] not in seen_turn, "Duplicate visible query turn")
                seen_turn.add(turn["id"])
                turn_paths.append("turns/" + turn["filename"])
            private["controller_public_path"] = "controller_public/" + batch["filename"]
            private["ordered_turn_paths"] = turn_paths
            rows.append(row)
            private_rows.append(private)
            writer_checks.append(_writer_checks(adapter, support, seed, setting, demos))

    stress_rows, stress_private = [], []
    for h, w, family in STRESS:
        inp = grid(adapter.core.sample_input(9, 0, h, w, family))
        _check((len(inp), len(inp[0])) == (h, w), "Stress shape differs")
        _check(not adapter.core.validate_input(inp), "Stress input violates grammar")
        outputs = []
        for setting in settings:
            actual = execute(adapter.program(deepcopy(setting)), inp)
            expected = grid(adapter.core.predict(deepcopy(inp), setting["output_mode"]))
            _check(actual == expected, f"Stress {h}x{w}/{setting}: label differs")
            outputs.append({"settings": setting, "output": actual})
        stress_rows.append({"seed": 9, "index": 0, "marker_family": family,
                            "input_sha256": _digest(inp), "content": _coverage(inp),
                            "outputs": [{"settings": item["settings"],
                                         "shape": [len(item["output"]), len(item["output"][0])],
                                         "sha256": _digest(item["output"])} for item in outputs]})
        stress_private.append({"seed": 9, "index": 0, "marker_family": family,
                               "input": inp, "outputs": outputs})
    private = {"schema": "f283b8535697-prototype-private-v1", "task_id": TASK_ID,
               "programs": programs, "episodes": private_rows, "stress_cases": stress_private,
               "controller_public_is_model_visible": False,
               "model_visible_files": "turns/*.json", "training_admitted": False}
    (stage / "private.json").write_bytes(_raw(private))
    return {"schema": "f283b8535697-prototype-audit-v1", "status": "passed",
            "task_id": TASK_ID, "racket": identity, "racket_evaluations": evaluations,
            "counts": {"settings": len(settings), "seeds": len(seeds),
                       "episodes": len(rows), "demos_per_episode": demos,
                       "queries_per_episode": queries, "stress_inputs": len(STRESS),
                       "controller_batches": len(seen_batch), "model_turns": len(seen_turn)},
            "matched_inputs_across_settings": True, "episodes": rows,
            "writer_checks": writer_checks, "stress_cases": stress_rows,
            "prototype_scope": True, "native_qualification": "not_performed",
            "owner_acceptance": "not_performed", "training_admitted": False,
            "limits": "Finite requested seeds/counts, declared rivals and four size endpoints. "
                      "No universal rule uniqueness or learning benefit is established. "
                      "Only turns/ is model-visible; controller_public/ exposes the full query batch."}


def verify_and_export(output, *, seeds=(0, 17), demos=3, queries=4):
    output = Path(output).absolute()
    _check(not output.exists() and not output.is_symlink(), "Choose a new output directory")
    _check(type(demos) is int and 2 <= demos <= 6, "demos must be an integer in 2..6")
    _check(type(queries) is int and 1 <= queries <= 4, "queries must be an integer in 1..4")
    _check(isinstance(seeds, (list, tuple)) and 1 <= len(seeds) <= 8
           and all(type(seed) is int and 0 <= seed < 2**63 for seed in seeds)
           and len(set(seeds)) == len(seeds), "Use 1..8 distinct seeds in 0..2**63-1")
    sources = _source_files()
    prior_path, prior_bytecode = list(sys.path), sys.dont_write_bytecode
    previous_support = sys.modules.get("reviewer_support")
    sys.path.insert(0, str(ROOT / "src"))
    sys.dont_write_bytecode = True
    try:
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.parametric_promotion import settings_space
        from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
        runtime = ROOT / "shared/runtime"
        with _local_imports(runtime, HERE):
            support = _load_exact(runtime / "reviewer_support.py", "_f283_support_")
            sys.modules["reviewer_support"] = support
            # Import the adapter only after establishing the same-tree runtime.
            adapter = _load_exact(HERE / "adapter.py", "_f283_audit_adapter_")
            contract = json.loads((HERE / "promotion.json").read_bytes())
            settings = settings_space(contract)
            catalog = Catalog(ROOT)
            selected = catalog.describe(TASK_ID)
            authority = selected.get("rule_task_id", TASK_ID)
            canonical = {row["program_solution"] for row in catalog._variants()[authority]}
            _check(canonical == {adapter.program(contract["default"])},
                   "Default differs from exact selected canonical source")
            apply, identity, bridge = _real_evaluator(runtime)
            try:
                output.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix=".f283-audit-", dir=output.parent) as temp:
                    stage = Path(temp)
                    report = _audit(adapter, support, _grid, apply, identity, settings,
                                    seeds, demos, queries, stage)
                    _check(_source_files() == sources, "Source changed during audit; rerun stable bytes")
                    report["source_files"] = sources
                    report["private_sha256"] = hashlib.sha256((stage / "private.json").read_bytes()).hexdigest()
                    (stage / "report.json").write_bytes(_raw(report))
                    _check(not output.exists() and not output.is_symlink(), "Output appeared during audit")
                    os.rename(stage, output)
            finally:
                bridge.close()
    finally:
        sys.path[:] = prior_path
        sys.dont_write_bytecode = prior_bytecode
        if previous_support is None:
            sys.modules.pop("reviewer_support", None)
        else:
            sys.modules["reviewer_support"] = previous_support
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new review-evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--demos", type=int, choices=range(2, 7), default=3)
    parser.add_argument("--queries", type=int, choices=range(1, 5), default=4)
    args = parser.parse_args(argv)
    try:
        report = verify_and_export(args.out, seeds=args.seeds, demos=args.demos, queries=args.queries)
    except Exception as error:
        print(f"verify_and_export: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "racket_evaluations": report["racket_evaluations"],
                      "report": str(args.out.absolute() / "report.json"),
                      "training_admitted": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

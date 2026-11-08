"""Bounded protected-Racket teaching audit and public/private export.

Run from this checkout (or the review workspace's ``review.py run`` wrapper)::

    python3 generators/2a5919c40197/workspace/parametric/audit.py --out NEW_DIRECTORY

This task-local tool grants no approval, qualification, or training admission.
Its finite rival catalogue and two seeds do not prove unique human inference or
correctness over every future draw. Python labels are claims until the protected
same-checkout Racket evaluator re-executes them. public/*.json are controller-side
masked collections; only next_turn(...) is model-facing.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "2a5919c40197"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
MODES = ("all_uniform", "longest_uniform_run")
SEEDS = (0, 17)
DEMO_COUNTS = (2, 6)
QUERY_COUNT = 4


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _support():
    runtime = ROOT / "shared/runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    import reviewer_support
    if Path(reviewer_support.__file__).resolve() != runtime / "reviewer_support.py":
        raise ValueError("Public projection must use this checkout's reviewer_support")
    return reviewer_support


def public_projection(challenge):
    """Return only labeled demonstrations and input-only query records."""
    return json.loads(_support().public_challenge_bytes(challenge))


def next_turn(challenge, index):
    """Reveal one query without its answer, later queries, or private metadata.

    ``index`` belongs to the controller; it is deliberately absent from the
    returned value. No query count, progress field, seed, settings, or rule is
    returned. Demonstrations are copied so consumers cannot mutate the source.
    """
    visible = public_projection(challenge)
    if type(index) is not int or not 0 <= index < len(visible["test"]):
        raise ValueError("query index must be an exact in-range integer")
    return {"train": visible["train"], "test": [visible["test"][index]]}


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_row_band_audit_adapter_" + _sha(path.read_bytes())
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load task-local adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Compile the actual hashed source, independent of stale .pyc timestamps.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _source_hashes():
    paths = [HOME / name for name in
             ("adapter.py", "audit.py", "promotion.json", "canonical.rkt", "longest.rkt")]
    return {p.relative_to(ROOT).as_posix(): _sha(p.read_bytes()) for p in paths}


def _row_rule(selection, *, predicate="uniform", same_color=False):
    """Build an executable rival; all branches are total on admitted grids.

    Band lengths use a bounded walk on row flags. A predicate rival changes
    only the flag computation, preserving the selected episode's aggregation.
    """
    predicates = {
        "uniform": "(= 1 (length (unique row)))",
        "prefix3": "(= 1 (length (unique (take row (min 3 (length row))))))",
        "endpoints": "(= (car row) (last row))",
    }
    condition = ""
    if same_color:
        condition = " (= (car (row-at g j)) (car (row-at g origin)))"
    choices = {
        "all_uniform": "(list-ref flags r)",
        "longest_uniform_run": "(and (> best 0) (= (list-ref lengths r) best))",
        "first": "(and (> best 0) (= (list-ref lengths r) best) (<= r (+ first-best (- best 1))))",
        "last": "(and (> best 0) (= (list-ref lengths r) best) (>= r (- last-best (- best 1))))",
        "height20": "(and (list-ref flags r) (>= (* 5 (list-ref lengths r)) (rows g)))",
        "height25": "(and (list-ref flags r) (>= (* 4 (list-ref lengths r)) (rows g)))",
    }
    if selection.startswith("threshold"):
        threshold = int(selection.removeprefix("threshold"))
        selected = (f"(and (list-ref flags r) (or (< best {threshold}) "
                    f"(>= (list-ref lengths r) {threshold})))")
    else:
        selected = choices[selection]
    return f"""(rule! (lambda (g)
  (let* ((flags (map (lambda (row) {predicates[predicate]}) g))
         (lengths
           (for/list ((origin (range 0 (rows g))))
             (if (list-ref flags origin)
                 (let ((walk (lambda (step)
                         (let loop ((j (+ origin step)))
                           (if (and (>= j 0) (< j (rows g)) (list-ref flags j){condition})
                               (+ 1 (loop (+ j step))) 0)))))
                   (+ 1 (walk -1) (walk 1))) 0)))
         (best (apply max lengths))
         (first-best (let loop ((i 0))
                       (if (or (= i (- (rows g) 1)) (= (list-ref lengths i) best))
                           i (loop (+ i 1)))))
         (last-best (let loop ((i (- (rows g) 1)))
                      (if (or (= i 0) (= (list-ref lengths i) best))
                          i (loop (- i 1))))))
    (cellmap g (r c v) (if {selected} 5 0)))))"""


def rival_programs(mode, adapter):
    """Finite plausible alternatives, fitted only to demonstration labels."""
    other = MODES[1] if mode == MODES[0] else MODES[0]
    rivals = {
        "opposite_mode": adapter.program({"mode": other}),
        "first_three_cells": _row_rule(mode, predicate="prefix3"),
        "row_endpoints": _row_rule(mode, predicate="endpoints"),
        "same_color_longest": _row_rule("longest_uniform_run", same_color=True),
        "first_longest_tie": _row_rule("first"),
        "last_longest_tie": _row_rule("last"),
        **{f"threshold_{k}_or_all": _row_rule(f"threshold{k}") for k in (2, 3, 4)},
        # Exact cross multiplication avoids floating-point or division artifacts.
        "height_at_least_20_percent": _row_rule("height20"),
        "height_at_least_25_percent": _row_rule("height25"),
        "column_uniform": "(rule! (lambda (g) (cellmap g (r c v) (if (= 1 (length (unique (map (lambda (row) (list-ref row c)) g)))) 5 0))))",
        "constant_black": "(rule! (lambda (g) (cellmap g (r c v) 0)))",
        "constant_gray": "(rule! (lambda (g) (cellmap g (r c v) 5)))",
    }
    return rivals


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("Racket result must be an ARC grid")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("Racket result must contain rectangular exact integer colors")
    return copy.deepcopy(value)


class _Executor:
    def __init__(self, apply):
        self.apply = apply
        self.cache = {}
        self.requests = 0
        self.evaluations = 0

    def __call__(self, program, grid):
        self.requests += 1
        key = (program, _json_bytes(grid))
        if key not in self.cache:
            self.cache[key] = _grid(self.apply(program, copy.deepcopy(grid)))
            self.evaluations += 1
        return copy.deepcopy(self.cache[key])


def _require_new_directory(path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ValueError(f"Output must be a new directory: {path}")
    return path


def _must_reject(name, action):
    try:
        action()
    except (TypeError, ValueError, KeyError, IndexError):
        return name
    raise AssertionError(f"Negative check unexpectedly accepted: {name}")


def _export_checks(episode, single_query):
    support = _support()
    visible = public_projection(episode)
    raw = support.public_challenge_bytes(episode)
    identifier = support.public_challenge_id(episode)
    assert identifier == _sha(raw)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    mutated = copy.deepcopy(episode)
    mutated.update({"seed": -987654321, "settings": {"mode": "PRIVATE_SENTINEL"},
                    "program_solution": "PRIVATE_SENTINEL", "query_total": 9000})
    for pair in mutated["test"]:
        pair["output"] = [[9]]
        pair["future_query_hint"] = "PRIVATE_SENTINEL"
    assert support.public_challenge_bytes(mutated) == raw
    assert support.public_challenge_id(mutated) == identifier
    assert next_turn(episode, 0) == next_turn(single_query, 0)
    assert next_turn(mutated, 0) == next_turn(episode, 0)
    later_changed = copy.deepcopy(episode)
    for pair in later_changed["test"][1:]:
        pair["input"] = [[9]]
    assert next_turn(later_changed, 0) == next_turn(episode, 0)
    for index in range(len(episode["test"])):
        turn = next_turn(episode, index)
        assert turn == {"train": visible["train"], "test": [visible["test"][index]]}
    return {"public_id": identifier, "hash_of_exact_visible_file_bytes": True,
            "private_field_id_invariance": True, "single_query_first_turn_equal": True,
            "future_query_input_invariance": True, "single_query_projection_count": len(episode["test"])}


def _negative_checks(adapter, example):
    support = _support()
    invalid = []
    for name, settings in (("missing_mode", {}), ("extra_setting", {"mode": MODES[0], "x": 0}),
                           ("unknown_mode", {"mode": "other"}), ("boolean_mode", {"mode": True})):
        invalid.append(_must_reject(name, lambda settings=settings: adapter.program(settings)))
    for name, seed, demos, queries in (("boolean_seed", True, 2, 1),
                                      ("negative_seed", -1, 2, 1),
                                      ("one_demo", 0, 1, 1), ("seven_demos", 0, 7, 1),
                                      ("zero_queries", 0, 2, 0), ("five_queries", 0, 2, 5)):
        invalid.append(_must_reject(name, lambda seed=seed, demos=demos, queries=queries:
                                   adapter.generate(seed, {"mode": MODES[0]}, demos, queries)))
    for name, replacement in (("public_boolean_cell", [[True]]),
                               ("public_ragged_grid", [[1, 2], [3]])):
        bad = copy.deepcopy(example)
        bad["test"][0]["input"] = replacement
        invalid.append(_must_reject(name, lambda bad=bad: support.public_challenge_bytes(bad)))
    missing_label = copy.deepcopy(example)
    del missing_label["train"][0]["output"]
    invalid.append(_must_reject("missing_demo_label", lambda: support.public_challenge_bytes(missing_label)))
    empty_queries = copy.deepcopy(example)
    empty_queries["test"] = []
    invalid.append(_must_reject("empty_query_list", lambda: support.public_challenge_bytes(empty_queries)))
    for name, index in (("negative_turn_index", -1), ("boolean_turn_index", True),
                        ("past_last_turn_index", len(example["test"]))):
        invalid.append(_must_reject(name, lambda index=index: next_turn(example, index)))
    invalid.append(_must_reject("existing_output_directory", lambda: _require_new_directory(HOME)))
    return invalid


def run_audit(out):
    """Execute eight bounded episodes and retain two masked controller collections."""
    out = _require_new_directory(out)
    sources = _source_hashes()
    adapter = _load_adapter()
    contract = json.loads((HOME / "promotion.json").read_bytes())
    assert contract["parameters"] == {"mode": list(MODES)}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    support = _support()
    source_root = ROOT / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from arcpuzzles import parametric_worker
    if not Path(parametric_worker.__file__).resolve().is_relative_to(source_root):
        raise ValueError("Protected evaluator must come from this checkout")

    apply, identity, bridge = parametric_worker._real_evaluator(ROOT / "shared/runtime")
    execute = _Executor(apply)
    checks, retained, witnesses, rival_sources, all_episodes = [], [], {}, {}, {}
    witness_by_program = {}
    labels = 0
    lesson = None
    try:
        for seed in SEEDS:
            for demos in DEMO_COUNTS:
                matched = None
                for mode in MODES:
                    settings = {"mode": mode}
                    episode = adapter.generate(seed, settings, demos, QUERY_COUNT)
                    chosen = adapter.program(settings)
                    assert episode["program_solution"] == chosen
                    assert len(episode["train"]) == demos and len(episode["test"]) == QUERY_COUNT
                    inputs = {split: [pair["input"] for pair in episode[split]] for split in ("train", "test")}
                    if matched is None:
                        matched = inputs
                    else:
                        assert inputs == matched, "settings must receive matched input grids"
                    flattened = [_json_bytes(grid) for split in inputs.values() for grid in split]
                    assert len(flattened) == len(set(flattened)), "episode inputs must be distinct"
                    assert [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]] == [
                        (3, 3), (17, 12), (24, 23), (30, 30)]
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = execute(chosen, pair["input"])
                            assert actual == pair["output"], f"Racket label mismatch: {seed}/{mode}/{split}/{index}"
                            labels += 1
                    one = adapter.generate(seed, settings, demos, 1)
                    assert one["train"] == episode["train"]
                    assert one["test"] == episode["test"][:1]
                    visibility = _export_checks(episode, one)
                    key = (seed, demos, mode)
                    all_episodes[key] = episode
                    if demos == 6:
                        prefix = all_episodes[(seed, 2, mode)]
                        assert episode["train"][:2] == prefix["train"]
                        assert episode["test"] == prefix["test"], "query stream must be demo-count independent"

                    rival_checks = []
                    for name, candidate in rival_programs(mode, adapter).items():
                        rival_hash = _sha(candidate.encode("utf-8"))
                        rival_sources[rival_hash] = candidate
                        rejected = None
                        for index, pair in enumerate(episode["train"]):
                            observed = execute(candidate, pair["input"])
                            if observed != pair["output"]:
                                rejected = (index, pair, observed)
                                break
                        row = {"rival": name, "program_sha256": rival_hash}
                        if rejected is not None:
                            index, pair, observed = rejected
                            binding = (_sha(chosen.encode("utf-8")), rival_hash)
                            if binding not in witness_by_program:
                                witness = {"kind": "single_demonstration_rejection", "settings": settings,
                                           "seed": seed, "demonstration_count": demos, "demo_index": index,
                                           "reference_program_sha256": binding[0], "rival_program_sha256": rival_hash,
                                           "input": pair["input"], "expected": pair["output"], "rival_output": observed,
                                           "minimality": "One exact labeled demonstration; no claim of cell-wise minimality."}
                                witness_id = _sha(_json_bytes(witness))
                                witnesses[witness_id] = witness
                                witness_by_program[binding] = witness_id
                            row.update({"fits_demos": False, "first_mismatch_demo_index": index,
                                        "witness_id": witness_by_program[binding], "queries_examined": 0})
                        else:
                            differences = []
                            for index, pair in enumerate(episode["test"]):
                                observed = execute(candidate, pair["input"])
                                if observed != pair["output"]:
                                    differences.append(index)
                            row.update({"fits_demos": True, "queries_examined": QUERY_COUNT,
                                        "query_difference_indices": differences,
                                        "status": "harmful_survivor" if differences else "agrees_on_sampled_queries"})
                            assert not differences, f"Harmful rival survivor: {seed}/{demos}/{mode}/{name}/{differences}"
                        rival_checks.append(row)

                    checks.append({"seed": seed, "settings": settings, "demos": demos, "queries": QUERY_COUNT,
                                   "labels_reexecuted": demos + QUERY_COUNT, "rivals": rival_checks,
                                   "export_checks": visibility})
                    if seed == 0 and demos == 2:
                        retained.append({"seed": seed, "settings": settings, "public_id": visibility["public_id"],
                                         "program_solution": chosen, "train": episode["train"], "test": episode["test"]})

        # Separate counterfactual lesson: fitting is still demonstrations-only.
        # This records a real weakness of the one-demo prefix and its repair.
        episode = all_episodes[(0, 2, "longest_uniform_run")]
        threshold = rival_programs("longest_uniform_run", adapter)["threshold_2_or_all"]
        if execute(threshold, episode["train"][0]["input"]) == episode["train"][0]["output"]:
            for index, pair in enumerate(episode["test"]):
                observed = execute(threshold, pair["input"])
                if observed != pair["output"]:
                    second = episode["train"][1]
                    rejected = execute(threshold, second["input"]) != second["output"]
                    assert rejected, "Second demonstration must repair the one-demo threshold shortcut"
                    binding = (_sha(episode["program_solution"].encode("utf-8")), _sha(threshold.encode("utf-8")))
                    lesson = {"rival": "threshold_2_or_all", "seed": 0,
                              "settings": {"mode": "longest_uniform_run"},
                              "program_sha256": binding[1], "fits_demo_indices": [0],
                              "one_demo": episode["train"][0],
                              "query_index": index, "query_input": pair["input"],
                              "query_expected": pair["output"], "query_rival_output": observed,
                              "repair_demo_index": 1, "repair_witness_id": witness_by_program[binding],
                              "fitting_uses_query_answers": False}
                    break
        assert lesson is not None, "Expected a concrete one-demo threshold lesson"
        negative_checks = _negative_checks(adapter, retained[0])
    finally:
        bridge.close()

    assert labels == 64 and len(checks) == 8
    assert _source_hashes() == sources, "Audited source changed during execution; rerun on stable bytes"
    report = {
        "schema": "2a5919c40197-protected-self-audit-v1", "task_id": TASK_ID,
        "status": "passed", "source_sha256": sources, "racket": identity,
        "scope": {"seeds": list(SEEDS), "modes": list(MODES), "demo_counts": list(DEMO_COUNTS),
                  "query_count": QUERY_COUNT, "episodes": len(checks), "claimed_labels_reexecuted": labels,
                  "retained_public_episodes": len(retained), "rivals_per_episode": 14},
        "racket_evaluations": execute.evaluations, "evaluation_requests": execute.requests,
        "cache_hits": execute.requests - execute.evaluations,
        "checks": checks, "negative_checks": negative_checks,
        "single_demo_witness_count": len(witnesses), "harmful_survivors": [],
        "one_demo_teaching_repair": "private/one-demo-lesson.json",
        "exposure_contract": {
            "public_directory": "Controller-side masked collections; may contain multiple query inputs.",
            "model_facing": "Only next_turn(challenge, index), with one query and no future inputs or metadata.",
        },
        "limitations": ["Finite rival catalogue and two sampled seeds; no claim against arbitrary alternative rules.",
                        "Surviving rivals agree only on the sampled queries; this is not a universal equivalence proof.",
                        "Rival formulas are total on the rectangular admitted grammar; runtime errors fail the audit.",
                        "No approval, native qualification, acceptance, or training admission is created."],
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    for episode in retained:
        raw = support.public_challenge_bytes(episode)
        identifier = support.public_challenge_id(episode)
        assert identifier == _sha(raw)
        path = out / "public" / f"{identifier}.json"
        path.write_bytes(raw)
        assert _sha(path.read_bytes()) == identifier
    (out / "private" / "episodes.json").write_bytes(_json_bytes(retained))
    (out / "private" / "rivals.json").write_bytes(_json_bytes(rival_sources))
    (out / "private" / "witnesses.json").write_bytes(_json_bytes(witnesses))
    (out / "private" / "one-demo-lesson.json").write_bytes(_json_bytes(lesson))
    (out / "audit.json").write_bytes(_json_bytes(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new output directory; existing paths are refused")
    args = parser.parse_args(argv)
    report = run_audit(args.out)
    print(json.dumps({"status": report["status"], "scope": report["scope"],
                      "racket_evaluations": report["racket_evaluations"],
                      "single_demo_witness_count": report["single_demo_witness_count"],
                      "report": str(args.out / "audit.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

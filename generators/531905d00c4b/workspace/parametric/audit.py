"""Bounded protected-Racket audit and one-query public views for this prototype.

This is reviewer evidence, not native qualification, acceptance, or a claim of
universal identifiability. Every rival is executed; errors never refute a rival.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "531905d00c4b"
sys.dont_write_bytecode = True


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _source_hashes():
    paths = {p for p in HERE.rglob("*") if p.is_file()
             and p.suffix in {".py", ".rkt", ".json"}
             and not {"evidence", "examples", "__pycache__"}.intersection(p.relative_to(HERE).parts)}
    paths.update(ROOT / relative for relative in (
        f"generators/{TASK}/generator.py",
        f"generators/{TASK}/tests/test_parametric.py",
        "src/arcpuzzles/parametric_worker.py",
        "shared/runtime/reviewer_support.py",
        "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/tools/comment_solutions.py",
    ))
    contract = json.loads((HERE / "promotion.json").read_bytes())
    paths.update(ROOT / relative for relative in contract.get("resources", []))
    return {p.relative_to(ROOT).as_posix(): _sha(p.read_bytes()) for p in sorted(paths)}


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_531905d00c4b_audit_adapter_" + _sha(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Rival transformation no longer matches one exact source expression: " + old)
    return source.replace(old, new, 1)


def rival_programs(adapter, policy):
    """Small explicit alternatives; preserve the selected policy where relevant."""
    selected = adapter.program({"reflection_policy": policy})
    oriented = adapter.program({"reflection_policy": "larger_left"})
    always = _replace(oriented,
        "(oriented (if (> left-mass right-mass) (flip-lr tile) tile))",
        "(oriented (flip-lr tile))")
    rivals = {"always_reflect": always}
    if policy != "canonical":
        comparison = ">" if policy == "larger_left" else "<"
        rivals.update({
            "neighbor_numeric_colors": _replace(selected,
                "(s17p-mass (s17b-lookup-grid lib (at index r c)))", "(at index r c)"),
            "bbox_area_instead_of_mass": _replace(selected,
                "(define (s17p-mass tile) (length (nonzero-cells tile)))",
                "(define (s17p-mass tile) (* (rows tile) (cols tile)))"),
            "inclusive_comparison_ties": _replace(selected,
                f"({comparison} left-mass right-mass)",
                f"({comparison}= left-mass right-mass)"),
            "wraparound_neighbors": _replace(selected,
                "(if (in-bounds? r c (rows index) (cols index)) "
                "(s17p-mass (s17b-lookup-grid lib (at index r c))) 0)",
                "(s17p-mass (s17b-lookup-grid lib (at index r (modulo c (cols index)))))"),
            "reflect_padded_instead_of_tight_crop": _replace(selected,
                "(tile (s17b-lookup-grid lib (at index-area r c)))",
                "(tile (s17b-pad-top-left (s17b-lookup-grid lib (at index-area r c)) ph pw))"),
        })
        cached = _replace(selected,
            "(left-mass (s17p-neighbor-mass lib index-area r (- c 1)))",
            "(first-pos (first (filter (lambda (p) "
            "(= (at index-area (first p) (second p)) (at index-area r c))) "
            "(grid-positions index-area)))) "
            "(left-mass (s17p-neighbor-mass lib index-area "
            "(first first-pos) (- (second first-pos) 1)))")
        rivals["per_color_cached_orientation"] = _replace(cached,
            "(right-mass (s17p-neighbor-mass lib index-area r (+ c 1)))",
            "(right-mass (s17p-neighbor-mass lib index-area "
            "(first first-pos) (+ (second first-pos) 1)))")

    rivals["preserve_absolute_rows"] = _replace(selected,
        "(define (s17b-object-crop grid obj) (let ((bb (obj-bbox obj))) "
        "(subgrid grid (first bb) (second bb) (third bb) (fourth bb))))",
        "(define (s17b-object-crop grid obj) (let ((bb (obj-bbox obj))) "
        "(subgrid grid 0 (second bb) (- (rows grid) 1) (fourth bb))))")
    uncropped = _replace(selected,
        "(index-area (crop-nonzero raw-index))",
        "(index-area (let ((bb (bbox-of-cells (nonzero-cells raw-index)))) "
        "(subgrid raw-index 0 0 (third bb) (fourth bb))))")
    rivals["uncropped_index_top_left"] = _replace(uncropped,
        "(define (s17b-lookup-grid pairs key) "
        "(second (first (filter (lambda (kv) (= (first kv) key)) pairs))))",
        "(define (s17b-lookup-grid pairs key) (if (= key 0) (list (list 0)) "
        "(second (first (filter (lambda (kv) (= (first kv) key)) pairs)))))")
    fixed = _replace(selected,
        "(ph (apply max (map (lambda (obj) (rows (s17b-object-crop lib-area obj))) objs)))",
        "(ph 3)")
    rivals["fixed_3x3_frames"] = _replace(fixed,
        "(pw (apply max (map (lambda (obj) (cols (s17b-object-crop lib-area obj))) objs)))",
        "(pw 3)")
    return rivals


def _rival_grid(value):
    """Keep total wrong-size rival outputs as disagreements, never as errors."""
    if (type(value) is not list or not value or type(value[0]) is not list or not value[0]
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value)):
        raise ValueError("Racket returned a malformed rival grid")
    return value


def _shape(grid):
    return [len(grid), len(grid[0])]


def _difference(expected, actual):
    for r in range(max(len(expected), len(actual))):
        for c in range(max(len(expected[0]), len(actual[0]))):
            a = expected[r][c] if r < len(expected) and c < len(expected[0]) else None
            b = actual[r][c] if r < len(actual) and c < len(actual[0]) else None
            if a != b:
                return {"position": [r, c], "expected": a, "rival": b}
    return None


def _counterexample(episode_index, episode, outputs, demo_bad, query_bad):
    choices = [("train", i) for i in demo_bad] or [("test", i) for i in query_bad]
    if not choices:
        return None
    split, index = min(choices, key=lambda item: sum(
        len(g) * len(g[0]) for g in (episode[item[0]][item[1]]["input"],
                                    episode[item[0]][item[1]]["output"], outputs[item[0]][item[1]])))
    pair, actual = episode[split][index], outputs[split][index]
    return {"pair": f"private.json#/episodes/{episode_index}/{split}/{index}",
            "input_sha256": _sha(_raw(pair["input"])),
            "expected_sha256": _sha(_raw(pair["output"])),
            "rival_sha256": _sha(_raw(actual)),
            "expected_shape": _shape(pair["output"]), "rival_shape": _shape(actual),
            "first_difference": _difference(pair["output"], actual),
            "selection": "smallest checked demonstration refutation, or smallest differing query"}


def build_audit(seed, output):
    """Execute one bounded corpus and publish only labels actually replayed."""
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    output = Path(output).resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Choose a new output directory: " + str(output))
    before = _source_hashes()
    adapter = _load_adapter()
    prototype = adapter.prototype
    policies = tuple(prototype.POLICIES)
    episodes = []
    source_programs = {}
    cache = {}
    calls = hits = 0
    failures = []
    comparisons = []
    teaching = []
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        from reviewer_support import public_challenge_bytes, public_challenge_id
        apply, identity, bridge = _real_evaluator(runtime)

        def execute(program, grid):
            nonlocal calls, hits
            key = (program, _raw(grid))
            source_programs[_sha(program.encode())] = program
            if key in cache:
                hits += 1
            else:
                calls += 1
                cache[key] = _rival_grid(apply(program, deepcopy(grid)))
            return deepcopy(cache[key])

        try:
            common_inputs = None
            for policy in policies:
                settings = {"reflection_policy": policy}
                claimed = adapter.generate(seed, settings, 2, 4)
                program = adapter.program(settings)
                if claimed.get("program_solution") != program:
                    raise ValueError("Adapter program_solution differs from its setting program")
                if len(claimed["train"]) != 2 or len(claimed["test"]) != 4:
                    raise ValueError("Adapter did not honor independent demonstration/query counts")
                inputs = [_grid(p["input"]) for p in claimed["train"] + claimed["test"]]
                if len({_raw(g) for g in inputs}) != 6:
                    raise ValueError("Demonstration/query inputs are not all distinct")
                if common_inputs is not None and common_inputs != inputs:
                    raise ValueError("Input corpus differs across parameter settings")
                common_inputs = inputs
                episode = {"settings": settings, "program_sha256": _sha(program.encode())}
                for split in ("train", "test"):
                    episode[split] = []
                    for index, pair in enumerate(claimed[split]):
                        grid = _grid(pair["input"])
                        actual = _grid(execute(program, grid))
                        if actual != _grid(pair["output"]):
                            failures.append({"kind": "python_label_mismatch", "policy": policy,
                                             "split": split, "pair_index": index})
                        episode[split].append({"input": grid, "output": actual})
                episodes.append(episode)

            for episode_index, episode in enumerate(episodes):
                policy = episode["settings"]["reflection_policy"]
                survivors = []
                for candidate in policies:
                    program = adapter.program({"reflection_policy": candidate})
                    if all(execute(program, pair["input"]) == pair["output"]
                           for pair in episode["train"]):
                        survivors.append(candidate)
                teaching.append({"policy": policy, "survivors_from_demonstrations_only": survivors})
                if survivors != [policy]:
                    failures.append({"kind": "declared_setting_ambiguity", "policy": policy,
                                     "survivors": survivors})
                for name, program in rival_programs(adapter, policy).items():
                    row = {"policy": policy, "rival": name, "backend": "protected_racket",
                           "program_sha256": _sha(program.encode())}
                    try:
                        outputs = {"train": [execute(program, p["input"]) for p in episode["train"]]}
                        demo_bad = [i for i, p in enumerate(episode["train"])
                                    if outputs["train"][i] != p["output"]]
                        query_bad = []
                        if not demo_bad:
                            outputs["test"] = [execute(program, p["input"]) for p in episode["test"]]
                            query_bad = [i for i, p in enumerate(episode["test"])
                                         if outputs["test"][i] != p["output"]]
                        status = ("refuted_on_demonstrations" if demo_bad else
                                  "ambiguous_queries" if query_bad else "unrefuted_agreement_on_support")
                        row.update(status=status, demonstration_refutations=demo_bad,
                                   query_audit="not_needed_refuted_on_demo" if demo_bad else "executed",
                                   query_mismatches=None if demo_bad else query_bad,
                                   counterexample=_counterexample(episode_index, episode, outputs,
                                                                 demo_bad, query_bad))
                        if status == "ambiguous_queries":
                            failures.append({"kind": status, "policy": policy, "rival": name,
                                             "query_mismatches": query_bad, "seed": seed})
                    except Exception as error:
                        row.update(status="execution_failed", error=f"{type(error).__name__}: {error}")
                        failures.append({"kind": "rival_execution_failed", "policy": policy,
                                         "rival": name, "error": row["error"]})
                    comparisons.append(row)
        finally:
            bridge.close()

        public = []
        for episode_index, episode in enumerate(episodes):
            for query_index, pair in enumerate(episode["test"]):
                visible = prototype.public_turn(episode, query_index)
                payload = public_challenge_bytes(visible)
                identifier = public_challenge_id(visible)
                if identifier != _sha(payload) or len(json.loads(payload)["test"]) != 1:
                    raise ValueError("Public projection/identity contract failed")
                public.append((identifier, payload, {
                    "public_id": identifier, "episode_index": episode_index,
                    "query_index": query_index, "settings": episode["settings"],
                    "answer": deepcopy(pair["output"]),
                }))
    public.sort(key=lambda item: item[0])
    if len({item[0] for item in public}) != len(public):
        raise ValueError("Duplicate visible challenge in audit export")
    if _source_hashes() != before:
        raise ValueError("Prototype/audit sources changed during execution; rerun on final bytes")
    private = {"schema": "arcpuzzles-parametric-audit-private-v1", "task_id": TASK,
               "seed": seed, "episodes": episodes, "program_sources": source_programs,
               "public_answers": [item[2] for item in public]}
    private_bytes = _raw(private)
    report = {
        "schema": "arcpuzzles-parametric-teaching-audit-v1", "task_id": TASK,
        "status": "failed" if failures else "passed", "seed": seed,
        "source_hashes": before, "racket": identity,
        "counts": {"settings": len(episodes), "demonstrations_per_episode": 2,
                   "queries_per_episode": 4, "shared_distinct_inputs": 6,
                   "selected_labels_checked": 6 * len(episodes),
                   "extra_rival_comparisons": len(comparisons),
                   "racket_evaluations": calls, "racket_cache_hits": hits},
        "jobs": [{"seed": seed, "settings": e["settings"], "demos": 2, "queries": 4,
                  "program_sha256": e["program_sha256"]} for e in episodes],
        "declared_setting_teaching": teaching, "rivals": comparisons, "failures": failures,
        "query_shapes": [{"policy": e["settings"]["reflection_policy"],
                          "shapes": [{"input": _shape(p["input"]), "output": _shape(p["output"])}
                                     for p in e["test"]]} for e in episodes],
        "files": [{"path": f"public/{identifier}.json", "sha256": identifier,
                   "bytes": len(payload)} for identifier, payload, _ in public]
                 + [{"path": "private.json", "sha256": _sha(private_bytes), "bytes": len(private_bytes)}],
        "public_visibility": "Each hash-named visible file contains demonstrations and exactly one query input. "
                             "Settings, query answers, other query inputs, and programs are private.",
        "limits": "One seed and a finite declared rival set only. Rival fits use demonstrations only. "
                  "Queries of already refuted extra rivals are not executed; all intended query labels are. "
                  "Counterexamples select the smallest checked pair; no cell minimization is claimed. "
                  "Wrong-size rival grids are output disagreements, not execution failures. "
                  "No native qualification, owner acceptance, universal identifiability or training admission.",
        "training_admitted": False,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    for identifier, payload, _ in public:
        (output / "public" / f"{identifier}.json").write_bytes(payload)
    (output / "private.json").write_bytes(private_bytes)
    (output / "report.json").write_bytes(_raw(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New audit output directory")
    parser.add_argument("--seed", type=int, default=17)
    options = parser.parse_args(argv)
    try:
        report = build_audit(options.seed, options.out)
    except Exception as error:
        print(json.dumps({"status": "failed", "error": f"{type(error).__name__}: {error}"}), file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in ("status", "task_id", "seed", "counts", "failures")},
                     sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

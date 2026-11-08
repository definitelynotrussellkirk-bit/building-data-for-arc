"""Bounded protected-Racket evidence for this task's separate parametric family.

Run ``check --out NEW_DIRECTORY`` before manifest/qualification, then attach the
native source binding with ``witness --qualification FILE --evidence FILE
--out NEW_FILE``. Public files contain one current query and opaque byte hashes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = "9c5bdbcdcd50"
SEEDS = (0, 17)
ANCHORS = ("frame", "largest")
MAX_RACKET_EVALUATIONS = 150


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _load(path, role):
    path = Path(path).resolve()
    name = "_lattice_probe_" + role + "_" + _digest(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _support():
    return _load(ROOT / "shared/runtime/reviewer_support.py", "public")


def _native():
    source = str(ROOT / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    return _grid, _local_imports, _real_evaluator


def source_hashes():
    """Task source subset of the native binding; no duplicated runtime inventory."""
    paths = {ROOT / "generators" / TASK / "generator.py"}
    paths.update(path for path in HOME.rglob("*")
                 if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
                 and not any(part in {"evidence", "examples", "__pycache__"}
                             for part in path.relative_to(HOME).parts))
    result = {}
    for path in sorted(paths):
        if path.is_symlink() or path.resolve() != path:
            raise ValueError("Source must be a regular same-checkout file: " + str(path))
        result[path.relative_to(ROOT).as_posix()] = _digest(path.read_bytes())
    return result


def public_view(episode, query_index=0):
    """One turn's visible context, without future inputs or private metadata."""
    if (type(query_index) is not int or not 0 <= query_index < len(episode["test"])):
        raise ValueError("query_index must identify one stored query")
    value = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(_support().public_challenge_bytes(value))


def validate_public_bytes(payload, identifier):
    """Reject leaked fields, malformed grids, noncanonical bytes and wrong IDs."""
    value = json.loads(payload)
    if (type(value) is not dict or set(value) != {"train", "test"}
            or type(value["train"]) is not list or type(value["test"]) is not list
            or not value["train"] or len(value["test"]) != 1
            or any(type(pair) is not dict or set(pair) != {"input", "output"}
                   for pair in value["train"])
            or type(value["test"][0]) is not dict
            or set(value["test"][0]) != {"input"}):
        raise ValueError("Public files need only demonstrations and one query input")
    if _support().public_challenge_bytes(value) != payload:
        raise ValueError("Public bytes must be exact canonical visible serialization")
    if _digest(payload) != identifier:
        raise ValueError("Public identifier must hash only the exact public bytes")
    return value


def _replace(program, old, new):
    if program.count(old) != 1:
        raise ValueError("Rival template no longer matches one exact source expression: " + old)
    return program.replace(old, new, 1)


def _fixed_pivot(program, row, col):
    result = _replace(program, "(pr (second selected))", f"(pr {row})")
    return _replace(result, "(pc (third selected))", f"(pc {col})")


def _rivals(programs):
    frame, largest = programs["frame"], programs["largest"]
    interior = "((and (> ri 0) (< ri (- nr 1)) (> ci 0) (< ci (- nc 1))) 7)"
    swapped = _replace(frame, "((and (= ri (- nr 1)) (zero? ci)) 1)",
                       "((and (= ri (- nr 1)) (zero? ci)) 8)")
    swapped = _replace(swapped, "((and (= ri (- nr 1)) (= ci (- nc 1))) 8)",
                       "((and (= ri (- nr 1)) (= ci (- nc 1))) 1)")
    threshold = _replace(frame, interior,
        "((and (> ri 0) (< ri (- nr 1)) (> ci 0) (< ci (- nc 1))) "
        "(if (< (* (+ 1 (- (second rr) (first rr))) "
        "(+ 1 (- (second cr) (first cr)))) 4) 0 7))")
    swapped_pivot = _replace(largest, "(pr (second selected))", "(pr (third selected))")
    swapped_pivot = _replace(swapped_pivot, "(pc (third selected))", "(pc (second selected))")
    interior_pivot = _replace(largest, "(selected (argmax first regions))",
        "(selected (argmax first (filter (lambda (p) "
        "(and (> (second p) 0) (< (second p) (- nr 1)) "
        "(> (third p) 0) (< (third p) (- nc 1)))) regions)))")
    pivot_only = largest
    for old, new in (
        ("((and (< ri pr) (< ci pc)) 2)", "((and (< ri pr) (< ci pc)) 0)"),
        ("((and (< ri pr) (> ci pc)) 4)", "((and (< ri pr) (> ci pc)) 0)"),
        ("((and (> ri pr) (< ci pc)) 1)", "((and (> ri pr) (< ci pc)) 0)"),
        ("(else 8)", "(else 0)"),
    ):
        pivot_only = _replace(pivot_only, old, new)
    return {
        "frame": {
            "declared_largest": largest,
            "paint_noncorner_edges": _replace(frame, "(else 0)", "(else 7)"),
            "swap_bottom_corner_colors": swapped,
            "omit_interior_fill": _replace(frame, interior, interior[:-2] + "0)"),
            "interior_area_at_least_four": threshold,
        },
        "largest": {
            "declared_frame": frame,
            "fixed_middle_pivot": _fixed_pivot(largest, "(quotient nr 2)", "(quotient nc 2)"),
            "fixed_pivot_1_1": _fixed_pivot(largest, 1, 1),
            "largest_interior_pivot": interior_pivot,
            "swap_pivot_axes": swapped_pivot,
            "column_mirrored_from_row": _replace(largest, "(pc (third selected))",
                                                 "(pc (max 0 (- nc 1 pr)))"),
            "row_mirrored_from_column": _replace(largest, "(pr (second selected))",
                                                 "(pr (max 0 (- nr 1 (third selected))))"),
            "smallest_pivot": _replace(largest, "(selected (argmax first regions))",
                                       "(selected (argmin first regions))"),
            "pivot_only": pivot_only,
        },
    }


def _validate_episode(episode, settings, demos, queries, program, grid):
    if type(episode) is not dict or episode.get("program_solution") != program:
        raise ValueError("Episode program differs from its episode-fixed setting")
    inputs = []
    for name, count in (("train", demos), ("test", queries)):
        if type(episode.get(name)) is not list or len(episode[name]) != count:
            raise ValueError("Returned split count differs from the independent request")
        for pair in episode[name]:
            grid(pair["input"])
            grid(pair["output"])
            inputs.append(_bytes(pair["input"]))
    if len(set(inputs)) != len(inputs):
        raise ValueError("Demonstrations and queries must all have distinct inputs")


def _input_sequence(episode):
    return {name: [pair["input"] for pair in episode[name]] for name in ("train", "test")}


def _export_public(output, selected):
    support = _support()
    planned, index = {}, []
    for episode in selected:
        for number in range(len(episode["test"])):
            payload = support.public_challenge_bytes(public_view(episode, number))
            identifier = support.public_challenge_id(public_view(episode, number))
            validate_public_bytes(payload, identifier)
            if identifier in planned:
                raise ValueError("Duplicate visible challenge in bounded export")
            planned[identifier] = payload
            index.append({"settings": episode["settings"], "seed": episode["seed"],
                          "query_index": number, "public_id": identifier})
    directory = output / "public"
    directory.mkdir()
    for identifier, payload in sorted(planned.items()):
        path = directory / (identifier + ".json")
        with path.open("xb") as stream:
            stream.write(payload)
        validate_public_bytes(path.read_bytes(), path.stem)
    # In-memory negative verifier cases never leave a malformed public artifact.
    payload = next(iter(planned.values()))
    cases = []
    leaked = json.loads(payload)
    leaked["settings"] = {"anchor": "largest"}
    malformed = json.loads(payload)
    malformed["test"][0]["input"][0][0] = False
    for name, candidate, identifier in (
        ("private_setting_field", _bytes(leaked), _digest(_bytes(leaked))),
        ("boolean_color", _bytes(malformed), _digest(_bytes(malformed))),
        ("wrong_visible_hash", payload, "0" * 64),
    ):
        try:
            validate_public_bytes(candidate, identifier)
        except (ValueError, TypeError):
            cases.append({"case": name, "rejected": True})
        else:
            raise AssertionError("Malformed public export was accepted: " + name)
    return {"files": len(planned), "private_index": index, "negative_verifier_cases": cases,
            "projection": "Each public file contains the original demos and one current query; no future inputs, answers, settings, programs or total-count hints."}


def check(output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    before = source_hashes()
    output.mkdir(parents=True, exist_ok=False)
    result = {"task_id": TASK, "status": "running", "source_sha256": before,
              "command": list(sys.argv), "training_admitted": False,
              "counts": {"requests": 0, "generation_succeeded": 0,
                         "generation_failed": 0, "racket_evaluations": 0},
              "teaching": [], "episodes": [], "boundaries": [],
              "limitations": "Two seeds and finite declared rivals only. No universal identifiability, broad seed census, measured learning benefit, or native acceptance is claimed. Tallest-row/widest-column factorization is mathematically equivalent to largest area on this grammar."}
    try:
        prototype = _load(HOME / "prototype.py", "prototype")
        programs = {anchor: prototype.program({"anchor": anchor}) for anchor in ANCHORS}
        result["programs"] = {anchor: {"settings": {"anchor": anchor}, "program": program,
                                        "sha256": _digest(program.encode())}
                              for anchor, program in programs.items()}
        rivals = _rivals(programs)
        result["rivals"] = {anchor: {name: {"program": program, "sha256": _digest(program.encode())}
                                    for name, program in choices.items()}
                             for anchor, choices in rivals.items()}
        grid, local_imports, real_evaluator = _native()
        cache = {}
        episodes = {}
        holes = []
        with local_imports(ROOT / "shared/runtime", HOME):
            apply, identity, bridge = real_evaluator(ROOT / "shared/runtime")
            result["racket"] = identity
            try:
                def execute(program, value):
                    key = (_digest(program.encode()), _digest(_bytes(value)))
                    if key not in cache:
                        if result["counts"]["racket_evaluations"] >= MAX_RACKET_EVALUATIONS:
                            raise ValueError("Bounded probe exhausted its 150-execution budget")
                        result["counts"]["racket_evaluations"] += 1
                        cache[key] = grid(apply(program, grid(value)))
                    return copy.deepcopy(cache[key])

                def generate(seed, anchor, demos, queries):
                    result["counts"]["requests"] += 1
                    try:
                        episode = prototype.generate(seed, {"anchor": anchor}, demos, queries)
                        _validate_episode(episode, {"anchor": anchor}, demos, queries, programs[anchor], grid)
                        for split in ("train", "test"):
                            for pair in episode[split]:
                                prototype.analyze(pair["input"])
                                if execute(programs[anchor], pair["input"]) != pair["output"]:
                                    raise AssertionError("Python label disagrees with protected Racket")
                    except Exception:
                        result["counts"]["generation_failed"] += 1
                        raise
                    result["counts"]["generation_succeeded"] += 1
                    return episode

                for seed in SEEDS:
                    for anchor in ANCHORS:
                        episode = generate(seed, anchor, 3, 4)
                        episodes[(seed, anchor)] = episode
                        result["boundaries"].append({"seed": seed, "settings": {"anchor": anchor},
                            "query_sizes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
                            "query_geometry": [prototype.analyze(pair["input"]) for pair in episode["test"]],
                            "demonstration_pivots": [prototype.analyze(pair["input"])["pivot"] for pair in episode["train"]]})
                        checks = []
                        for name, rival in rivals[anchor].items():
                            predicted = [execute(rival, pair["input"]) for pair in episode["train"][:2]]
                            mismatches = [i for i, (actual, pair) in enumerate(zip(predicted, episode["train"]))
                                          if actual != pair["output"]]
                            row = {"name": name, "demos_executed": 2,
                                   "fits_all_demos": not mismatches, "distinguishing_demo_indices": mismatches}
                            if not mismatches:
                                disagreements = []
                                for index, pair in enumerate(episode["test"]):
                                    alternative = execute(rival, pair["input"])
                                    if alternative != pair["output"]:
                                        disagreements.append(index)
                                        if not any(h["seed"] == seed and h["anchor"] == anchor and h["rival"] == name for h in holes):
                                            holes.append({"seed": seed, "anchor": anchor, "rival": name,
                                                "train": episode["train"][:2], "query": pair,
                                                "rival_query_output": alternative})
                                row["query_disagreements"] = disagreements
                            checks.append(row)
                        result["teaching"].append({"seed": seed, "settings": {"anchor": anchor},
                            "demos_used": 2, "rivals": checks})
                        # Count boundaries share deterministic inputs with the ordinary draw.
                        for demos in (2, 6):
                            for queries in (1, 4):
                                boundary = generate(seed, anchor, demos, queries)
                                if (boundary["train"][:min(3, demos)] != episode["train"][:min(3, demos)]
                                        or boundary["test"] != episode["test"][:queries]):
                                    raise AssertionError("Count requests changed stable demonstration/query prefixes")
                        one = generate(seed, anchor, 3, 1)
                        if public_view(one) != public_view(episode):
                            raise AssertionError("Single-query and four-query first turns differ")
                        altered = copy.deepcopy(episode)
                        altered.update(settings={"private": "changed"}, seed=-1, program_solution="private")
                        for pair in altered["test"]:
                            pair["output"] = [[9]]
                        altered["test"][1:] = [{"input": [[8]], "output": [[7]]}]
                        if public_view(altered) != public_view(episode):
                            raise AssertionError("Private metadata or future queries leaked into the current turn")
                    if _input_sequence(episodes[(seed, "frame")]) != _input_sequence(episodes[(seed, "largest")]):
                        raise AssertionError("Private settings changed sampled inputs")

                dependency = {
                    "step_a": "Parse the complete green-divider lattice and select its unique largest zero rectangle.",
                    "intermediate": "The selected rectangle's input-derived matrix coordinates, bounds, and area.",
                    "step_b": "Use that selected coordinate to fill the pivot 7, its other row/column regions 0, and the four quadrants 2/4/1/8, preserving dividers.",
                    "why_b_depends_on_a": "The selected coordinates determine each region's quadrant or axis; moving the unique largest rectangle changes later color choices at unchanged matrix indices.",
                    "cases": [],
                }
                wrong = _fixed_pivot(programs["largest"], 1, 1)
                for rb, cb in (([1, 6, 2, 3, 4], [4, 2, 1, 6, 3]),
                               ([1, 2, 3, 6, 4], [4, 6, 1, 2, 3])):
                    value = prototype.lattice(rb, cb)
                    facts = prototype.analyze(value)
                    pr, pc = facts["pivot"]
                    actual = execute(programs["largest"], value)
                    alternative = execute(wrong, value)
                    if actual == alternative or actual != prototype.transform(value, "largest"):
                        raise AssertionError("Causal witness did not change the Racket-verified final output")
                    dependency["cases"].append({"input": value, "settings": {"anchor": "largest"},
                        "intermediate_value": {"pivot": facts["pivot"], "row_range": facts["row_ranges"][pr],
                                               "col_range": facts["col_ranges"][pc], "area": facts["largest_area"]},
                        "program": programs["largest"], "output": actual,
                        "counterfactual_program": wrong, "counterfactual_output": alternative,
                        "ablation": "wrong_intermediate"})
                result["causal_witness_raw"] = dependency
            finally:
                bridge.close()
        result["teaching_holes"] = holes
        result["counts"]["teaching_holes"] = len(holes)
        result["counts"]["rival_demo_executions_requested"] = sum(
            row["demos_executed"] for lesson in result["teaching"] for row in lesson["rivals"])
        selected = [{"seed": SEEDS[0], "settings": {"anchor": anchor},
                     "train": episodes[(SEEDS[0], anchor)]["train"],
                     "test": episodes[(SEEDS[0], anchor)]["test"]} for anchor in ANCHORS]
        result["episodes"] = selected
        if holes:
            raise AssertionError("A plausible wrong rule fits both required demos and disagrees on a query")
        result["public_export"] = _export_public(output, selected)
        if source_hashes() != before:
            raise ValueError("Prototype source changed during the bounded check")
        result["checks"] = {"matched_inputs_across_settings": True,
            "stable_prefixes_across_independent_counts": True,
            "identical_one_vs_four_query_first_turn": True,
            "private_metadata_and_future_query_independence": True,
            "demos_requested": [2, 3, 6], "queries_requested": [1, 4],
            "seeds": list(SEEDS), "source_unchanged": True}
        result["status"] = "passed"
    except Exception as error:
        result["status"] = "failed"
        result["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        with (output / "evidence.json").open("xb") as stream:
            stream.write(_bytes(result))
    return result


def build_witness(qualification_path, evidence_path, output):
    """Bind already executed cases to exact current native qualification bytes."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    qualification = json.loads(Path(qualification_path).read_bytes())
    evidence = json.loads(Path(evidence_path).read_bytes())
    if (qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or qualification.get("status") != "qualified"
            or qualification.get("task_id") != TASK or evidence.get("task_id") != TASK
            or evidence.get("status") != "passed"):
        raise ValueError("Witness needs this task's passing probe and native qualification")
    if evidence.get("source_sha256") != source_hashes():
        raise ValueError("Executed probe evidence differs from current source hashes")
    _native()
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_promotion import _ready
    contract, binding = _ready(Catalog(ROOT), TASK)
    if qualification.get("source_binding") != binding or qualification.get("contract") != contract:
        raise ValueError("Qualification differs from the exact current source binding")
    bound = {row["path"]: row["sha256"] for row in binding["files"]}
    if any(bound.get(name) != digest for name, digest in evidence["source_sha256"].items()):
        raise ValueError("Qualification does not bind every probed source file")
    raw = evidence["causal_witness_raw"]
    if evidence.get("racket", {}).get("backend") != "racket" or evidence["racket"].get("protected") is not True:
        raise ValueError("Causal labels must already have executed through protected Racket")
    for case in raw["cases"]:
        key = json.dumps(case["settings"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if qualification.get("programs", {}).get(key) != _digest(case["program"].encode()):
            raise ValueError("Causal program is absent from the qualified setting-program map")
        if case["output"] == case["counterfactual_output"]:
            raise ValueError("Counterfactual must change the executed output")
    result = {"schema": "arcpuzzles-sequential-dependency-witness-v1",
              "source_binding": binding, "racket": {"backend": "racket", "protected": True}, **raw}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(_bytes(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("check", help="Run the finite protected-Racket authoring check")
    verify.add_argument("--out", required=True, type=Path)
    witness = sub.add_parser("witness", help="Bind executed causal cases after native qualification")
    witness.add_argument("--qualification", required=True, type=Path)
    witness.add_argument("--evidence", required=True, type=Path)
    witness.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check(args.out)
            summary = {"status": result["status"], "counts": result["counts"],
                       "evidence": str(args.out / "evidence.json")}
        else:
            result = build_witness(args.qualification, args.evidence, args.out)
            summary = {"status": "bound", "cases": len(result["cases"]), "witness": str(args.out)}
    except Exception as error:
        print(json.dumps({"status": "failed", "error": type(error).__name__, "message": str(error)}))
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

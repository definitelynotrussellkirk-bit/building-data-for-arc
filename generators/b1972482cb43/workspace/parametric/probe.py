#!/usr/bin/env python3
"""Bounded protected-Racket self-audit and visible-byte export for this family.

From the packet root, using its selected Python environment::

    WORK/.venv/bin/python review.py run python3 \
      generators/b1972482cb43/workspace/parametric/probe.py \
      --seeds 0 17 --demos 3 6 \
      --out generators/b1972482cb43/workspace/parametric/evidence/probe

Only ``public/*.json`` is model-visible. ``private.json`` retains the actual
episodes, settings, programs, intermediate geometry and execution outputs.
``summary.json`` is a source-bound authoring receipt, written last. This tool
does not qualify, accept, approve, or admit data to training. Its finite rivals
and sampled seeds do not establish exhaustive identifiability.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import parametric_worker as native
import reviewer_support as visible

TASK_ID = "b1972482cb43"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared/runtime"
QUERIES = 4
SCHEMA = "b1972482cb43-parametric-probe-v1"


class ProbeError(ValueError):
    """A failed audit must not publish a purportedly verified challenge."""


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def _load_prototype():
    path = HERE / "prototype.py"
    body = path.read_bytes()
    name = "_b197_probe_prototype_" + _sha(str(path).encode() + body)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Execute precisely the hashed bytes, avoiding timestamp-based pyc reuse.
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def _source_inventory():
    paths = set(HERE.glob("*.py")) | set(HERE.glob("*.rkt")) | set(HERE.glob("*.json"))
    paths.update((RUNTIME / "arc_repl").glob("*.py"))
    paths.update((RUNTIME / "arc_repl/racket_prelude").rglob("*.rkt"))
    paths.update(ROOT / relative for relative in (
        f"generators/{TASK_ID}/generator.py", "src/arcpuzzles/parametric_worker.py",
        "shared/runtime/reviewer_support.py", "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/runtime/puzzle_generators/base.py", "shared/runtime/puzzle_generators/helpers/grid.py",
    ))
    rows = []
    for path in sorted(paths):
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ProbeError(f"Source must be a regular same-checkout file: {path}")
        body = path.read_bytes()
        rows.append({"path": path.relative_to(ROOT).as_posix(),
                     "bytes": len(body), "sha256": _sha(body)})
    return {"files": rows, "sha256": _sha(_bytes(rows))}


def _execute(execute, program, grid, name, stage, index):
    try:
        return native._grid(execute(program, native._grid(grid)))
    except Exception as exc:
        raise ProbeError(f"{name} failed at {stage} {index}: {type(exc).__name__}: {exc}") from exc


def fit_demonstrations(train, programs, execute):
    """Fit a fixed finite candidate set using only the supplied demonstrations.

    There is deliberately no query argument. Every candidate executes every
    demonstration, even after its first disagreement; errors are never witnesses.
    Witness positions in receipts are one-based.
    """
    if not train or not programs:
        raise ProbeError("Nonempty demonstrations and candidate programs are required")
    rows, actual = [], {}
    for name, program in programs.items():
        if type(name) is not str or not name or type(program) is not str or not program.strip():
            raise ProbeError("Each candidate needs a name and exact nonempty Racket text")
        outputs = [_execute(execute, program, pair["input"], name, "demonstration", i)
                   for i, pair in enumerate(train, 1)]
        agreement = [output == pair["output"] for output, pair in zip(outputs, train)]
        rows.append({"name": name, "program_sha256": _sha(program.encode()),
                     "demonstration_agreement": agreement,
                     "first_distinguishing_demo": next((i for i, same in enumerate(agreement, 1)
                                                         if not same), None),
                     "survives_demos": all(agreement)})
        actual[name] = outputs
    return rows, actual


def check_queries(test, programs, fitted, execute):
    """Verify labels and agreement of the already frozen demonstration survivors."""
    survivors = [row["name"] for row in fitted if row["survives_demos"]]
    if "selected" not in survivors:
        raise ProbeError("Selected Racket program disagrees with demonstration claims")
    selected = [_execute(execute, programs["selected"], pair["input"], "selected", "query", i)
                for i, pair in enumerate(test, 1)]
    for i, (output, pair) in enumerate(zip(selected, test), 1):
        if output != pair["output"]:
            raise ProbeError(f"Selected Racket program disagrees with Python claim at query {i}")
    outputs = {"selected": selected}
    agreements = {"selected": [True] * len(test)}
    for name in survivors:
        if name == "selected":
            continue
        outputs[name] = [_execute(execute, programs[name], pair["input"], name, "query", i)
                         for i, pair in enumerate(test, 1)]
        agreements[name] = [output == reference for output, reference in zip(outputs[name], selected)]
        if not all(agreements[name]):
            index = agreements[name].index(False) + 1
            raise ProbeError(f"Demonstration survivor {name} disagrees at query {index}")
    return {"candidate_query_agreement": agreements, "per_query_agreement": [
        {"query": i + 1, "all_demonstration_survivors_agree": True,
         "survivor_count": len(survivors), "selected_claim_matches": True}
        for i in range(len(test))]}, outputs


def public_identity_checks(episode):
    """Use the shared exact serializer; exercise hidden and visible field controls."""
    payload = visible.public_challenge_bytes(episode)
    public_id = visible.public_challenge_id(episode)
    if public_id != _sha(payload):
        raise ProbeError("Public identity is not the SHA-256 of the exact visible bytes")
    metadata = copy.deepcopy(episode)
    metadata.update(settings={"private_mutation": True}, seed=-1,
                    program_solution="private program mutation", private_metadata=["changed"])
    for pair in metadata["train"] + metadata["test"]:
        pair["private_metadata"] = {"changed": True}
    answers = copy.deepcopy(episode)
    for pair in answers["test"]:
        pair["output"] = [[(cell + 1) % 10 for cell in row] for row in pair["output"]]
    controls = {"metadata_mutation_invariant": visible.public_challenge_bytes(metadata) == payload,
                "query_answer_mutation_invariant": visible.public_challenge_bytes(answers) == payload}
    for value in (metadata, answers):
        if visible.public_challenge_id(value) != public_id:
            raise ProbeError("Hidden metadata or query answers changed the public ID")
    changed_demo = copy.deepcopy(episode)
    changed_demo["train"][0]["output"][0][0] = (changed_demo["train"][0]["output"][0][0] + 1) % 10
    changed_query = copy.deepcopy(episode)
    changed_query["test"][0]["input"][0][0] = (changed_query["test"][0]["input"][0][0] + 1) % 10
    controls["visible_mutation_changes_id"] = all(
        visible.public_challenge_id(value) != public_id for value in (changed_demo, changed_query))
    if not all(controls.values()):
        raise ProbeError("Public-byte mutation control failed")
    return payload, {"public_id": public_id, **controls}


def first_turn_check(full, one_query):
    """More requested queries must not change the visible first-turn challenge."""
    projected = {"train": full["train"], "test": full["test"][:1]}
    left = visible.public_challenge_bytes(projected)
    right = visible.public_challenge_bytes(one_query)
    if left != right:
        raise ProbeError("One-query and four-query first-turn visible bytes differ")
    if one_query["test"][0]["output"] != full["test"][0]["output"]:
        raise ProbeError("One-query first-turn answer claim differs from the rederived label")
    return {"equal_visible_bytes": True, "one_query_public_id": _sha(right),
            "four_query_first_turn_public_id": _sha(left)}


def _episode(value, program, demos, queries):
    if type(value) is not dict or value.get("program_solution") != program:
        raise ProbeError("Generated program_solution must exactly equal program(settings)")
    normalized = {"program_solution": program}
    for split, count in (("train", demos), ("test", queries)):
        pairs = value.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ProbeError(f"Requested {count} {split} pairs, but generation returned another count")
        normalized[split] = []
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ProbeError("Every generated pair needs input and output grids")
            normalized[split].append({key: native._grid(pair[key]) for key in ("input", "output")})
    inputs = [_bytes(pair["input"]) for split in ("train", "test") for pair in normalized[split]]
    if len(set(inputs)) != demos + queries:
        raise ProbeError("All demonstration and query inputs must be distinct")
    return normalized


def _candidates(prototype, settings, chosen):
    chosen_settings = settings[chosen]
    programs = {"selected": prototype.program(copy.deepcopy(chosen_settings))}
    bindings = {"selected": {"settings": chosen_settings, "rival": None}}
    for index, setting in enumerate(settings):
        if index != chosen:
            name = f"setting:{index}"
            programs[name] = prototype.program(copy.deepcopy(setting))
            bindings[name] = {"settings": setting, "rival": None}
    rivals = prototype.rival_programs(copy.deepcopy(chosen_settings))
    if type(rivals) is not dict or not rivals:
        raise ProbeError("rival_programs(settings) must declare a nonempty finite mapping")
    for name, program in rivals.items():
        if type(name) is not str or not name:
            raise ProbeError("Each declared rival must have a nonempty name")
        programs["rival:" + name] = program
        bindings["rival:" + name] = {"settings": chosen_settings, "rival": name}
    if any(type(program) is not str or not program.strip() for program in programs.values()):
        raise ProbeError("Every candidate must provide exact nonempty Racket source")
    return programs, bindings


def _geometry_parity(prototype, pairs, outputs, binding, name, split):
    for i, (pair, actual) in enumerate(zip(pairs, outputs), 1):
        predicted = native._grid(prototype.predict(copy.deepcopy(pair["input"]),
            copy.deepcopy(binding["settings"]), binding["rival"]))
        if predicted != actual:
            raise ProbeError(f"Python/Racket diagnostic mismatch for {name} at {split} {i}")


def _bounded(values, low, high, name):
    if (type(values) is not list or not values or len(values) > 8
            or any(type(value) is not int or not low <= value <= high for value in values)
            or len(set(values)) != len(values)):
        raise ProbeError(f"{name} requires 1..8 distinct exact integers in {low}..{high}")
    return values


def run_probe(out, *, seeds, demo_counts):
    """Audit in memory, then publish a new source-bound review evidence bundle."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"Refusing existing output directory: {out}")
    seeds = _bounded(seeds, 0, 2**63 - 1, "seeds")
    demo_counts = _bounded(demo_counts, 3, 6, "demo counts")
    for module, expected in ((native, ROOT / "src/arcpuzzles/parametric_worker.py"),
                             (visible, RUNTIME / "reviewer_support.py")):
        if Path(module.__file__).resolve() != expected:
            raise ProbeError("Shared evaluator and public serializer must come from this checkout")
    source = _source_inventory()
    episodes, receipts, public_files, inventories = [], [], {}, []
    evaluations = 0
    with native._local_imports(RUNTIME, HERE):
        prototype = _load_prototype()
        settings = copy.deepcopy(list(prototype.SETTINGS))
        if (not 2 <= len(settings) <= 16 or any(type(setting) is not dict for setting in settings)
                or len({_bytes(setting) for setting in settings}) != len(settings)):
            raise ProbeError("SETTINGS must declare 2..16 distinct finite parameter objects")
        candidates = [_candidates(prototype, settings, i) for i in range(len(settings))]
        apply, identity, bridge = native._real_evaluator(RUNTIME)
        def execute(program, grid):
            nonlocal evaluations
            evaluations += 1
            return apply(program, grid)
        try:
            for index, (programs, bindings) in enumerate(candidates):
                inventories.append({"setting_index": index, "settings": settings[index],
                                    "programs": programs, "bindings": bindings})
            for demos in demo_counts:
                for seed in seeds:
                    matched = None
                    for chosen, setting in enumerate(settings):
                        programs, bindings = candidates[chosen]
                        claims = _episode(prototype.generate(seed, copy.deepcopy(setting), demos, QUERIES),
                                          programs["selected"], demos, QUERIES)
                        inputs = [pair["input"] for split in ("train", "test") for pair in claims[split]]
                        if matched is not None and inputs != matched:
                            raise ProbeError(f"Inputs differ between settings for seed {seed}, demos {demos}")
                        matched = copy.deepcopy(inputs)
                        # This call cannot inspect query inputs or labels.
                        fitted, demo_outputs = fit_demonstrations(claims["train"], programs, execute)
                        if not fitted[0]["survives_demos"]:
                            raise ProbeError("Selected Racket program disagrees with Python demonstration claims")
                        if any(row["name"].startswith("setting:") and row["survives_demos"] for row in fitted):
                            raise ProbeError("Demonstrations do not identify the chosen declared setting")
                        for name, outputs in demo_outputs.items():
                            _geometry_parity(prototype, claims["train"], outputs, bindings[name], name, "demonstration")
                        queries, query_outputs = check_queries(claims["test"], programs, fitted, execute)
                        for name, outputs in query_outputs.items():
                            _geometry_parity(prototype, claims["test"], outputs, bindings[name], name, "query")
                        # Export labels are the actual protected-runtime results.
                        episode = {"program_solution": programs["selected"], **{
                            split: [{"input": pair["input"], "output": output}
                                    for pair, output in zip(claims[split], outputs)]
                            for split, outputs in (("train", demo_outputs["selected"]),
                                                   ("test", query_outputs["selected"]))}}
                        one = _episode(prototype.generate(seed, copy.deepcopy(setting), demos, 1),
                                       programs["selected"], demos, 1)
                        projection = first_turn_check(episode, one)
                        payload, public_checks = public_identity_checks(episode)
                        public_id = public_checks["public_id"]
                        if public_id in public_files:
                            raise ProbeError("Duplicate exact visible challenge in export batch")
                        public_files[public_id] = payload
                        intermediates = {split: [prototype.intermediate(copy.deepcopy(pair["input"]))
                                                for pair in episode[split]] for split in ("train", "test")}
                        for row in fitted:
                            row["python_geometry_agrees_on_demos"] = True
                            row["query_agreement"] = queries["candidate_query_agreement"].get(row["name"])
                        receipts.append({"public_id": public_id, "setting_index": chosen, "seed": seed,
                            "counts": {"demos": demos, "queries": QUERIES},
                            "program_sha256": _sha(programs["selected"].encode()),
                            "distinct_inputs": len(inputs), "inputs_matched_across_settings": True,
                            "input_sequence_sha256": _sha(_bytes(inputs)),
                            "finite_candidates": fitted, "per_query_agreement": queries["per_query_agreement"],
                            "first_turn_projection": projection, "public_identity_controls": public_checks,
                            "intermediate_branch_counts": {split: dict(Counter(row["axis"]
                                for row in intermediates[split])) for split in ("train", "test")}})
                        episodes.append({"public_id": public_id, "seed": seed, "settings": copy.deepcopy(setting),
                            "counts": {"demos": demos, "queries": QUERIES}, **episode,
                            "python_claims_sha256": _sha(_bytes(claims)), "all_claims_match_racket": True,
                            "intermediates": intermediates, "candidate_demonstration_outputs": demo_outputs,
                            "surviving_candidate_query_outputs": query_outputs})
            if candidates != [_candidates(prototype, settings, i) for i in range(len(settings))]:
                raise ProbeError("Candidate programs or settings changed during the audit")
            current_identity = bridge.runtime_identity
            if any(current_identity.get(key) != value for key, value in identity.items()):
                raise ProbeError("Protected runtime identity changed during the audit")
        finally:
            bridge.close()
    if _source_inventory() != source:
        raise ProbeError("Source bytes changed during the audit; start a fresh run")
    private = {"schema": SCHEMA, "visibility": "private authoring evidence", "task_id": TASK_ID,
               "source": source, "racket": identity, "candidate_inventories": inventories, "episodes": episodes}
    summary = {"schema": SCHEMA, "status": "pass", "task_id": TASK_ID,
        "evidence_kind": "bounded authoring probe", "accepted": False, "training_admitted": False,
        "seeds": seeds, "demo_counts": demo_counts, "queries": QUERIES,
        "setting_count": len(settings), "episode_count": len(episodes),
        "exported_label_count": sum(len(episode[split]) for episode in episodes for split in ("train", "test")),
        "racket_evaluations": evaluations, "source": source, "racket": identity, "episodes": receipts,
        "limits": ["Only public/*.json is model-visible; the receipt and private.json are authoring evidence.",
                   "Rivals are fitted on demonstrations only; query disagreement fails without refitting.",
                   "Evidence covers the declared finite rivals and requested seeds/counts, not all possible rules.",
                   "This probe neither qualifies nor accepts source and grants no training admission."]}
    # All semantic checks precede publication. An absent final summary means an
    # interrupted/incomplete write, never a completed export. Existing paths fail.
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    files = []
    for public_id, payload in sorted(public_files.items()):
        path = out / "public" / f"{public_id}.json"
        path.write_bytes(payload)
        if path.read_bytes() != payload:
            raise ProbeError("Public bytes changed during publication")
        files.append({"path": path.relative_to(out).as_posix(), "bytes": len(payload), "sha256": public_id})
    private_bytes = _bytes(private)
    private_path = out / "private.json"
    private_path.write_bytes(private_bytes)
    private_path.chmod(0o600)
    if private_path.read_bytes() != private_bytes:
        raise ProbeError("Private evidence changed during publication")
    files.append({"path": "private.json", "bytes": len(private_bytes), "sha256": _sha(private_bytes)})
    summary["files"] = files
    (out / "summary.json").write_bytes(_bytes(summary))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="A new review evidence directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--demos", type=int, nargs="+", default=[3],
                        help="One or more demo counts in 3..6; every episode has four queries")
    options = parser.parse_args(argv)
    try:
        summary = run_probe(options.out, seeds=options.seeds, demo_counts=options.demos)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({key: summary[key] for key in
                      ("status", "episode_count", "exported_label_count", "racket_evaluations")} |
                     {"summary_sha256": _sha((options.out / "summary.json").read_bytes()),
                      "out": str(options.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

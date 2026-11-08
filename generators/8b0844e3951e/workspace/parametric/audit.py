"""Bounded, repeatable authoring audit for the modal-row parameter family.

Run from the outer packet with::

    python3 review.py run python3 \
      generators/8b0844e3951e/workspace/parametric/audit.py --out ../checks/modal-row-audit

The output directory must be new. ``public/`` contains controller-side ARC
challenges, not complete model turns. The existing public serializer is checked
on the first-query projection; downstream consumers own sequential delivery.
All programs, settings, query labels and diagnostics remain private. This
command never performs owner acceptance or training admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys

sys.dont_write_bytecode = True


TASK_ID = "8b0844e3951e"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEEDS = (0, 17, 23)
DEMO_COUNTS = (2, 3, 6)
SCOPES = ("global", "modal_row")
RACKET_RIVALS = (
    "overall_mode", "global_runner_up", "first_row", "last_row",
    "local_including_zero", "modal_column",
)


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _load_prototype():
    """Compile adjacent source bytes; do not reuse a generic prototype cache."""
    source = HERE / "prototype.py"
    body = source.read_bytes()
    name = "_modal_row_audit_prototype_" + _sha(str(source).encode() + body)
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(source), "exec"), module.__dict__)
    return module


def _support():
    runtime = ROOT / "shared/runtime"
    source = runtime / "reviewer_support.py"
    name = "_modal_row_audit_support_" + _sha(str(source).encode())
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("Expected rectangular 1..30 grid with exact integer colors 0..9")
    return deepcopy(grid)


def _fill(grid, color):
    if type(color) is not int or not 0 <= color <= 9:
        raise ValueError("A rival returned an invalid color")
    return [[color] * len(grid[0]) for _ in grid]


def _episode(prototype, seed, scope, demos, queries):
    settings = {"scope": scope}
    episode = prototype.generate(seed, settings, demos, queries)
    if (not isinstance(episode, dict)
            or episode.get("program_solution") != prototype.program(settings)):
        raise ValueError("Generated program_solution differs from program(settings)")
    for split, count in (("train", demos), ("test", queries)):
        if type(episode.get(split)) is not list or len(episode[split]) != count:
            raise ValueError("Independent demo/query request count was not honored")
        for pair in episode[split]:
            _strict_grid(pair["input"])
            _strict_grid(pair["output"])
    inputs = [_raw(pair["input"]) for split in ("train", "test") for pair in episode[split]]
    if len(inputs) != len(set(inputs)):
        raise ValueError("Duplicate demonstration/query input")
    result = deepcopy(episode)
    result.update(seed=seed, settings=settings)
    return result


def _rival_case(prototype, episode, name):
    agreement = {}
    for split in ("train", "test"):
        agreement[split] = [
            _fill(pair["input"], prototype.rival_colors(pair["input"])[name]) == pair["output"]
            for pair in episode[split]
        ]
    return agreement


def _python_screen(prototype):
    aggregates = {scope: {} for scope in SCOPES}
    findings = []
    episodes_checked = 0
    labels_checked = 0
    matched_input_requests = 0
    size_profiles = set()
    for seed in SEEDS:
        for demos in DEMO_COUNTS:
            paired = {scope: _episode(prototype, seed, scope, demos, 4) for scope in SCOPES}
            inputs = {scope: [_raw(p["input"]) for split in ("train", "test")
                              for p in paired[scope][split]] for scope in SCOPES}
            if inputs["global"] != inputs["modal_row"]:
                findings.append({"check": "matched_inputs", "seed": seed, "demos": demos})
            matched_input_requests += 1
            for scope, episode in paired.items():
                episodes_checked += 1
                labels_checked += demos + 4
                names = set(prototype.rival_colors(episode["train"][0]["input"]))
                if not {"global", "modal_row", *RACKET_RIVALS} <= names:
                    raise ValueError("Prototype is missing a declared audit rival")
                for split in ("train", "test"):
                    for pair in episode[split]:
                        rivals = prototype.rival_colors(pair["input"])
                        if set(rivals) != names:
                            raise ValueError("Finite rival names changed between inputs")
                        if _fill(pair["input"], rivals[scope]) != pair["output"]:
                            findings.append({"check": "python_selected_label", "seed": seed,
                                             "demos": demos, "scope": scope, "split": split})
                shapes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
                size_profiles.update(shapes)
                if (shapes[0] != (3, 3) or shapes[3] != (30, 30)
                        or shapes[1] != (8, 13)
                        or not all(21 <= n <= 29 for n in shapes[2])):
                    findings.append({"check": "four_query_size_profiles", "seed": seed,
                                     "demos": demos, "scope": scope, "shapes": shapes})
                for name in sorted(names):
                    agreement = _rival_case(prototype, episode, name)
                    row = aggregates[scope].setdefault(name, {
                        "episodes": 0, "demo_refuted": 0,
                        "demo_survives_queries_agree": 0, "wrong_query_survivors": 0,
                        "pair_disagreements": 0,
                    })
                    row["episodes"] += 1
                    row["pair_disagreements"] += sum(not x for values in agreement.values() for x in values)
                    if not all(agreement["train"]):
                        row["demo_refuted"] += 1
                    elif all(agreement["test"]):
                        row["demo_survives_queries_agree"] += 1
                    else:
                        row["wrong_query_survivors"] += 1
                        findings.append({
                            "check": "demo_fitting_wrong_query_rival", "seed": seed,
                            "demos": demos, "settings": episode["settings"], "rival": name,
                            "train": episode["train"],
                            "test": [pair for pair, agrees in zip(episode["test"], agreement["test"])
                                     if not agrees],
                        })
    return {
        "backend": "python_mirror", "seeds": list(SEEDS),
        "demonstration_counts": list(DEMO_COUNTS), "queries": 4,
        "episodes_checked": episodes_checked, "pair_labels_screened": labels_checked,
        "matched_input_requests": matched_input_requests,
        "query_shapes": [list(shape) for shape in sorted(size_profiles)],
        "rivals": aggregates,
        "wrong_query_survivors": sum(row["wrong_query_survivors"]
                                     for scope in aggregates.values() for row in scope.values()),
        "limits": "Python finite-rival screen only; independent protected Racket coverage is reported separately.",
    }, findings


def _rank(values, excluded, default=0):
    counts = Counter(value for value in values if value not in excluded)
    return min(counts, key=lambda color: (-counts[color], color)) if counts else default


def _independent_rival_colors(grid):
    """Independent, explicit semantics mirrored by the Racket wrappers below."""
    flat = [color for row in grid for color in row]
    mode = _rank(flat, {0})
    selected_row = max(range(len(grid)), key=lambda index: grid[index].count(mode))
    selected_col = max(range(len(grid[0])), key=lambda index: sum(row[index] == mode for row in grid))
    return {
        "overall_mode": _rank(flat, set()),
        "global_runner_up": _rank(flat, {0, mode}, mode),
        "first_row": _rank(grid[0], {0, mode}, mode),
        "last_row": _rank(grid[-1], {0, mode}, mode),
        "local_including_zero": _rank(grid[selected_row], {mode}, mode),
        "modal_column": _rank([row[selected_col] for row in grid], {0, mode}, mode),
    }


def rival_program(name):
    """Standalone rivals; color ties use the smallest color, position ties first."""
    expressions = {
        "overall_mode": "(winner flat (list) 0)",
        "global_runner_up": "(winner flat (list 0 m) m)",
        "first_row": "(winner (first g) (list 0 m) m)",
        "last_row": "(winner (last g) (list 0 m) m)",
        "local_including_zero": "(winner (list-ref g ri) (list m) m)",
        "modal_column": "(winner (for/list ([row (in-list g)]) (list-ref row ci)) (list 0 m) m)",
    }
    if name not in expressions:
        raise ValueError("Undeclared protected-Racket rival")
    return """(rule!
      (let* ([flat (apply append g)]
             [winner
               (lambda (values excluded fallback)
                 (let ([colors (filter (lambda (v) (not (member v excluded)))
                                       (sort (remove-duplicates values) <))])
                   (if (empty? colors) fallback
                     (first (sort colors
                       (lambda (a b)
                         (let ([ca (count (lambda (v) (= v a)) values)]
                               [cb (count (lambda (v) (= v b)) values)])
                           (or (> ca cb) (and (= ca cb) (< a b))))))))))]
             [m (winner flat (list 0) 0)]
             [ri (argmax (lambda (r) (count (lambda (v) (= v m)) (list-ref g r)))
                         (range (rows g)))]
             [ci (argmax (lambda (c) (for/sum ([row (in-list g)])
                                       (if (= (list-ref row c) m) 1 0)))
                         (range (cols g)))]
             [answer """ + expressions[name] + """])
        (empty-grid (rows g) (cols g) answer)))"""


def _protected_checks(prototype, episodes):
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    runtime = ROOT / "shared/runtime"
    findings = []
    cache = {}
    label_rows = []
    rival_rows = []
    endpoint_rows = []
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            def execute(program, grid):
                key = (_sha(program.encode()), _sha(_raw(grid)))
                if key not in cache:
                    cache[key] = _strict_grid(apply(program, deepcopy(grid)))
                return deepcopy(cache[key])

            for episode in episodes:
                scope = episode["settings"]["scope"]
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = execute(episode["program_solution"], pair["input"])
                        correct = actual == pair["output"]
                        label_rows.append({"scope": scope, "split": split, "pair_index": index,
                                           "input_sha256": _sha(_raw(pair["input"])),
                                           "output_sha256": _sha(_raw(actual)), "matched": correct})
                        if not correct:
                            findings.append({"check": "racket_reference_label", "scope": scope,
                                             "split": split, "pair_index": index,
                                             "input": pair["input"], "expected": pair["output"],
                                             "actual": actual})
                candidates = {**{s: prototype.program({"scope": s}) for s in SCOPES},
                              **{name: rival_program(name) for name in RACKET_RIVALS}}
                for name, program in candidates.items():
                    agreement = {}
                    for split in ("train", "test"):
                        agreement[split] = []
                        for index, pair in enumerate(episode[split]):
                            actual = execute(program, pair["input"])
                            agreement[split].append(actual == pair["output"])
                            if name in RACKET_RIVALS:
                                independent = _independent_rival_colors(pair["input"])[name]
                                declared = prototype.rival_colors(pair["input"])[name]
                                if actual != _fill(pair["input"], independent) or independent != declared:
                                    findings.append({"check": "independent_rival_parity", "scope": scope,
                                                     "rival": name, "split": split, "pair_index": index,
                                                     "independent_color": independent, "declared_color": declared,
                                                     "racket_output": actual, "input": pair["input"]})
                    demo_fit = all(agreement["train"])
                    wrong_query = not all(agreement["test"])
                    rival_rows.append({"scope": scope, "rival": name,
                                       "program_sha256": _sha(program.encode()),
                                       "demo_agreement": agreement["train"],
                                       "query_agreement": agreement["test"],
                                       "status": "ambiguous" if demo_fit and wrong_query else
                                                 "support_equivalent" if demo_fit else "demo_refuted"})
                    if demo_fit and wrong_query:
                        findings.append({"check": "racket_wrong_query_survivor", "scope": scope,
                                         "rival": name, "program": program, "episode": episode})
                finite = [row["rival"] for row in rival_rows
                          if row["scope"] == scope and row["rival"] in SCOPES
                          and all(row["demo_agreement"])]
                if finite != [scope]:
                    findings.append({"check": "racket_setting_identification",
                                     "scope": scope, "survivors": finite})
            for seed, demos, queries in ((31, 2, 1), (37, 6, 4)):
                for scope in SCOPES:
                    episode = _episode(prototype, seed, scope, demos, queries)
                    matched = 0
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            actual = execute(episode["program_solution"], pair["input"])
                            if actual == pair["output"]:
                                matched += 1
                            else:
                                findings.append({"check": "racket_endpoint_label", "scope": scope,
                                                 "seed": seed, "demos": demos, "queries": queries,
                                                 "input": pair["input"], "actual": actual,
                                                 "expected": pair["output"]})
                    endpoint_rows.append({"seed": seed, "scope": scope, "demos": demos,
                                          "queries": queries, "labels_matched": matched,
                                          "labels_checked": demos + queries,
                                          "query_shapes": [[len(p["input"]), len(p["input"][0])]
                                                           for p in episode["test"]]})
        finally:
            bridge.close()
    return {
        "racket": identity, "actual_evaluations": len(cache),
        "reference_labels": label_rows, "rivals": rival_rows, "count_endpoints": endpoint_rows,
        "rival_programs": {name: rival_program(name) for name in RACKET_RIVALS},
        "limits": "All labels of two 3-demo/4-query episodes, six independent rivals, two setting programs, and four endpoint episodes. Finite sampled evidence only.",
    }, findings


def _privacy_and_reveal(prototype, episodes):
    support = _support()
    findings = []
    records = []
    for episode in episodes:
        scope = episode["settings"]["scope"]
        payload = support.public_challenge_bytes(episode)
        identifier = support.public_challenge_id(episode)
        changed = deepcopy(episode)
        changed.update(seed=999999, settings={"private": "changed"},
                       program_solution="private changed text", program="other private text",
                       provenance={"different": True})
        for pair in changed["test"]:
            pair["output"] = [[(cell + 1) % 10 for cell in row] for row in pair["output"]]
            pair["private_annotation"] = "changed"
        invariant = (payload == support.public_challenge_bytes(changed)
                     and identifier == support.public_challenge_id(changed))
        if not invariant:
            findings.append({"check": "private_field_public_identity", "scope": scope})
        one = _episode(prototype, episode["seed"], scope, len(episode["train"]), 1)
        first_four = support.public_challenge_bytes({"train": episode["train"],
                                                     "test": episode["test"][:1]})
        first_one = support.public_challenge_bytes(one)
        if first_four != first_one:
            findings.append({"check": "one_four_first_turn_equivalence", "scope": scope})
        expected = {"train": json.loads(payload)["train"],
                    "test": [{"input": episode["test"][0]["input"]}]}
        if json.loads(first_four) != expected:
            findings.append({"check": "first_query_exact_public_projection", "scope": scope})
        changed_future = deepcopy(episode)
        for pair in changed_future["test"][1:]:
            pair.update(input=[[9]], output=[[8]])
        future_invariant = first_four == support.public_challenge_bytes({
            "train": changed_future["train"], "test": changed_future["test"][:1]})
        if not future_invariant:
            findings.append({"check": "future_query_first_turn_invariance", "scope": scope})
        records.append({"scope": scope, "public_id": identifier,
                        "private_field_mutation_invariant": invariant,
                        "one_four_first_turn_equal": first_one == first_four,
                        "first_turn_sha256": _sha(first_four),
                        "future_query_mutation_invariant": future_invariant,
                        "first_turn_projection": "demonstrations + first query input only; no counts, ordinals, future inputs, settings, query answers, or programs"})
    return {"records": records, "projection_helper": "reviewer_support.public_challenge_bytes",
            "public_container_role": "Controller data; never dump the four-query container into a model turn.",
            "limits": "Initial projection equality and privacy only. Actual downstream answer-gated sequencing is neither implemented nor exercised by this authoring audit."}, findings


def _export(output, episodes):
    support = _support()
    planned = sorted(((support.public_challenge_id(episode),
                       support.public_challenge_bytes(episode), episode) for episode in episodes),
                     key=lambda row: row[0])
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("Duplicate visible public challenge")
    (output / "public").mkdir(parents=True)
    (output / "private").mkdir()
    private_rows = []
    for identifier, payload, episode in planned:
        (output / "public" / (identifier + ".json")).write_bytes(payload)
        private_rows.append({"episode_id": identifier, **episode})
    (output / "private" / "episodes.json").write_bytes(_raw(private_rows))
    for identifier, payload, _ in planned:
        saved = (output / "public" / (identifier + ".json")).read_bytes()
        if saved != payload or _sha(saved) != identifier:
            raise ValueError("Saved public challenge bytes/identity changed")
    return [{"path": "public/" + identifier + ".json", "sha256": identifier}
            for identifier, _, _ in planned]


def run(output):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Choose a new audit output directory: " + str(output))
    prototype = _load_prototype()
    before = {path.name: _sha(path.read_bytes()) for path in HERE.iterdir()
              if path.is_file() and path.suffix in {".py", ".rkt", ".json"}}
    python_report, findings = _python_screen(prototype)
    episodes = [_episode(prototype, 17, scope, 3, 4) for scope in SCOPES]
    protected, extra = _protected_checks(prototype, episodes)
    findings.extend(extra)
    privacy, extra = _privacy_and_reveal(prototype, episodes)
    findings.extend(extra)
    after = {path.name: _sha(path.read_bytes()) for path in HERE.iterdir()
             if path.is_file() and path.suffix in {".py", ".rkt", ".json"}}
    if before != after:
        raise ValueError("Prototype source changed while the audit ran")
    public_files = _export(output, episodes)
    witness_pairs = [episode["test"][0] for episode in episodes]
    cross_setting = {
        "schema": "arcpuzzles-modal-row-setting-difference-v1",
        "input": witness_pairs[0]["input"],
        "matched_inputs": witness_pairs[0]["input"] == witness_pairs[1]["input"],
        "different_outputs": witness_pairs[0]["output"] != witness_pairs[1]["output"],
        "settings": [episode["settings"] for episode in episodes],
        "programs": [episode["program_solution"] for episode in episodes],
        "outputs": [pair["output"] for pair in witness_pairs],
        "intermediate": prototype.analyze(witness_pairs[0]["input"]),
        "reference_evidence": "protected-racket.json reference_labels: test pair_index 0 for each setting",
    }
    if not cross_setting["matched_inputs"] or not cross_setting["different_outputs"]:
        findings.append({"check": "shared_input_different_outputs"})
    (output / "private" / "setting-difference.json").write_bytes(_raw(cross_setting))
    (output / "private" / "protected-racket.json").write_bytes(_raw(protected))
    (output / "private" / "privacy-reveal.json").write_bytes(_raw(privacy))
    (output / "private" / "findings.json").write_bytes(_raw(findings))
    report = {
        "schema": "arcpuzzles-modal-row-authoring-audit-v1", "task_id": TASK_ID,
        "status": "passed" if not findings else "failed", "source_sha256": before,
        "invocation": shlex.join([sys.executable, *sys.argv]),
        "cwd": str(Path.cwd()), "python_screen": python_report,
        "protected_racket": {
            "runtime": protected["racket"], "actual_evaluations": protected["actual_evaluations"],
            "exported_reference_labels": len(protected["reference_labels"]),
            "independent_rivals": list(RACKET_RIVALS),
            "setting_programs": list(SCOPES), "endpoint_jobs": protected["count_endpoints"],
            "evidence": "private/protected-racket.json",
        },
        "public_files": public_files, "privacy_and_sequential_reveal": privacy,
        "findings": len(findings), "findings_path": "private/findings.json",
        "owner_acceptance": "not_performed", "training_admitted": False,
        "limits": "Finite sampled demonstrations, rivals and endpoints only. Python screening is separated from protected-Racket execution. No universal identifiability, measured learning benefit, owner acceptance, or training admission is claimed.",
    }
    (output / "report.json").write_bytes(_raw(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    try:
        report = run(args.out)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("modal-row audit: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "report": str((args.out / "report.json").absolute()),
                      "python_episodes": report["python_screen"]["episodes_checked"],
                      "wrong_query_survivors": report["python_screen"]["wrong_query_survivors"],
                      "protected_racket_evaluations": report["protected_racket"]["actual_evaluations"],
                      "findings": report["findings"], "owner_acceptance": "not_performed"}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

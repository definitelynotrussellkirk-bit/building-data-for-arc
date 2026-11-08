"""Bounded protected-Racket teaching, label and public-export evidence.

Run through review.py from the packet's outer directory. This authoring audit
does not accept the family or admit training data. All retained labels and all
declared rival predictions are obtained from this checkout's protected Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import tempfile
import time


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = "8811ea806605"
MODES = ("fall", "fall_then_clear", "clear_then_fall")
SEEDS = (0, 17)
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes, public_challenge_id


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def require_new(path):
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Choose a new audit destination: {path}")


def load_prototype():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("_gravity_audit_" + digest(path.read_bytes()), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sources():
    paths = [HOME / name for name in ("audit.py", "adapter.py", "prototype.py", "promotion.json", "canonical.rkt")]
    paths.extend(ROOT / name for name in (
        f"generators/{TASK}/generator.py", "shared/runtime/reviewer_support.py",
        "shared/runtime/puzzle_generators/rule_wrap.py", "shared/tools/comment_solutions.py",
        "src/arcpuzzles/parametric_worker.py"))
    return [{"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path.read_bytes()),
             "bytes": path.stat().st_size} for path in sorted(paths)]


_RACKET = """(rule!
 (lambda (g)
  (let ()
   (define (columns x)
     (map (lambda (c) (count-where (lambda (r) (= (at x r c) 1)) (range h))) (range w)))
   (define (pack cs)
     (grid-from-fn h w (lambda (r c) (if (>= r (- h (list-ref cs c))) 1 0))))
   (define (top-pack cs)
     (grid-from-fn h w (lambda (r c) (if (< r (list-ref cs c)) 1 0))))
   (define (fall x) (pack (columns x)))
   (define (full-row row) (= (count-where (lambda (v) (= v 1)) row) w))
   (define (full-at r) (full-row (list-ref g r)))
   (define (clear-near x)
     (let* ((kept (filter (lambda (row) (< (count-where (lambda (v) (= v 1)) row) (- w 1))) x))
            (lost (- h (length kept))))
       (append (make-list lost (make-list w 0)) kept)))
   (let* ((counts (columns g))
          (k (count-where full-row g))
          (m (apply min counts)))
     (let ()
       (define (subtract n) (map (lambda (v) (max 0 (- v n))) counts))
       EXPRESSION)))))"""


def racket(expression):
    return _RACKET.replace("EXPRESSION", expression)


def histogram(grid):
    return [sum(row[c] for row in grid) for c in range(len(grid[0]))]


def packed(counts, height, top=False):
    return [[int(r < n if top else r >= height - n) for n in counts] for r in range(height)]


def subtracted(counts, amount):
    return [max(0, value - amount) for value in counts]


def base_counts(grid, mode):
    counts = histogram(grid)
    amount = 0 if mode == "fall" else (min(counts) if mode == "fall_then_clear" else sum(all(row) for row in grid))
    return subtracted(counts, amount)


def near_clear(grid):
    width = len(grid[0])
    kept = [row[:] for row in grid if sum(row) < width - 1]
    return [[0] * width for _ in range(len(grid) - len(kept))] + kept


def rivals(proto):
    result = []

    def add(name, program, mirror, description):
        result.append({"name": name, "program": program, "mirror": mirror, "description": description})

    base_expressions = {"fall": "counts", "fall_then_clear": "(subtract m)", "clear_then_fall": "(subtract k)"}
    for mode in MODES:
        add(mode, proto.program({"mode": mode}), lambda g, mode=mode: proto.transform(g, mode), "Declared setting")
        expression = base_expressions[mode]
        for transform, operation in (("top", f"(top-pack {expression})"),
                                     ("cap4", f"(pack (map (lambda (v) (min 4 v)) {expression}))"),
                                     ("sorted", f"(pack (sort {expression} <))"),
                                     ("reversed", f"(pack (reverse {expression}))")):
            def mirror(grid, mode=mode, transform=transform):
                counts = base_counts(grid, mode)
                if transform == "cap4": counts = [min(4, n) for n in counts]
                if transform == "sorted": counts = sorted(counts)
                if transform == "reversed": counts = list(reversed(counts))
                return packed(counts, len(grid), top=transform == "top")
            add(f"{mode}_{transform}", racket(operation), mirror, f"{mode} with {transform} histogram rendering")

    add("identity", "(rule! (lambda (g) g))", lambda g: copy.deepcopy(g), "Return the original grid")
    for mode, symbol in (("fall_then_clear", "m"), ("clear_then_fall", "k")):
        for cap in range(1, 7):
            def mirror(grid, mode=mode, cap=cap):
                counts = histogram(grid)
                number = min(counts) if mode == "fall_then_clear" else sum(all(row) for row in grid)
                return packed(subtracted(counts, min(cap, number)), len(grid))
            add(f"{mode}_clear_at_most_{cap}", racket(f"(pack (subtract (min {cap} {symbol})))"),
                mirror, f"Clear at most {cap} rows in {mode}")

    for mode, symbol, amount in (("fall_then_clear", "m", 7), ("clear_then_fall", "k", 3)):
        def mirror(grid, mode=mode, amount=amount):
            counts = histogram(grid)
            number = min(counts) if mode == "fall_then_clear" else sum(all(row) for row in grid)
            return packed(subtracted(counts, amount if number else 0), len(grid))
        add(f"{mode}_fixed_positive_{amount}", racket(f"(pack (subtract (if (> {symbol} 0) {amount} 0)))"),
            mirror, f"Subtract fixed {amount} whenever any clearing is triggered")

    def positive_minimum(grid):
        counts = histogram(grid)
        positive = [n for n in counts if n]
        return packed(subtracted(counts, min(positive) if positive else 0), len(grid))
    add("fall_then_clear_ignore_empty_columns", racket("(let ((positive (filter (lambda (n) (> n 0)) counts))) (pack (subtract (if (null? positive) 0 (apply min positive)))))"),
        positive_minimum, "Use the minimum positive column count, ignoring empty columns")
    add("clear_nearly_full_then_fall", racket("(fall (clear-near g))"),
        lambda g: proto.fall(near_clear(g)), "Clear original rows with at least width minus one blue cells")
    add("fall_then_clear_nearly_full", racket("(clear-near (fall g))"),
        lambda g: near_clear(proto.fall(g)), "Clear fallen rows with at least width minus one blue cells")
    add("fall_then_zero_full_rows_in_place", racket("(map (lambda (row) (if (full-row row) (make-list w 0) row)) (fall g))"),
        lambda g: [[0] * len(g[0]) if all(row) else row[:] for row in proto.fall(g)],
        "Erase full fallen rows without compacting the retained rows")
    for name, condition, keep_index in (
        ("ignore_top_full_row", "(> r 0)", lambda i, h: i > 0),
        ("ignore_bottom_full_row", "(< r (- h 1))", lambda i, h: i < h - 1),
        ("interior_full_rows_only", "(and (> r 0) (< r (- h 1)))", lambda i, h: 0 < i < h - 1),
    ):
        def mirror(grid, keep_index=keep_index):
            count = sum(all(row) and keep_index(i, len(grid)) for i, row in enumerate(grid))
            return packed(subtracted(histogram(grid), count), len(grid))
        add(f"clear_then_fall_{name}", racket(f"(pack (subtract (count-where (lambda (r) (and {condition} (full-at r))) (range h))))"),
            mirror, "Clear before falling, but " + name.replace("_", " "))
    assert len(result) == 37 and len({row["name"] for row in result}) == len(result)
    return result


class Executor:
    def __init__(self, apply, proto):
        self.apply, self.proto = apply, proto
        self.cache = {}
        self.calls = 0
        self.requests = 0
        self.mirror_comparisons = 0

    def __call__(self, program, grid, expected=None):
        self.requests += 1
        self.proto.validate_grid(grid)
        key = (digest(program.encode("utf-8")), digest(raw(grid)))
        if key not in self.cache:
            result = _grid(self.apply(program, copy.deepcopy(grid)))
            self.proto.validate_grid(result)
            self.cache[key] = result
            self.calls += 1
        result = self.cache[key]
        if expected is not None:
            _grid(expected)
            self.proto.validate_grid(expected)
            if result != expected:
                raise AssertionError(f"Racket/mirror mismatch for program {key[0]} and input {key[1]}")
            self.mirror_comparisons += 1
        return copy.deepcopy(result)


def labeled_episode(proto, execute, seed, mode, demos, queries):
    claimed = proto.generate(seed, {"mode": mode}, demos, queries)
    result = {"task_id": TASK, "seed": seed, "settings": {"mode": mode},
              "program_solution": claimed["program_solution"], "label_authority": "protected_racket"}
    for split, count in (("train", demos), ("test", queries)):
        assert len(claimed[split]) == count
        result[split] = [{"input": copy.deepcopy(pair["input"]),
                          "output": execute(result["program_solution"], pair["input"], pair["output"])}
                         for pair in claimed[split]]
    inputs = [raw(pair["input"]) for split in ("train", "test") for pair in result[split]]
    assert len(inputs) == len(set(inputs))
    return result


def assess(train, query_inputs, selected_program, declared, execute):
    """Fit on demonstrations; query labels are deliberately absent from this API."""
    survivors, rejected, disagreements = [], [], []
    expected_queries = [execute(selected_program, grid) for grid in query_inputs]
    for rival in declared:
        predicted = [execute(rival["program"], pair["input"], rival["mirror"](pair["input"])) for pair in train]
        mismatches = [i for i, (prediction, pair) in enumerate(zip(predicted, train)) if prediction != pair["output"]]
        survives = not mismatches
        if survives: survivors.append(rival["name"])
        else: rejected.append({"name": rival["name"], "first_demo_mismatch": mismatches[0]})
        for index, (grid, expected) in enumerate(zip(query_inputs, expected_queries)):
            prediction = execute(rival["program"], grid, rival["mirror"](grid))
            if survives and prediction != expected:
                disagreements.append({"rival": rival["name"], "query_index": index})
    if disagreements:
        raise AssertionError("Demonstration-consistent rivals disagree on queries: " + json.dumps(disagreements))
    return {"survivors": survivors, "rejected": rejected, "query_disagreements": disagreements,
            "rivals_tested": len(declared), "query_inputs_checked": len(query_inputs),
            "query_answers_used_for_fitting": False}


def public_plan(episodes):
    planned = []
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        assert digest(payload) == identifier
        planned.append((identifier, payload, episode))
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("Duplicate visible public payload")
    return sorted(planned, key=lambda row: row[0])


def export_regressions(proto, episode):
    before = public_challenge_bytes(episode)
    mutated = copy.deepcopy(episode)
    mutated.update(seed=-999, settings={"private": "changed"}, program_solution="changed private program",
                   private_metadata={"arbitrary": True})
    for pair in mutated["test"]: pair["output"] = [[9]]
    assert public_challenge_bytes(mutated) == before
    assert public_challenge_id(mutated) == public_challenge_id(episode)
    first = proto.public_view(episode, 0)
    for pair in mutated["test"][1:]: pair["input"] = [[8]]
    assert proto.public_view(mutated, 0) == first
    visible = json.loads(first)
    assert set(visible) == {"train", "test"} and len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    try:
        public_plan([episode, copy.deepcopy(episode)])
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate visible payload accepted")
    with tempfile.TemporaryDirectory(prefix="gravity-audit-existing-") as temp:
        try:
            require_new(Path(temp))
        except FileExistsError:
            pass
        else:
            raise AssertionError("Existing output directory accepted")
    return {"private_metadata_and_query_answer_invariance": True,
            "future_input_and_answer_first_turn_invariance": True,
            "public_ids_hash_exact_visible_bytes": True, "duplicate_payload_rejected": True,
            "existing_destination_rejected": True, "first_turn_has_exactly_one_input_only_query": True}


def weak_lesson(episodes, declared, execute):
    episode = next(ep for ep in episodes if ep["seed"] == 0 and ep["settings"]["mode"] == "fall_then_clear")
    rival = next(row for row in declared if row["name"] == "fall_then_clear_fixed_positive_7")
    for pair in episode["train"][:2]:
        assert execute(rival["program"], pair["input"], rival["mirror"](pair["input"])) == pair["output"]
    restored = episode["train"][2]
    wrong_restored = execute(rival["program"], restored["input"], rival["mirror"](restored["input"]))
    assert wrong_restored != restored["output"]
    query = episode["test"][0]
    actual = execute(episode["program_solution"], query["input"])
    wrong = execute(rival["program"], query["input"], rival["mirror"](query["input"]))
    assert actual != wrong
    return {"schema": "arcpuzzles-bounded-weak-lesson-v1", "seed": 0,
            "settings": episode["settings"], "omitted_demo_index": 2,
            "rival_name": rival["name"], "program": episode["program_solution"],
            "rival_program": rival["program"], "weak_train": episode["train"][:2],
            "restored_demo": restored, "rival_restored_output": wrong_restored,
            "query_input": query["input"], "output": actual, "rival_output": wrong,
            "rival_survives_first_two_demos": True, "first_query_disagrees": True,
            "third_demo_rejects_rival": True, "query_answers_used_for_fitting": False}


def run(output):
    require_new(output)
    started = time.monotonic()
    binding = sources()
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK)
    authority = row.get("rule_task_id", TASK)
    canonical = {value["program_solution"] for value in catalog._variants()[authority]}
    with _local_imports(ROOT / "shared/runtime", HOME):
        proto = load_prototype()
        assert canonical == {proto.program({"mode": "fall"})}
        declared = rivals(proto)
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        assert identity["backend"] == "racket" and identity["protected"] is True
        execute = Executor(apply, proto)
        try:
            episodes = [labeled_episode(proto, execute, seed, mode, 3, 4) for seed in SEEDS for mode in MODES]
            for seed in SEEDS:
                matched = [ep for ep in episodes if ep["seed"] == seed]
                for split in ("train", "test"):
                    assert all([p["input"] for p in ep[split]] == [p["input"] for p in matched[0][split]] for ep in matched)
            teaching = []
            for episode in episodes:
                result = assess(episode["train"], [p["input"] for p in episode["test"]],
                                episode["program_solution"], declared, execute)
                assert episode["settings"]["mode"] in result["survivors"]
                teaching.append({"episode_id": public_challenge_id(episode), "seed": episode["seed"],
                                 "settings": episode["settings"], **result})
            weak = weak_lesson(episodes, declared, execute)
            regressions = export_regressions(proto, episodes[0])
            matrix = []
            for seed in SEEDS:
                for mode in MODES:
                    reference = next(ep for ep in episodes if ep["seed"] == seed and ep["settings"]["mode"] == mode)
                    for demos, queries in ((3, 1), (6, 8)):
                        episode = labeled_episode(proto, execute, seed, mode, demos, queries)
                        assert episode["train"][:3] == reference["train"]
                        assert episode["test"][:min(queries, 4)] == reference["test"][:min(queries, 4)]
                        surviving = [candidate for candidate in MODES
                                     if all(execute(proto.program({"mode": candidate}), pair["input"],
                                                    proto.transform(pair["input"], candidate)) == pair["output"]
                                            for pair in episode["train"])]
                        assert surviving == [mode]
                        if demos == 3:
                            assert proto.public_view(episode, 0) == proto.public_view(reference, 0)
                        matrix.append({"seed": seed, "settings": {"mode": mode}, "demos": demos,
                                       "queries": queries, "labels_checked": demos + queries,
                                       "surviving_modes": surviving, "episode_sha256": digest(raw(episode)),
                                       "shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["train"] + episode["test"]]})
            boundaries = []
            for value in (0, 1):
                grid = [[value] * 5 for _ in range(5)]
                for mode in MODES:
                    expected = [[value if mode == "fall" else 0] * 5 for _ in range(5)]
                    actual = execute(proto.program({"mode": mode}), grid, expected)
                    boundaries.append({"case": "all_zero" if value == 0 else "all_one",
                                       "settings": {"mode": mode}, "input": grid, "output": actual})
            views = []
            for episode in episodes:
                turns = []
                for index in range(4):
                    payload = proto.public_view(episode, index)
                    visible = json.loads(payload)
                    assert set(visible) == {"train", "test"} and len(visible["test"]) == 1
                    assert set(visible["test"][0]) == {"input"}
                    assert visible["test"][0]["input"] == episode["test"][index]["input"]
                    turns.append({"query_index_private": index, "view_sha256": digest(payload), "visible_queries": 1})
                views.append({"episode_id": public_challenge_id(episode), "turns": turns})
            assert binding == sources(), "Audit source changed during execution"
            report = {"schema": "arcpuzzles-gravity-line-clear-audit-v1", "status": "passed", "task_id": TASK,
                      "command": shlex.join([sys.executable, *sys.argv]), "cwd": str(Path.cwd().resolve()),
                      "source_files": binding, "generator_sha256": row["generator_sha256"],
                      "canonical_rule_hash": row["rule_hash"], "rule_task_id": authority,
                      "canonical_program_sha256": digest(next(iter(canonical)).encode()),
                      "racket": identity, "racket_evaluations": execute.calls,
                      "evaluation_requests": execute.requests, "mirror_comparisons": execute.mirror_comparisons,
                      "rival_count": len(declared), "retained_episodes": len(episodes),
                      "teaching": teaching, "matched_inputs_across_settings": True,
                      "count_request_matrix": matrix, "count_and_first_query_prefixes_stable": True,
                      "export_regressions": regressions, "sequential_views": views,
                      "weak_lesson": "weak-lesson.private.json", "boundaries": boundaries,
                      "elapsed_seconds": round(time.monotonic() - started, 3),
                      "training_admitted": False, "native_acceptance": False,
                      "limits": "Only the 37 named rivals, two seeds, declared count requests and literal boundaries. No universal identifiability, semantic-depth proof, owner acceptance or training admission. Cache reuses identical executed program/input pairs."}
        finally:
            bridge.close()
    planned = public_plan(episodes)
    require_new(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".gravity-audit-", dir=output.parent) as temporary:
        stage = Path(temporary)
        (stage / "public").mkdir()
        (stage / "first-turns").mkdir()
        private = []
        for identifier, payload, episode in planned:
            (stage / "public" / f"{identifier}.json").write_bytes(payload)
            first = proto.public_view(episode, 0)
            (stage / "first-turns" / f"{digest(first)}.json").write_bytes(first)
            private.append({"episode_id": identifier, **episode})
        (stage / "episodes.private.json").write_bytes(raw(private))
        (stage / "rivals.private.json").write_bytes(raw([
            {"name": r["name"], "description": r["description"], "program": r["program"],
             "program_sha256": digest(r["program"].encode())} for r in declared]))
        (stage / "weak-lesson.private.json").write_bytes(raw(weak))
        (stage / "audit.json").write_bytes(raw(report))
        inventory = [{"path": p.relative_to(stage).as_posix(), "sha256": digest(p.read_bytes()), "bytes": p.stat().st_size}
                     for p in sorted(stage.rglob("*")) if p.is_file()]
        (stage / "manifest.json").write_bytes(raw({"schema": "arcpuzzles-task-audit-export-v1", "status": "complete",
            "public_ids": [entry[0] for entry in planned], "files": inventory,
            "public_data_role": "Controller containers hold four queries; model turns use only first-turns or public_view.",
            "training_admitted": False}))
        require_new(output)
        output.mkdir()
        for path in sorted(stage.iterdir(), key=lambda p: (p.name == "manifest.json", p.name)):
            path.rename(output / path.name)
    return {"status": "passed", "output": str(output), "audit": str(output / "audit.json"),
            "rival_count": len(declared), "retained_episodes": len(episodes),
            "racket_evaluations": report["racket_evaluations"], "count_requests": len(matrix),
            "elapsed_seconds": report["elapsed_seconds"], "training_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    result = run(options.out.absolute())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

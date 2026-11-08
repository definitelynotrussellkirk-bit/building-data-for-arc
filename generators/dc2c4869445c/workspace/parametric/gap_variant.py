#!/usr/bin/env python3
"""Separate authoring prototype: translate each canonical mirror outward by gap.

The selected generator and rule remain authoritative and unchanged by this
module. All emitted labels and parameter-rival predictions use real Racket.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
    normalize_grid,
)


TASK_ID = "dc2c4869445c"
ROOT = find_root(__file__)
ALLOWED_GAPS = (0, 1, 2)
DEFAULT_GAP = 0
PROTOTYPE_VERSION = "1.0.0"


def public_filename(challenge):
    """Hash only visible inputs and demonstration labels, never private metadata."""
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in challenge["train"]],
               "test": [{"input": p["input"]} for p in challenge["test"]]}
    raw = json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()
    return "challenge-" + hashlib.sha256(raw).hexdigest() + ".json"


def json_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def text_sha256(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _integer(value, name, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi}; got {value!r}")
    return value


def _gap(value):
    return _integer(value, "gap", 0, 2)


@lru_cache(maxsize=1)
def selected_generator():
    return load_selected_generator(TASK_ID, root=ROOT)


@lru_cache(maxsize=1)
def canonical_program():
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError("canonical variant is missing its Racket program")
                programs.append(program)
    if not programs or len({" ".join(p.split()) for p in programs}) != 1:
        raise ValueError("expected one unambiguous canonical Racket authority")
    return programs[0]


def program_for_gap(gap=DEFAULT_GAP):
    """Materialize native Racket, preserving canonical bytes exactly at gap=0.

    The four guarded replacements are translations of the existing coordinate
    expressions. A changed authority shape fails explicitly rather than guessing.
    """
    _gap(gap)
    source = canonical_program()
    coordinates = (
        ("(- (- (* 2 mr1) 1) mr)", "-"),
        ("(- (+ (* 2 mr2) 1) mr)", "+"),
        ("(- (- (* 2 mc1) 1) mcl)", "-"),
        ("(- (+ (* 2 mc2) 1) mcl)", "+"),
    )
    for expression, direction in coordinates:
        if source.count(expression) != 1:
            raise ValueError(f"canonical coordinate expression changed: {expression}")
        if gap:
            source = source.replace(expression, f"({direction} {expression} {gap})")
    return source


def callable_for_gap(gap=DEFAULT_GAP):
    """The exact native lambda evaluated by this prototype, distinct from rule! text."""
    body = strip_rule_wrapper(program_for_gap(gap))
    if not body.startswith("(lambda (g)") or any(x in body for x in (";", "{", "}")):
        raise ValueError("prototype needs the known native canonical lambda form")
    return body


def bridge_definition_for_gap(gap=DEFAULT_GAP):
    """Exact definition string passed to RacketBridge.eval_text before transport."""
    return f"(define __gap_{_gap(gap)} {callable_for_gap(gap)})"


def _program_hashes(gap):
    return {"program_sha256": text_sha256(program_for_gap(gap)),
            "callable_sha256": text_sha256(callable_for_gap(gap)),
            "bridge_definition_sha256": text_sha256(bridge_definition_for_gap(gap))}


def gap_from_seed(seed, *, episode_index=0):
    """Choose one episode-level value without consulting or altering global RNG."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(episode_index, "episode_index", 0, 2**31 - 1)
    digest = text_sha256(f"{TASK_ID}:gap:{PROTOTYPE_VERSION}:{seed}:{episode_index}")
    return ALLOWED_GAPS[int(digest, 16) % len(ALLOWED_GAPS)]


def _paints(grid, gap):
    generator = selected_generator()[0]
    for gi, cells in enumerate(generator._groups8(grid)):
        _, main, seeds = generator._group_parts(grid, cells)
        r0, r1 = min(r for r, c in main), max(r for r, c in main)
        c0, c1 = min(c for r, c in main), max(c for r, c in main)
        for sr, sc in seeds:
            color = grid[sr][sc]
            for r, c in main:
                nr = 2 * r0 - 1 - r - gap if sr < r0 else (
                    2 * r1 + 1 - r + gap if sr > r1 else r)
                nc = 2 * c0 - 1 - c - gap if sc < c0 else (
                    2 * c1 + 1 - c + gap if sc > c1 else c)
                yield gi, (sr, sc), color, (nr, nc)


def input_problems(grid):
    """Require the canonical structure and safe, order-independent paints at ALL gaps.

    A seed's own same-colored paint over its cue (normal at gap=0) is harmless.
    Every other input overlap and every distinct-writer target overlap rejects.
    """
    try:
        grid = normalize_grid(grid)
    except (TypeError, ValueError) as exc:
        return [f"malformed input: {exc}"]
    generator = selected_generator()[0]
    problems = list(generator.self_check(grid))
    if problems:
        return [f"canonical input: {item}" for item in problems]
    h, w = len(grid), len(grid[0])
    for gap in ALLOWED_GAPS:
        writers = {}
        for group, cue, color, cell in _paints(grid, gap):
            r, c = cell
            if not (0 <= r < h and 0 <= c < w):
                problems.append(f"gap={gap}: group {group} copy clips at {cell}")
                continue
            if grid[r][c] and not (cell == cue and grid[r][c] == color):
                problems.append(f"gap={gap}: group {group} paint hits input at {cell}")
            owner = (group, cue)
            if cell in writers and writers[cell] != owner:
                problems.append(f"gap={gap}: distinct seed/group targets overlap at {cell}")
            writers[cell] = owner
    return sorted(set(problems))


def python_mirror(grid, gap=DEFAULT_GAP):
    """Audit-only mirror, never the source of materialized labels.

    Like the canonical rule this raw diagnostic clips outside the grid. The
    sampler checks input_problems first, so emitted prototype pairs never clip.
    """
    _gap(gap)
    grid = normalize_grid(grid)
    result = deepcopy(grid)
    for _, _, color, (r, c) in _paints(grid, gap):
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            result[r][c] = color
    return result


class RuleExecutor:
    """One actual Racket process holding all three materialized native lambdas."""

    def __init__(self):
        self.programs = {gap: program_for_gap(gap) for gap in ALLOWED_GAPS}
        self.definitions = {gap: bridge_definition_for_gap(gap) for gap in ALLOWED_GAPS}
        self.bridge = RacketBridge(timeout=10.0)
        self.calls = 0
        try:
            for definition in self.definitions.values():
                # These exact sources are self-contained native Racket lambdas:
                # no free h/w, shorthand bindings, dict literals or comments.
                # Use the shared wrapper parser without the unrelated legacy
                # scripts.comment_solutions import in wrap_rule's normalizer.
                self.bridge.eval_text(definition)
        except BaseException:
            self.bridge.close()
            raise

    def apply(self, grid, gap=DEFAULT_GAP):
        _gap(gap)
        grid = normalize_grid(grid)
        self.bridge.define_grid("__gap_input", grid)
        output = normalize_grid(self.bridge.eval_text(f"(__gap_{gap} __gap_input)"))
        self.calls += 1
        if (len(output), len(output[0])) != (len(grid), len(grid[0])):
            raise ValueError("Racket changed grid dimensions")
        return output

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.close()


class SamplingError(RuntimeError):
    def __init__(self, details):
        self.details = details
        super().__init__(f"incomplete prototype sample: accepted {details['accepted']}/"
                         f"{details['requested']} after {details['attempts']} attempts")


def sample_pool(seed, *, start_index=0, difficulty="medium", n_pairs=4,
                max_attempts=256, executor=None):
    """Draw unchanged canonical inputs and label each accepted input at every gap."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(start_index, "start_index", 0, 2**31 - 1)
    _integer(n_pairs, "n_pairs", 1, 30)
    _integer(max_attempts, "max_attempts", 1, 4096)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium or hard")
    if executor is None:
        with RuleExecutor() as live:
            return sample_pool(seed, start_index=start_index, difficulty=difficulty,
                               n_pairs=n_pairs, max_attempts=max_attempts, executor=live)
    generator, _, generator_sha = selected_generator()
    pairs, rejected, seen = [], [], set()
    for offset in range(max_attempts):
        index = start_index + offset
        try:
            grid = generator.generate(seed, index, difficulty=difficulty)
        except ValueError as exc:
            rejected.append({"sample_index": index, "reasons": [f"canonical draw: {exc}"]})
            continue
        input_sha = json_sha256(grid)
        problems = input_problems(grid)
        if input_sha in seen:
            problems.append("duplicate input within episode")
        if problems:
            rejected.append({"sample_index": index, "input_sha256": input_sha,
                             "reasons": problems})
            continue
        outputs = {str(gap): executor.apply(grid, gap) for gap in ALLOWED_GAPS}
        for gap in ALLOWED_GAPS:
            if outputs[str(gap)] != python_mirror(grid, gap):
                raise RuntimeError(f"Python/Racket disagreement at index={index}, gap={gap}")
            if any(outputs[str(gap)][r][c] != value for r, row in enumerate(grid)
                   for c, value in enumerate(row) if value):
                raise RuntimeError(f"input cue or main cell changed at index={index}, gap={gap}")
        output_hashes = {gap: json_sha256(output) for gap, output in outputs.items()}
        if len(set(output_hashes.values())) != len(ALLOWED_GAPS):
            rejected.append({"sample_index": index, "input_sha256": input_sha,
                             "reasons": ["settings do not have pairwise distinct Racket labels"]})
            continue
        pairs.append({"sample_index": index, "input": grid, "input_sha256": input_sha,
                      "outputs": outputs, "output_sha256": output_hashes})
        seen.add(input_sha)
        if len(pairs) == n_pairs:
            return {"seed": seed, "difficulty": difficulty, "start_index": start_index,
                    "attempts": offset + 1, "next_index": index + 1,
                    "max_attempts": max_attempts, "pairs": pairs, "rejections": rejected,
                    "generator_sha256": generator_sha, "label_backend": "RacketBridge"}
    raise SamplingError({"seed": seed, "difficulty": difficulty, "start_index": start_index,
                         "attempts": max_attempts, "accepted": len(pairs),
                         "requested": n_pairs, "rejections": rejected,
                         "generator_sha256": generator_sha,
                         "accepted_indices": [p["sample_index"] for p in pairs]})


def episode_from_pool(pool, *, gap=DEFAULT_GAP, n_train=3, n_test=1, episode_index=0):
    """Choose gap once, then demand demonstration elimination of both rivals."""
    _integer(n_train, "n_train", 3, 20)
    _integer(n_test, "n_test", 1, 10)
    _integer(episode_index, "episode_index", 0, 2**31 - 1)
    selection = "explicit"
    if gap is None:
        gap = gap_from_seed(pool["seed"], episode_index=episode_index)
        selection = "seed_sha256_once_per_episode"
    _gap(gap)
    if len(pool["pairs"]) != n_train + n_test:
        raise ValueError("incomplete episode pool: exact requested train/test count required")
    rivals = []
    for rival in ALLOWED_GAPS:
        if rival == gap:
            continue
        mismatches = [i for i, pair in enumerate(pool["pairs"])
                      if pair["outputs"][str(rival)] != pair["outputs"][str(gap)]]
        train_mismatches = [i for i in mismatches if i < n_train]
        if not train_mismatches:
            raise ValueError(f"episode is not identifiable: gap={rival} fits every demonstration")
        rivals.append({"gap": rival, "status": "eliminated_by_demonstrations",
                       "backend": "RacketBridge",
                       **_program_hashes(rival),
                       "demonstration_mismatch_indices": train_mismatches,
                       "query_mismatch_indices": [i - n_train for i in mismatches if i >= n_train],
                       "prediction_sha256": [json_sha256(p["outputs"][str(rival)])
                                             for p in pool["pairs"]]})
    holdouts = {"status": "not_evaluated_multiple_queries", "all_identifiable": None,
                "extra_racket_calls": 0, "rotations": []}
    if n_test == 1:
        rotations = []
        for query_index in range(len(pool["pairs"])):
            demonstrations = [i for i in range(len(pool["pairs"])) if i != query_index]
            checks = []
            for rival in ALLOWED_GAPS:
                if rival == gap:
                    continue
                different = [i for i, pair in enumerate(pool["pairs"])
                             if pair["outputs"][str(rival)] != pair["outputs"][str(gap)]]
                demo_differences = [i for i in demonstrations if i in different]
                status = "eliminated_by_demonstrations" if demo_differences else (
                    "ambiguous_query" if query_index in different else "survived_all")
                checks.append({"gap": rival, "status": status,
                               "demonstration_mismatch_pair_indices": demo_differences,
                               "query_differs": query_index in different,
                               "query_prediction_sha256": json_sha256(
                                   pool["pairs"][query_index]["outputs"][str(rival)]),
                               "callable_sha256": text_sha256(callable_for_gap(rival))})
            rotations.append({"query_pair_index": query_index,
                              "demonstration_pair_indices": demonstrations,
                              "rival_checks": checks})
        all_identifiable = all(check["status"] == "eliminated_by_demonstrations"
                               for rotation in rotations for check in rotation["rival_checks"])
        if not all_identifiable:
            raise ValueError("episode is not identifiable under every single-query holdout")
        holdouts = {"status": "no_parameter_ambiguity_found", "all_identifiable": True,
                    "extra_racket_calls": 0, "rotations": rotations}
    labeled = []
    for pair in pool["pairs"]:
        data = {"input": deepcopy(pair["input"]), "output": deepcopy(pair["outputs"][str(gap)])}
        labeled.append({**data, "sample_index": pair["sample_index"],
                        "input_sha256": json_sha256(data["input"]),
                        "output_sha256": json_sha256(data["output"]),
                        "pair_sha256": json_sha256(data)})
    private = {"task_id": TASK_ID, "status": "prototype", "parameters": {"gap": gap},
               "parameter_selection": selection, "episode_index": episode_index,
               "seed": pool["seed"], "difficulty": pool["difficulty"],
               **_program_hashes(gap), "query_holdouts": holdouts,
               "label_backend": "RacketBridge", "rival_checks": rivals,
               "train": labeled[:n_train], "test": labeled[n_train:]}
    public = {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                        for p in labeled[:n_train]],
              "test": [{"input": deepcopy(p["input"])} for p in labeled[n_train:]]}
    private["public_sha256"] = json_sha256(public)
    return {"public": public, "private": private}


def _canonical_check(executor):
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    if not pairs:
        raise ValueError("no canonical pairs: cannot establish original-setting parity")
    rows = []
    for pair in pairs:
        actual = executor.apply(pair["input"], 0)
        if actual != pair["output"]:
            raise RuntimeError(f"gap=0 canonical mismatch: {pair['variant']}/{pair['split']}/"
                               f"{pair['pair_index']}")
        rows.append({"variant": pair["variant"], "split": pair["split"],
                     "pair_index": pair["pair_index"], "input_sha256": json_sha256(pair["input"]),
                     "output_sha256": json_sha256(actual), "status": "equal"})
    return {"pairs_checked": len(rows), "all_match": True, "pairs": rows,
            "canonical_pairs_sha256": json_sha256(pairs),
            "canonical_program_sha256": text_sha256(canonical_program()),
            "executed_callable_sha256": text_sha256(callable_for_gap(0)),
            "bridge_definition_sha256": text_sha256(bridge_definition_for_gap(0))}


def _source_hashes():
    generator, source, loaded_sha = selected_generator()
    del generator
    if hashlib.sha256(source.read_bytes()).hexdigest() != loaded_sha:
        raise RuntimeError("selected generator changed during the probe; rerun with stable source")
    paths = [Path(__file__).resolve(), Path(__file__).resolve().with_name("README.md"), source,
             ROOT / "generators" / TASK_ID / "tests/test_parametric_dc2c4869445c.py"]
    # Hash the modules actually imported, including flattened staged runtimes;
    # do not assume their library storage paths are their execution paths.
    paths.extend(Path(sys.modules[symbol.__module__].__file__).resolve()
                 for symbol in (canonical_path, strip_rule_wrapper, RacketBridge))
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(out, *, seed=1729, gap="all", start_index=0, difficulty="medium",
                   n_train=3, n_test=1, max_attempts=256, episode_index=0):
    """Write a complete, self-checking authoring bundle or retain an explicit failure."""
    if gap not in ("all", "seed", "0", "1", "2"):
        raise ValueError("gap mode must be all, seed, 0, 1 or 2")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    source_hashes = None
    programs = {}
    request = {"seed": seed, "gap": gap, "start_index": start_index, "difficulty": difficulty,
               "n_train": n_train, "n_test": n_test, "max_attempts": max_attempts,
               "episode_index": episode_index}
    try:
        source_hashes = _source_hashes()
        (out / "programs").mkdir()
        for value in ALLOWED_GAPS:
            code = program_for_gap(value)
            path = out / "programs" / f"gap-{value}.rkt"
            path.write_text(code, encoding="utf-8")
            callable_path = out / "programs" / f"gap-{value}.callable.rkt"
            callable_path.write_text(callable_for_gap(value), encoding="utf-8")
            definition_path = out / "programs" / f"gap-{value}.definition.rkt"
            definition_path.write_text(bridge_definition_for_gap(value), encoding="utf-8")
            programs[str(value)] = {"path": str(path.relative_to(out)),
                                    "sha256": text_sha256(code),
                                    "callable_path": str(callable_path.relative_to(out)),
                                    "callable_sha256": text_sha256(callable_for_gap(value)),
                                    "bridge_definition_path": str(definition_path.relative_to(out)),
                                    "bridge_definition_sha256": text_sha256(bridge_definition_for_gap(value)),
                                    "normalized_rule_hash": text_sha256(" ".join(code.split()))[:12]}
        with RuleExecutor() as live:
            canonical = _canonical_check(live)
            pool = sample_pool(seed, start_index=start_index, difficulty=difficulty,
                               n_pairs=n_train + n_test, max_attempts=max_attempts, executor=live)
            values = list(ALLOWED_GAPS) if gap == "all" else [None if gap == "seed" else int(gap)]
            episodes = [episode_from_pool(pool, gap=value, n_train=n_train, n_test=n_test,
                                          episode_index=episode_index) for value in values]
            runtime_identity = live.bridge.runtime_identity
            rule_calls = live.calls
        if _source_hashes() != source_hashes:
            raise RuntimeError("prototype or dependency source changed during the probe; rerun")
        (out / "public").mkdir()
        (out / "private").mkdir()
        episode_rows = []
        for index, episode in enumerate(episodes):
            name = f"episode-{index:03d}.json"
            public_name = public_filename(episode["public"])
            _write_json(out / "public" / public_name, episode["public"])
            _write_json(out / "private" / name, episode["private"])
            episode_rows.append({"gap": episode["private"]["parameters"]["gap"],
                                 "public": f"public/{public_name}", "private": f"private/{name}",
                                 "public_sha256": json_sha256(episode["public"]),
                                 "private_sha256": json_sha256(episode["private"]),
                                 "rivals_eliminated": len(episode["private"]["rival_checks"]),
                                 "single_query_holdouts": len(episode["private"]["query_holdouts"]["rotations"]),
                                 "holdouts_identifiable": episode["private"]["query_holdouts"]["all_identifiable"]})
        witness = deepcopy(pool["pairs"][0])
        witness["explanation"] = "Same lawful input; all three actual Racket outputs differ."
        _write_json(out / "cross-setting-witness.json", witness)
        _write_json(out / "sampling.json", {key: value for key, value in pool.items() if key != "pairs"} | {
            "accepted_pairs": [{"sample_index": pair["sample_index"],
                                "input_sha256": pair["input_sha256"],
                                "output_sha256": pair["output_sha256"],
                                "split": "train" if i < n_train else "test",
                                "pair_index": i if i < n_train else i - n_train}
                               for i, pair in enumerate(pool["pairs"])]})
        _write_json(out / "canonical-parity.json", canonical)
        report = {"schema": "dc2c4869445c-gap-prototype-v1", "status": "complete_prototype",
                  "task_id": TASK_ID, "parent_family": "training:b775ac94",
                  "prototype_version": PROTOTYPE_VERSION,
                  "parameter": {"name": "gap", "allowed_values": list(ALLOWED_GAPS), "default": 0},
                  "seed": seed, "start_index": start_index, "episode_index": episode_index,
                  "difficulty": difficulty, "n_train": n_train, "n_test": n_test,
                  "max_attempts": max_attempts, "actual_attempts": pool["attempts"],
                  "accepted_indices": [p["sample_index"] for p in pool["pairs"]],
                  "rejections": len(pool["rejections"]), "episodes": episode_rows,
                  "programs": programs, "source_sha256": source_hashes,
                  "request": request,
                  "canonical_pairs_checked": canonical["pairs_checked"],
                  "actual_racket_rule_calls": rule_calls, "runtime_identity": runtime_identity,
                  "actual_payload_argv": [sys.executable, *sys.argv],
                  "limits": ["Prototype only; no production API or approval/training status change.",
                             "Finite selected seed/index evidence against exactly the other two gap settings.",
                             "Inputs are rejected unless every allowed gap preserves cues without clipping or overlaps.",
                             "All-setting episodes deliberately share accepted inputs for controlled comparison.",
                             "No claim about every seed, all semantic rivals, or production distribution coverage."]}
        report["artifacts"] = {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sorted(out.rglob("*")) if path.is_file()}
        _write_json(out / "report.json", report)
        return report
    except BaseException as exc:
        _write_json(out / "failure.json", {"status": "failed_incomplete_prototype",
                                           "error_type": type(exc).__name__, "error": str(exc),
                                           "details": getattr(exc, "details", None),
                                           "request": request, "source_sha256": source_hashes,
                                           "programs": programs,
                                           "actual_payload_argv": [sys.executable, *sys.argv]})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new evidence directory; never overwritten")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--gap", choices=("0", "1", "2", "seed", "all"), default="0")
    parser.add_argument("--episode-index", type=int, default=0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--train", dest="n_train", type=int, default=3)
    parser.add_argument("--test", dest="n_test", type=int, default=1)
    parser.add_argument("--max-attempts", type=int, default=256)
    args = parser.parse_args(argv)
    try:
        report = write_evidence(**vars(args))
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "settings": [row["gap"] for row in report["episodes"]],
                      "accepted_indices": report["accepted_indices"],
                      "actual_attempts": report["actual_attempts"],
                      "canonical_pairs_checked": report["canonical_pairs_checked"],
                      "actual_racket_rule_calls": report["actual_racket_rule_calls"],
                      "report": str(args.out / "report.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

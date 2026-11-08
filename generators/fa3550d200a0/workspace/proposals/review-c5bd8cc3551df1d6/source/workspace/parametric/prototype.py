"""Proposed task-local quarter-turn episodes; not a production rule API."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import gen_ctx
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "fa3550d200a0"
PARENT_TASK_ID = "414297c0"
VERSION = "quarter-turn-prototype-1"
PARAMETER_VALUES = (0, 1, 2, 3)
DEFAULT_PARAMETER = 0


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_parameter(value):
    if type(value) is not int or value not in PARAMETER_VALUES:
        raise ValueError("quarter_turns must be an integer in {0,1,2,3}")
    return value


def choose_parameter(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    context = gen_ctx(seed=seed, sample_index=0, task_id=TASK_ID, version=VERSION)
    return context.draw_choice("quarter_turns", PARAMETER_VALUES)


def read_canonical_program(root):
    with canonical_path(root).open(encoding="utf-8") as stream:
        programs = {
            row["program_solution"] for row in map(json.loads, stream)
            if row.get("task_id") == TASK_ID
        }
    if len(programs) != 1:
        raise ValueError(f"expected one unambiguous canonical program, found {len(programs)}")
    program = programs.pop()
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("unsupported canonical rule wrapper")
    return program


def instantiate_program(canonical_program, quarter_turns):
    """Return exact canonical bytes at zero; alter only stamp offsets otherwise."""
    validate_parameter(quarter_turns)
    if quarter_turns == 0:
        return canonical_program
    old_row = "(nr (+ mr (- (fst cell) sr)))"
    old_col = "(nc (+ mc (- (snd cell) scc2)))"
    if canonical_program.count(old_row) != 1 or canonical_program.count(old_col) != 1:
        raise ValueError("canonical coordinate sites changed; refusing an unreviewed rewrite")
    row_offset, col_offset = {
        1: ("(- (snd cell) scc2)", "(- (- (fst cell) sr))"),
        2: ("(- (- (fst cell) sr))", "(- (- (snd cell) scc2))"),
        3: ("(- (- (snd cell) scc2))", "(- (fst cell) sr)"),
    }[quarter_turns]
    return canonical_program.replace(old_row, f"(nr (+ mr {row_offset}))").replace(
        old_col, f"(nc (+ mc {col_offset}))"
    )


def rotation_domain_errors(grid, generator):
    """Require unclipped, disjoint target footprints at every declared setting.

    This is an input-domain test, not a label implementation. Actual labels and
    all demonstration rival predictions come from the exact Racket programs.
    """
    features, errors = generator._analyze(grid)
    if errors:
        return ["canonical domain: " + error for error in errors]
    top, left, bottom, right = features["canvas_bbox"]
    result = []
    for turns in PARAMETER_VALUES:
        owners = {}
        for piece_index, (role, marker, cells, _targets) in enumerate(features["piece_records"]):
            if role != "matched":
                continue
            sr, sc, _value = next(cell for cell in cells if cell[2] == marker)
            ar, ac = features["marker_positions"][marker][0]
            for row, col, _value in cells:
                dr, dc = row - sr, col - sc
                for _ in range(turns):
                    dr, dc = dc, -dr
                target = ar + dr, ac + dc
                if not (top <= target[0] <= bottom and left <= target[1] <= right):
                    result.append(f"turn {turns}: piece {piece_index} outside canvas at {target}")
                if target in owners and owners[target] != piece_index:
                    result.append(f"turn {turns}: overlapping piece footprints at {target}")
                owners[target] = piece_index
    return sorted(set(result))


def public_challenge(episode):
    """Strict allowlist, including fresh nested grids, for a solver-visible file."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


class SamplingExhausted(RuntimeError):
    def __init__(self, record):
        self.record = copy.deepcopy(record)
        super().__init__(
            f"sampling exhausted {record['max_attempts']} input attempts in {record['phase']} phase: "
            f"accepted {record['accepted_demos']}/{record['requested_demos']} demonstrations and "
            f"{record['accepted_queries']}/{record['requested_queries']} queries; "
            f"unresolved rivals {record['remaining_rivals']}"
        )


class EpisodeBuilder:
    """A single explicit source tree and one live public Racket bridge."""

    def __init__(self, *, root=None):
        self.root = Path(root).resolve() if root is not None else find_root(__file__)
        self.generator, self.generator_path, generator_sha = load_selected_generator(TASK_ID, root=self.root)
        canonical = read_canonical_program(self.root)
        self.programs = {turns: instantiate_program(canonical, turns) for turns in PARAMETER_VALUES}
        self.program_hashes = {
            turns: hashlib.sha256(program.encode()).hexdigest()
            for turns, program in self.programs.items()
        }
        self.source_paths = {
            "generator": self.generator_path,
            "prototype": Path(__file__).resolve(),
            "canonical_ledger": canonical_path(self.root),
        }
        self.source_binding = {
            name: {"path": str(path.relative_to(self.root)), "sha256": file_digest(path)}
            for name, path in self.source_paths.items()
        }
        if self.source_binding["generator"]["sha256"] != generator_sha:
            raise RuntimeError("generator changed while being loaded")
        self.bridge = RacketBridge(timeout=10.0)
        self.execution_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.bridge.close()
        return False

    def ensure_sources_unchanged(self):
        for name, path in self.source_paths.items():
            if file_digest(path) != self.source_binding[name]["sha256"]:
                raise RuntimeError(f"source changed during evidence collection: {name}")

    def execute(self, quarter_turns, grid):
        validate_parameter(quarter_turns)
        normalized = normalize_grid(grid)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"
        # A lexical rule! identity exposes the exact materialized rule's
        # function. No private verifier/runtime controller is imported.
        expression = f"(let ((rule! (lambda (proc) proc))) ({self.programs[quarter_turns]} {literal}))"
        output = normalize_grid(self.bridge.eval_text(expression))
        self.execution_count += 1
        return output

    def generate(self, seed, *, quarter_turns=None, demos=3, queries=4,
                 max_attempts=500, difficulty=None, input_overrides=None):
        if type(seed) is not int:
            raise ValueError("seed must be an integer")
        chosen = choose_parameter(seed) if quarter_turns is None else validate_parameter(quarter_turns)
        for name, value, maximum in (("demos", demos, 64), ("queries", queries, 64),
                                     ("max_attempts", max_attempts, 10000)):
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"{name} must be an integer in [1,{maximum}]")
        overrides = dict(input_overrides or {})
        train, test, attempts, accepted = [], [], [], set()
        remaining = set(PARAMETER_VALUES) - {chosen}
        demo_outputs, accepted_indices = [], {"train": [], "test": []}
        executions_before = self.execution_count

        def exhaustion(phase):
            return SamplingExhausted({
                "phase": phase, "seed": seed, "quarter_turns": chosen,
                "requested_demos": demos, "requested_queries": queries,
                "accepted_demos": len(train), "accepted_queries": len(test),
                "max_attempts": max_attempts, "remaining_rivals": sorted(remaining),
                "attempts": attempts, "source_binding": self.source_binding,
                "input_overrides": overrides, "difficulty": difficulty,
            })

        def draw(phase):
            if len(attempts) >= max_attempts:
                raise exhaustion(phase)
            index = len(attempts)
            attempt = {"sample_index": index, "phase": phase, "status": "pending"}
            attempts.append(attempt)
            try:
                grid = self.generator.generate(seed, index, difficulty=difficulty, **overrides)
            except RuntimeError as error:
                attempt.update(status="rejected", reason="canonical_sampler_exhausted", detail=str(error))
                return None, attempt
            input_hash = digest(grid)
            attempt["input_sha256"] = input_hash
            domain_errors = rotation_domain_errors(grid, self.generator)
            if domain_errors:
                attempt.update(status="rejected", reason="rotation_domain", errors=domain_errors)
                return None, attempt
            if input_hash in accepted:
                attempt.update(status="rejected", reason="duplicate_input")
                return None, attempt
            return grid, attempt

        # This entire loop finishes, and the rival set is checked, before any
        # query input is drawn or query label is executed.
        while len(train) < demos:
            grid, attempt = draw("demo")
            if grid is None:
                continue
            predictions = {turns: self.execute(turns, grid) for turns in PARAMETER_VALUES}
            eliminated = {turns for turns in remaining if predictions[turns] != predictions[chosen]}
            survivors = remaining - eliminated
            attempt["prediction_sha256"] = {str(turns): digest(output) for turns, output in predictions.items()}
            if remaining and not eliminated:
                attempt.update(status="rejected", reason="no_demo_identification_progress")
                continue
            if len(train) == demos - 1 and survivors:
                attempt.update(status="rejected", reason="last_demo_still_ambiguous",
                               remaining_rivals=sorted(survivors))
                continue
            attempt.update(status="accepted", eliminated_rivals=sorted(eliminated))
            remaining = survivors
            accepted.add(attempt["input_sha256"])
            accepted_indices["train"].append(attempt["sample_index"])
            train.append({"input": grid, "output": predictions[chosen]})
            demo_outputs.append(predictions)

        if remaining:
            raise exhaustion("demo")
        demo_survivors = [
            turns for turns in PARAMETER_VALUES
            if all(predictions[turns] == pair["output"]
                   for predictions, pair in zip(demo_outputs, train))
        ]
        if demo_survivors != [chosen]:
            raise AssertionError("demonstration gate did not identify exactly the chosen setting")

        while len(test) < queries:
            grid, attempt = draw("query")
            if grid is None:
                continue
            # Query outputs never affect acceptance: only input-domain and
            # uniqueness checks above can reject a query candidate.
            output = self.execute(chosen, grid)
            attempt.update(status="accepted")
            accepted.add(attempt["input_sha256"])
            accepted_indices["test"].append(attempt["sample_index"])
            test.append({"input": grid, "output": output})

        self.ensure_sources_unchanged()
        rival_witnesses = {
            str(turns): [index for index, (predictions, pair) in enumerate(zip(demo_outputs, train))
                         if predictions[turns] != pair["output"]]
            for turns in PARAMETER_VALUES if turns != chosen
        }
        return {
            "schema": "fa3550d200a0-quarter-turn-prototype-episode-v1",
            "train": train, "test": test, "program": self.programs[chosen],
            "meta": {
                "status": "proposed_prototype", "task_id": TASK_ID, "parent_task_id": PARENT_TASK_ID,
                "seed": seed, "quarter_turns": chosen, "canonical_default": chosen == 0,
                "program_sha256": self.program_hashes[chosen],
                "source_binding": copy.deepcopy(self.source_binding),
                "demo_survivors": demo_survivors, "demo_rival_witnesses": rival_witnesses,
                "demo_prediction_sha256": [
                    {str(turns): digest(output) for turns, output in predictions.items()}
                    for predictions in demo_outputs
                ],
                "query_lesson_checks": [
                    {"query_index": index, "input_sha256": digest(pair["input"]),
                     "output_sha256": digest(pair["output"]),
                     "demo_consistent_settings": demo_survivors,
                     "demo_witnesses": rival_witnesses,
                     "gate_completed_before_query_draw": True}
                    for index, pair in enumerate(test)
                ],
                "sampling": {"max_attempts": max_attempts, "attempts": attempts,
                             "accepted_indices": accepted_indices,
                             "difficulty": difficulty, "input_overrides": overrides},
                "racket_executions": self.execution_count - executions_before,
                "input_constraints": "canonical valid; every declared rotation fits; target footprints disjoint",
                "rival_scope": "the four declared quarter_turns settings only",
            },
        }

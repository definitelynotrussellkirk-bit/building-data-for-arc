#!/usr/bin/env python3
"""Proposed isolated frequency-extreme rule variant; never production approval.

All labels are executed by the bundled Racket bridge. The small constructor is
independent of the selected generator and deliberately supports both settings.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge

TASK_ID = "7944933e200f"
VERSION = "frequency-extreme-prototype-v1"
PARAMETER = "frequency_extreme"
SETTINGS = ("minimum", "maximum")
DEFAULT = "minimum"
CANONICAL_RULE = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let* ((objs (objects g 0))\n                  (all-vals (flatmap (lambda (r)\n                                       (map (lambda (c) (at g r c)) (range 0 (cols g))))\n                                     (range 0 (rows g))))\n                  (rarest (first (sort-by objs\n                                          (lambda (o)\n                                            (count-if (lambda (v) (= v (obj-color o)))\n                                                      all-vals))))))\n             (crop-object g rarest)))))'
COUNT_EXPRESSION = '(count-if (lambda (v) (= v (obj-color o)))\n                                                      all-vals)'
PARAMETER_SPEC = {
    PARAMETER: {
        "allowed": list(SETTINGS), "canonical_default": DEFAULT,
        "scope": "chosen once per complete episode; inferred from demonstrations",
        "semantics": "minimum or maximum whole-grid frequency of an object's nonzero color",
        "invariants": ["monochromatic four-connected nonzero objects", "global color counts", "stable first row-major tie", "original unmasked component bbox crop"],
        "input_constraints": "rectangular 5..30 integer-color grid with at least two nonzero colors; each setting requires its own selected bbox smaller than full input, so arbitrary-grid domains can differ; constructed episodes check both domains, have unequal global extremes, and demonstrations reject the other setting",
    }
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_hash(grid):
    return sha256(canonical_json(grid).encode())


def _setting(value):
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}: {value!r}")
    return value


def _integer(value, name):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not bool")
    return value


def _rng(seed, label):
    _integer(seed, "seed")
    return random.Random(int(sha256(f"{TASK_ID}|{VERSION}|{seed}|{label}".encode()), 16))


def choose_setting(seed):
    """Choose exactly once from the episode seed, before any pair construction."""
    return _rng(seed, "parameter").choice(SETTINGS)


def emit_rule(frequency_extreme=DEFAULT):
    """Exact canonical bytes for minimum; negate only the stable sort key for maximum."""
    setting = _setting(frequency_extreme)
    if setting == DEFAULT:
        return CANONICAL_RULE
    assert CANONICAL_RULE.count(COUNT_EXPRESSION) == 1
    return CANONICAL_RULE.replace(COUNT_EXPRESSION, f"(- {COUNT_EXPRESSION})")


def _grid_errors(grid):
    if not isinstance(grid, list) or not 5 <= len(grid) <= 30:
        return ["input must have 5..30 rows"]
    if any(not isinstance(row, list) for row in grid) or not 5 <= len(grid[0]) <= 30:
        return ["input must have 5..30 columns"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["input must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integers 0..9"]
    if len({value for row in grid for value in row if value}) < 2:
        return ["input must contain at least two nonzero colors"]
    return []


def _components(grid):
    seen, result = set(), []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            color = grid[row][col]
            if not color or (row, col) in seen:
                continue
            seen.add((row, col))
            stack, cells = [(row, col)], []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def python_reference(grid, frequency_extreme=DEFAULT):
    """Debug oracle only: episode labels are never taken from this mirror."""
    setting = _setting(frequency_extreme)
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = Counter(value for row in grid for value in row if value)
    components = _components(grid)
    direction = 1 if setting == "minimum" else -1
    _, cells = min(components, key=lambda item: direction * counts[item[0]])
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def domain_errors(grid, frequency_extreme=DEFAULT):
    _setting(frequency_extreme)
    errors = _grid_errors(grid)
    if errors:
        return errors
    output = python_reference(grid, frequency_extreme)
    if len(output) == len(grid) and len(output[0]) == len(grid[0]):
        return ["selected component bbox must be smaller than input"]
    return []


def _paint(grid, top, left, cells, color):
    for row, col in cells:
        grid[top + row][left + col] = color


def make_input(seed, pair_index):
    """Construct distinct global extremes, fragmentation and unmasked crop holes.

    Counts are 9, 13, and 18. Objects are distinct even when a color recurs.
    Position, color names and orientation are nuisances; the rule is fixed.
    """
    _integer(pair_index, "pair_index")
    if pair_index < 0:
        raise ValueError("pair_index must be nonnegative")
    rng = _rng(seed, f"pair:{pair_index}")
    rare, middle, common = rng.sample(range(1, 10), 3)
    grid = [[0] * 17 for _ in range(13)]
    open_ring = [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)]
    ring = [(r, c) for r in range(3) for c in range(3) if r in (0, 2) or c in (0, 2)]
    rectangle_ring = [(r, c) for r in range(3) for c in range(4) if r in (0, 2) or c in (0, 3)]
    _paint(grid, 1, 1, open_ring, rare)
    grid[2][2] = middle
    _paint(grid, 10, 14, [(0, 0), (1, 0)], rare)
    _paint(grid, 1, 8, ring, middle)
    _paint(grid, 5, 8, [(0, c) for c in range(4)], middle)
    _paint(grid, 7, 1, rectangle_ring, common)
    _paint(grid, 10, 5, [(0, c) for c in range(8)], common)
    # Keep the first demonstration rich, then vary which same-color component
    # is first. Exact input construction is independent of the hidden setting.
    turns = 0 if pair_index == 0 else rng.randrange(4)
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    if pair_index and rng.choice((False, True)):
        grid = [row[::-1] for row in grid]
    for setting in SETTINGS:
        if domain_errors(grid, setting):
            raise AssertionError(domain_errors(grid, setting))
    return grid


class RacketRunner:
    """Execute the emitted legacy callable with the real bundled Racket bridge.

    `rule!` is a controller registration form, not a prelude primitive. As the
    repository controller does, strip only that outer registration wrapper and
    apply the unchanged enclosed lambda. Both exact strings/hashes are retained.
    """
    def __init__(self):
        self.bridge = RacketBridge(timeout=15.0)
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.bridge.shutdown()

    def execute(self, grid, frequency_extreme=DEFAULT, *, label="probe"):
        setting = _setting(frequency_extreme)
        errors = domain_errors(grid, setting)
        if errors:
            raise ValueError("; ".join(errors))
        program = emit_rule(setting)
        callable_source = program[len("(rule! "):-1]
        self.bridge.define_grid("prototype_input", grid)
        expression = f"({callable_source} prototype_input)"
        output = self.bridge.eval_text(expression)
        expected = python_reference(grid, setting)
        if output != expected:
            raise AssertionError(f"Racket/Python mismatch for {setting}: {output!r} != {expected!r}")
        self.executions.append({"backend": "RacketBridge", "label": label, "parameters": {PARAMETER: setting}, "program_sha256": sha256(program.encode()), "callable_sha256": sha256(callable_source.encode()), "input_sha256": grid_hash(grid), "output_sha256": grid_hash(output), "output": output})
        return output


def generate_episode(seed, frequency_extreme=None, *, n_train=3, n_test=1, runner=None):
    """Return a visible-only challenge and private, Racket-derived evidence.

    A missing setting selects once from the seed. An explicit setting fixes the
    same parameter for every pair. Rivals see demos and no query labels.
    """
    _integer(seed, "seed")
    if type(n_train) is not int or not 1 <= n_train <= 8:
        raise ValueError("n_train must be an integer 1..8")
    if type(n_test) is not int or not 1 <= n_test <= 4:
        raise ValueError("n_test must be an integer 1..4")
    setting = choose_setting(seed) if frequency_extreme is None else _setting(frequency_extreme)
    if runner is None:
        with RacketRunner() as owned_runner:
            return generate_episode(seed, setting, n_train=n_train, n_test=n_test, runner=owned_runner)
    start = len(runner.executions)
    demos = []
    for index in range(n_train):
        grid = make_input(seed, index)
        demos.append({"input": grid, "output": runner.execute(grid, setting, label=f"demo:{index}")})
    rival_checks, consistent = {}, []
    # This entire check happens before the query is constructed or executed.
    for rival in SETTINGS:
        rejected = []
        for index, pair in enumerate(demos):
            rival_output = runner.execute(pair["input"], rival, label=f"rival:{rival}:demo:{index}")
            if rival_output != pair["output"]:
                rejected.append(index)
        rival_checks[rival] = {"fits_all_demos": not rejected, "rejected_on_demo_indices": rejected}
        if not rejected:
            consistent.append(rival)
    if consistent != [setting]:
        raise ValueError(f"unidentifiable episode: demonstration-consistent settings {consistent!r}")
    queries, labels = [], []
    for index in range(n_test):
        grid = make_input(seed, n_train + index)
        queries.append({"input": grid})
        labels.append(runner.execute(grid, setting, label=f"query:{index}"))
    return {
        "public": {"train": deepcopy(demos), "test": deepcopy(queries)},
        "private": {"schema": "arc-frequency-extreme-prototype-v1", "status": "proposed_unapproved_prototype", "task_id": TASK_ID, "prototype_version": VERSION, "seed": seed, "parameters": {PARAMETER: setting}, "parameter_spec": PARAMETER_SPEC, "program": emit_rule(setting), "program_sha256": sha256(emit_rule(setting).encode()), "demo_consistent_settings": consistent, "rival_demo_checks": rival_checks, "phase_order": ["execute_demonstrations", "check_parameter_rivals", "execute_query"], "query_outputs": labels, "pair_input_sha256": [grid_hash(pair["input"]) for pair in demos + queries], "executions": deepcopy(runner.executions[start:])},
    }


def semantic_witnesses():
    """Literal expected labels for preserved semantics, including stable max ties."""
    fragmented = [[0] * 7 for _ in range(5)]
    fragmented[0][:2] = [2, 2]
    fragmented[2][0] = fragmented[2][2] = fragmented[2][4] = 3
    tie = [[0] * 5 for _ in range(5)]
    tie[0][3] = tie[0][4] = 8
    tie[3][0] = tie[4][0] = 2
    diagonal = [[0] * 5 for _ in range(5)]
    diagonal[0][0] = diagonal[1][1] = 8
    diagonal[3][:3] = [2, 2, 2]
    intruder = [[0] * 8 for _ in range(6)]
    intruder[0][:3], intruder[1][:3], intruder[2][:3] = [2, 2, 2], [2, 3, 0], [2, 2, 2]
    intruder[4] = [3] * 8
    return [
        {"name": "global_fragmentation", "input": fragmented, "expected": {"minimum": [[2, 2]], "maximum": [[3]]}},
        {"name": "row_major_tie", "input": tie, "expected": {"minimum": [[8, 8]], "maximum": [[8, 8]]}},
        {"name": "diagonal_split", "input": diagonal, "expected": {"minimum": [[8]], "maximum": [[2, 2, 2]]}},
        {"name": "unmasked_intruder", "input": intruder, "expected": {"minimum": [[2, 2, 2], [2, 3, 0], [2, 2, 2]], "maximum": [[3]]}},
    ]


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def build_evidence(out):
    """Small finite authoring probe: two episodes, shared witness, four contracts."""
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"evidence directory must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    source_paths = [HERE / "prototype.py", HERE / "README.md", HERE.parents[1] / "tests/test_parametric_prototype.py"]
    authority = REPO / "shared/data/base/solutions/training/d9fac9be__7944933e200f.json"
    source_hashes = {str(path.relative_to(REPO)): sha256(path.read_bytes()) for path in source_paths}
    canonical = json.loads(authority.read_text())["racket_target"]["target_code"]
    if emit_rule() != canonical:
        raise AssertionError("canonical setting no longer matches recorded authority")
    source_hashes[str(authority.relative_to(REPO))] = sha256(authority.read_bytes())
    prelude = REPO / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"
    bridge_source = REPO / "shared/runtime/arc_repl/racket_bridge.py"
    for path in (prelude, bridge_source):
        source_hashes[str(path.relative_to(REPO))] = sha256(path.read_bytes())
    first_seeds = {setting: next(seed for seed in range(1000) if choose_setting(seed) == setting) for setting in SETTINGS}
    episodes = []
    with RacketRunner() as runner:
        for setting in SETTINGS:
            seed = first_seeds[setting]
            episode = generate_episode(seed, runner=runner)
            assert episode["private"]["parameters"][PARAMETER] == setting
            _write_json(out / "public" / f"episode-{len(episodes)}.json", episode["public"])
            _write_json(out / "private" / f"episode-{len(episodes)}.json", episode["private"])
            program = emit_rule(setting)
            (out / "private" / f"{setting}.rkt").write_text(program + "\n")
            episodes.append({"setting": setting, "seed": seed, "public_file": f"public/episode-{len(episodes)}.json", "private_file": f"private/episode-{len(episodes)}.json", "program_sha256": sha256(program.encode()), "demo_consistent_settings": episode["private"]["demo_consistent_settings"]})
        shared = make_input(20261023, 0)
        differing = {"input": shared, "seed": 20261023, "pair_index": 0, "input_sha256": grid_hash(shared), "outputs": {setting: runner.execute(shared, setting, label=f"shared:{setting}") for setting in SETTINGS}}
        assert differing["outputs"]["minimum"] != differing["outputs"]["maximum"]
        _write_json(out / "private/differentiating-input.json", differing)
        witness_results = []
        for case in semantic_witnesses():
            outputs = {setting: runner.execute(case["input"], setting, label=f"semantic:{case['name']}:{setting}") for setting in SETTINGS}
            if outputs != case["expected"]:
                raise AssertionError(f"wrong contract witness: {case['name']}")
            witness_results.append({**case, "actual": outputs, "passed": True, "input_sha256": grid_hash(case["input"])})
        _write_json(out / "private/semantic-witnesses.json", witness_results)
        receipts = {"schema": "arc-parametric-racket-executions-v1", "executions": runner.executions, "count": len(runner.executions), "runtime_binary": runner.bridge.racket_binary}
        _write_json(out / "private/bridge-receipts.json", receipts)
    report = {"schema": "arc-parametric-prototype-evidence-v1", "status": "proposed_unapproved_prototype", "task_id": TASK_ID, "parameter_spec": PARAMETER_SPEC, "source_sha256": source_hashes, "canonical_default_exact_match": True, "program_hash_definition": "sha256 of emit_rule UTF-8 bytes without trailing newline; .rkt files add one display newline", "episodes": episodes, "episode_count": len(episodes), "demo_count": 6, "query_count": 2, "semantic_witness_count": len(witness_results), "racket_execution_count": receipts["count"], "public_payload_policy": "public/*.json contains only train input/output pairs and test inputs; filename/index exposes no setting, seed or rule", "limitations": ["One proposed bounded parameter; neither variant nor prototype approved for production", "Finite probe uses two seeded episodes and a compact structured constructor, not arbitrary all-grid proof or broad diversity claim", "Rival identifiability checks cover the two declared settings only", "Existing production per-puzzle API remains fixed canonical and is not changed"]}
    _write_json(out / "private/manifest.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new evidence directory, relative to repo when called through review.py")
    args = parser.parse_args()
    report = build_evidence(args.out)
    print(json.dumps({key: report[key] for key in ("status", "episode_count", "demo_count", "query_count", "semantic_witness_count", "racket_execution_count")}, sort_keys=True))


if __name__ == "__main__":
    main()

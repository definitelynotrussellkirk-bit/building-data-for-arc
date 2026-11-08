"""Causal scale-map family preserving the exact canonical fixed-scale default.

The alternative performs two genuinely dependent stages. Step A expands rows
according to occurrences of the top-left target color. Step B then measures that
new intermediate and expands its target-densest column. The same input grammar
is used for both settings, so demonstrations must teach the rule rather than a
setting-specific sampler cue.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random


TASK_ID = "ecd1058990ce"
HERE = Path(__file__).resolve().parent
MODES = ("fixed_outer", "target_weighted")
DEMO_TEMPLATES = (
    ((0, 0, 1), (1, 0, 0), (0, 1, 2)),  # weighted middle; rejects raw-count order.
    ((0, 1, 0), (1, 2, 3), (2, 3, 0)),  # light row breaks heavy-row tie to right.
    ((0, 0, 1), (0, 2, 0), (1, 0, 2)),  # weighted left winner
    ((0, 0, 1), (2, 0, 3), (1, 2, 0)),  # light row breaks heavy-row tie to middle.
    ((0, 1, 2), (3, 0, 1), (2, 3, 0)),  # no heavy rows
    ((0, 0, 1), (0, 2, 0), (1, 0, 0)),  # all heavy rows
)
QUERY_TEMPLATES = (
    ((0, 0, 1), (2, 0, 0), (0, 3, 0)),  # 30x30, content in every quadrant
    ((0, 0, 1), (2, 0, 0), (0, 3, 1)),  # 21x30; Step A moves winner left -> middle
    ((0, 0, 1), (2, 3, 0), (1, 0, 2)),  # 12x30
    ((0, 1, 2), (1, 0, 3), (2, 3, 0)),  # 3x30
)


def _integer(value, label, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (
        maximum is not None and value > maximum
    ):
        raise ValueError(f"{label} must be an exact integer in {minimum}..{maximum}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"scale_mode"}:
        raise ValueError("settings must contain exactly scale_mode")
    value = settings["scale_mode"]
    if type(value) is not str or value not in MODES:
        raise ValueError("scale_mode must be fixed_outer or target_weighted")
    return value


def _grid(grid):
    if type(grid) is not list or len(grid) != 3:
        raise ValueError("scale-map family inputs must have exactly three rows")
    if any(
        type(row) is not list
        or len(row) != 3
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("input must be a 3x3 grid of exact integer colors 0..9")
    return grid


def _output_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("output must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("output must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("output must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    """Return complete exact Racket text for one declared setting."""
    return (HERE / f"{_setting(settings)}.rkt").read_text(encoding="utf-8")


def _scale_map(grid, row_scales, column_scales):
    _grid(grid)
    if len(row_scales) != 3 or len(column_scales) != 3:
        raise ValueError("scale vectors must match the 3x3 source")
    if any(type(value) is not int or value < 1 for value in (*row_scales, *column_scales)):
        raise ValueError("scale factors must be positive exact integers")
    output = []
    for row, row_scale in zip(grid, row_scales):
        expanded = [cell for cell, scale in zip(row, column_scales) for _ in range(scale)]
        for _ in range(row_scale):
            output.append(expanded[:])
    return output


def _column_counts(grid, target):
    return [sum(row[column] == target for row in grid) for column in range(len(grid[0]))]


def target_weighted_state(grid):
    """Expose the alternative's actual A -> intermediate -> B causal state."""
    _grid(grid)
    target = grid[0][0]
    row_scales = [10 if row.count(target) >= 2 else 1 for row in grid]
    intermediate = _scale_map(grid, row_scales, (1, 1, 1))
    original_counts = _column_counts(grid, target)
    intermediate_counts = _column_counts(intermediate, target)
    selected = intermediate_counts.index(max(intermediate_counts))
    return {
        "target": target,
        "row_scales": row_scales,
        "intermediate": intermediate,
        "original_column_counts": original_counts,
        "intermediate_column_counts": intermediate_counts,
        "selected_column": selected,
    }


def _expand_selected(intermediate, selected):
    column_scales = [28 if column == selected else 1 for column in range(3)]
    output = []
    for row in intermediate:
        output.append([cell for cell, scale in zip(row, column_scales) for _ in range(scale)])
    return output


def transform_wrong_order(grid):
    """Counterfactual: select a column before Step A changes its evidence."""
    state = target_weighted_state(grid)
    selected = state["original_column_counts"].index(max(state["original_column_counts"]))
    return _expand_selected(state["intermediate"], selected)


def _transform_fixed_column(grid, selected):
    state = target_weighted_state(grid)
    return _expand_selected(state["intermediate"], selected)


def transform(grid, settings):
    mode = _setting(settings)
    _grid(grid)
    if mode == "fixed_outer":
        return _scale_map(grid, (2, 1, 2), (2, 1, 2))
    state = target_weighted_state(grid)
    return _expand_selected(state["intermediate"], state["selected_column"])


def _rng(seed, stream, index):
    key = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def sample_input(seed, stream, index):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    if stream not in {"train", "test"}:
        raise ValueError("stream must be train or test")
    templates = DEMO_TEMPLATES if stream == "train" else QUERY_TEMPLATES
    if index >= len(templates):
        raise ValueError("index exceeds the bounded teaching bank")
    rng = _rng(seed, stream, index)
    colors = rng.sample(range(10), 4)
    template = templates[index]
    return [[colors[symbol] for symbol in row] for row in template]


def generate(seed, settings, demos, queries):
    """Native adapter contract with setting-independent, prefix-stable inputs."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    episode = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(key)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    return episode


def _target_program(selected_expression):
    """Build a finite fixed-column shortcut using the same row-expansion stage."""
    return f"""(rule! (lambda (g)
  (let* ((target (at g 0 0))
         (row-scales
          (for/list ((r (in-range (rows g))))
            (if (>= (for/sum ((c (in-range (cols g))))
                      (if (= (at g r c) target) 1 0))
                    2)
                10
                1)))
         (intermediate (scale-map g row-scales (make-list (cols g) 1)))
         (selected-column {selected_expression})
         (column-scales
          (for/list ((c (in-range (cols intermediate))))
            (if (= c selected-column) 28 1))))
    (scale-map intermediate (make-list (rows intermediate) 1) column-scales))))"""


def hypotheses(settings):
    """Finite semantic rivals for bounded demonstration-only self-review."""
    _setting(settings)
    return {
        **{f"setting:{mode}": program({"scale_mode": mode}) for mode in MODES},
        "identity": "(rule! (lambda (g) g))",
        "wrong_order": (HERE / "wrong_order.rkt").read_text(encoding="utf-8"),
        "heavy_rows_only": (HERE / "heavy_rows_only.rkt").read_text(encoding="utf-8"),
        "always_left": _target_program("0"),
        "always_middle": _target_program("1"),
        "always_right": _target_program("2"),
    }


class Reference:
    """One protected-Racket process reused across a bounded authoring study."""

    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=10.0)
        self.names = {}
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.shutdown()

    def apply(self, source, grid):
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.names:
            name = "causal_scale_rule_" + str(len(self.names))
            self.bridge.eval_text(f"(define {name} {wrap_rule(source)})")
            self.names[source] = name
        self.bridge.define_grid("causal_scale_input", grid)
        output = self.bridge.eval_text(f"({self.names[source]} causal_scale_input)")
        self.calls += 1
        return deepcopy(_output_grid(output))


def fit_demonstrations(train, settings, reference):
    """Fit only the visible demonstrations against a bounded rival family."""
    programs = hypotheses(settings)
    survivors = []
    rejected = {}
    for name, source in programs.items():
        mismatches = []
        for index, pair in enumerate(train):
            if reference.apply(source, pair["input"]) != pair["output"]:
                mismatches.append(index)
        if mismatches:
            rejected[name] = mismatches
        else:
            survivors.append(name)
    return {
        "survivors": survivors,
        "rejected_by_demo": rejected,
        "program_sha256": {
            name: hashlib.sha256(source.encode()).hexdigest() for name, source in programs.items()
        },
    }


def verify_episode(episode, reference):
    """Reject false labels, repeats, malformed grids, and finite-rival ambiguity."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = episode.get("settings")
    chosen = _setting(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("episode program differs from its fixed setting")
    seen = set()
    for split, minimum, maximum in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not minimum <= len(pairs) <= maximum:
            raise ValueError(f"{split} count must be in {minimum}..{maximum}")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("every private pair needs input and output")
            _grid(pair["input"])
            _output_grid(pair["output"])
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(key)
            if reference.apply(program(settings), pair["input"]) != pair["output"]:
                raise ValueError("claimed output differs from executed Racket")
    fit = fit_demonstrations(episode["train"], settings, reference)
    if fit["survivors"] != ["setting:" + chosen]:
        raise ValueError("demonstrations do not uniquely identify the selected finite setting")
    programs = hypotheses(settings)
    checks = []
    for index, pair in enumerate(episode["test"]):
        for name in fit["survivors"]:
            if reference.apply(programs[name], pair["input"]) != pair["output"]:
                raise ValueError(f"demonstrations do not identify query {index}: {name}")
        checks.append({"query_index": index, "identified_from_demonstrations": True})
    return {
        "schema": "causal-scale-map-finite-rivals-v1",
        **fit,
        "fit_uses": "demonstrations_only",
        "query_checks": checks,
        "limit": "Only two declared settings and six named shortcuts are tested.",
    }


def source_bindings():
    files = [
        HERE / name
        for name in (
            "prototype.py",
            "adapter.py",
            "promotion.json",
            "fixed_outer.rkt",
            "target_weighted.rkt",
            "wrong_order.rkt",
            "heavy_rows_only.rkt",
            "probe.py",
        )
    ]
    files.append(HERE.parents[1] / "generator.py")
    return {
        str(path.relative_to(HERE.parents[3])): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }

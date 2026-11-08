"""Proposed full-template versus marker-fragment ray propagation family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
TASK_ID = "b2d6e6b60917"
TEMPLATES = ("full", "fragment")


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "_b2_parametric_geometry_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"template"}
        or type(settings["template"]) is not str
        or settings["template"] not in TEMPLATES
    ):
        raise ValueError("settings must be exactly {'template': 'full'|'fragment'}")
    return settings["template"]


def program(settings):
    template = _setting(settings)
    return (HERE / ("canonical.rkt" if template == "full" else "fragment.rkt")).read_text(encoding="utf-8")


def _derived_seed(seed, split, index, attempt=0):
    raw = json.dumps([TASK_ID, "input-v1", seed, split, index, attempt], separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & (2**63 - 1)


def _standard_input(seed, index, *, split, attempt=0):
    n_markers = 2 + ((index + (0 if split == "train" else 1)) % 2)
    difficulty = ("easy", "medium", "hard")[(index + (0 if split == "train" else 1)) % 3]
    return GEN.generate(
        _derived_seed(seed, split, index, attempt),
        index + (0 if split == "train" else 100),
        difficulty=difficulty,
        n_markers=n_markers,
    )


def _large_scene(seed):
    """Construct one 30x30 three-ray scene, independent of private setting."""
    shape = tuple(GEN._SHAPES_3X3[3])
    directions = ((-1, -1), (1, 1), (1, -1))
    fragments = tuple(
        GEN._marker_fragment(shape, direction, include_second_layer=bool(index % 2))
        for index, direction in enumerate(directions)
    )
    candidates = GEN._placement_candidates(
        shape, directions, fragments, height=30, width=30
    )
    if not candidates:
        raise RuntimeError("no lawful 30x30 placement for the fixed ray scene")
    # Center the source so opposite diagonal rays cover both canvas dimensions.
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    top, left = min(
        candidates,
        key=lambda p: (
            abs((p[0] + (shape_h - 1) / 2) - 14.5)
            + abs((p[1] + (shape_w - 1) / 2) - 14.5),
            p,
        ),
    )
    grid = [[0] * 30 for _ in range(30)]
    for r, c in shape:
        grid[top + r][left + c] = 8
    for (dr, dc), fragment, color in zip(directions, fragments, (2, 3, 4)):
        shift_r = dr * (shape_h + 1)
        shift_c = dc * (shape_w + 1)
        for r, c in fragment:
            grid[top + r + shift_r][left + c + shift_c] = color
    GEN._analyze_grid(grid)
    return grid


def sample_input(seed, index, *, split, attempt=0):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(attempt, 0, 31, "attempt")
    if split == "train":
        _integer(index, 0, 5, "index")
    elif split == "test":
        _integer(index, 0, 3, "index")
    else:
        raise ValueError("split must be train or test")
    if split == "test" and index == 3:
        # Seed deliberately does not affect the fixed hard geometry; the input is
        # still unique within every episode and independent of the setting.
        return _large_scene(seed)
    return _standard_input(seed, index, split=split, attempt=attempt)


def claimed_output(grid, settings):
    mode = "shape" if _setting(settings) == "full" else "fragment"
    return GEN._render(deepcopy(grid), source_cells=mode)


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    draws = 0
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            for attempt in range(32):
                grid = sample_input(seed, index, split=split, attempt=attempt)
                draws += 1
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    break
            else:
                raise ValueError(f"distinct input budget exhausted for {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": claimed_output(grid, settings)})
    result["sampling"] = {"draws": draws, "duplicate_rejections": draws - demos - queries}
    return result


def teaching_certificate(episode):
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain demonstrations")
    survivors, rejected = [], {}
    for template in TEMPLATES:
        setting = {"template": template}
        mismatch = next(
            (i for i, pair in enumerate(episode["train"]) if claimed_output(pair["input"], setting) != pair["output"]),
            None,
        )
        if mismatch is None:
            survivors.append(setting)
        else:
            rejected[template] = mismatch
    return {"survivors": survivors, "rejected_by_demo": rejected, "query_answers_used": False}


def visible_turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})


def public_identity(episode):
    return public_challenge_id(episode)

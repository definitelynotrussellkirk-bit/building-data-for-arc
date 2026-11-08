"""Rotation matching followed by a turn-conditioned reflected selection.

The canonical source and sampling remain untouched. This separate grammar has
two possible template families below the divider, so the lower scene alone
does not determine a label. Labels here are claims; native qualification and
the retained audit execute the matching programs through protected Racket.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
TASK_ID = "1d26c382ab68"
DEFAULT = {"target": "rotation_match"}
ALTERNATIVE = {"target": "turn_guided_reflection"}
PROFILES = ((11, 13, 1), (20, 22, 2), (24, 26, 2), (30, 30, 3))
_base, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"target"}
            or type(settings["target"]) is not str
            or settings["target"] not in ("rotation_match", "turn_guided_reflection")):
        raise ValueError("target must be rotation_match or turn_guided_reflection, with no extra keys")
    return settings["target"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    mode = _settings(settings)
    name = "canonical.rkt" if mode == "rotation_match" else "reflection.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def counterfactual_program(ablation):
    """Standalone, executable semantic ablations for the retained witness."""
    source = program(ALTERNATIVE)
    target = "(rotate-by (flip-lr template-shape) turn)"
    replacements = {
        "wrong_order": "(flip-lr (rotate-by template-shape turn))",
        "wrong_intermediate": "(rotate-by (flip-lr template-shape) (+ turn 1))",
        "skip_a": "(flip-lr template-shape)",
    }
    if ablation not in replacements:
        raise ValueError("unknown causal ablation")
    if source.count(target) != 1:
        raise ValueError("the declared causal expression changed")
    return source.replace(target, replacements[ablation])


def _scale(shape, scale):
    return _base._normalize((r * scale + dr, c * scale + dc)
                            for r, c in shape
                            for dr in range(scale) for dc in range(scale))


def _orbit(shape):
    return set(_base._rotations(shape)) | set(_base._rotations(_base._reflect_lr(shape)))


@lru_cache(maxsize=3)
def _admitted_shapes(scale):
    return set().union(*(_orbit(_scale(shape, scale)) for shape in _base._TEMPLATE_FAMILIES[5]))


def analyze(grid):
    """Observe only visible cells; no latent sampler state enters selection."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    separators = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    if len(separators) != 1 or separators[0] in (0, h - 1):
        raise ValueError("one internal full maroon separator is required")
    sep = separators[0]
    if any(value == 9 and r != sep for r, row in enumerate(grid) for value in row):
        raise ValueError("maroon may appear only on the separator")
    if {v for row in grid[:sep] for v in row} - {0, 1}:
        raise ValueError("upper region contains only background and blue template")
    templates = _base._components(grid, row_lo=0, row_hi=sep - 1, predicate=lambda v: v == 1)
    if len(templates) != 1:
        raise ValueError("one connected blue template is required")
    template = _base._normalize(templates[0])
    scale = {5: 1, 20: 2, 45: 3}.get(len(template))
    if scale is None or template not in _admitted_shapes(scale):
        raise ValueError("template must be an admitted chiral pentomino at scale 1, 2 or 3")
    colors = {v for row in grid[sep + 1:] for v in row if v != 0}
    if len(colors) != 1 or next(iter(colors)) not in range(3, 9):
        raise ValueError("candidates share one color in 3..8")
    color = next(iter(colors))
    cells = _base._components(grid, row_lo=sep + 1, row_hi=h - 1, predicate=lambda v: v == color)
    cells.sort(key=lambda component: (min(r for r, _ in component), min(c for _, c in component)))
    shapes = [_base._normalize(component) for component in cells]
    if len(shapes) != 6 or any(len(shape) != len(template) for shape in shapes):
        raise ValueError("six separated same-sized candidate objects are required")
    rotations = _base._rotations(template)
    matches = [(i, rotations.index(shape)) for i, shape in enumerate(shapes) if shape in rotations]
    if len(matches) != 1:
        raise ValueError("exactly one rotational match is required")
    match, turn = matches[0]
    reflected = _base._reflect_lr(template)
    reflection_slots = [i for i, shape in enumerate(shapes) if shape in _base._rotations(reflected)]
    target = _base._rotate(reflected, turn)
    opposite = _base._rotate(reflected, turn + 2)
    if len(reflection_slots) != 2 or {shapes[i] for i in reflection_slots} != {target, opposite}:
        raise ValueError("both opposite turn-conditioned reflected candidates are required")
    others = [shape for shape in shapes if shape not in _orbit(template)]
    if (len(others) != 3 or len(set(others)) != 3 or others[0] not in _admitted_shapes(scale)
            or any(shape not in _orbit(others[0]) for shape in others)):
        raise ValueError("the second template family must be distinct, chiral and same-sized")
    return {"separator": sep, "template": template, "cells": cells, "shapes": shapes,
            "match_slot": match, "turn": turn, "turn_parity": turn % 2,
            "target_slot": shapes.index(target), "reflection_slots": reflection_slots,
            "scale": scale, "candidate_color": color}


def _paint(grid, info, slots):
    output = deepcopy(grid)
    for slot in slots:
        for row, col in info["cells"][slot]:
            output[row][col] = 2
    return output


def expected_output(grid, settings):
    mode = _settings(settings)
    info = analyze(grid)
    slot = info["match_slot"] if mode == "rotation_match" else info["target_slot"]
    return _paint(grid, info, [slot])


def rival_outputs(grid):
    """Finite plausible alternatives; execution errors never count as rejection."""
    info = analyze(grid)
    shapes, template = info["shapes"], info["template"]
    match = shapes[info["match_slot"]]

    def select(shape):
        return _paint(grid, info, [i for i, candidate in enumerate(shapes) if candidate == shape])

    outputs = {
        "rotation_match": _paint(grid, info, [info["match_slot"]]),
        "turn_guided_reflection": _paint(grid, info, [info["target_slot"]]),
        "reflection_any": _paint(grid, info, info["reflection_slots"]),
        "same_size_all": _paint(grid, info, range(6)),
        "identity": deepcopy(grid),
        "reflect_match": select(_base._reflect_lr(match)),
        "inverse_turn": select(_base._rotate(_base._reflect_lr(template), -info["turn"])),
        "lower_only_lexicographic": _paint(grid, info, [min(range(6), key=lambda i: shapes[i])]),
    }
    for k in range(4):
        outputs[f"fixed_reflected_template_turn_{k}"] = select(_base._rotate(_base._reflect_lr(template), k))
        outputs[f"fixed_reflected_match_turn_{k}"] = select(_base._rotate(_base._reflect_lr(match), k))
    for slot in range(6):
        outputs[f"fixed_slot_{slot}"] = _paint(grid, info, [slot])
    return outputs


def teaching_check(episode):
    """Fit rivals to demos only; query answers never select a survivor."""
    predictions = [rival_outputs(pair["input"]) for pair in episode["train"]]
    survivors = [name for name in predictions[0]
                 if all(prediction[name] == pair["output"]
                        for prediction, pair in zip(predictions, episode["train"]))]
    queries = [rival_outputs(pair["input"]) for pair in episode["test"]]
    ambiguities = []
    for name in survivors:
        disagreements = [i for i, (prediction, pair) in enumerate(zip(queries, episode["test"]))
                         if prediction[name] != pair["output"]]
        if disagreements:
            ambiguities.append({"rival": name, "queries": disagreements})
    return {"rivals_tested": len(predictions[0]), "survivors": survivors, "ambiguities": ambiguities,
            "scope": "Finite declared rivals, fit on original demonstrations only; not universal uniqueness."}


def _rng(seed, scene):
    digest = hashlib.sha256(f"{TASK_ID}:parametric-v1:{seed}:{scene}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _slack(amount, n, rng):
    buckets = [0] * n
    for _ in range(amount):
        buckets[rng.randrange(n)] += 1
    return buckets


def _paired_scene(seed, scene, profile):
    """Two top templates, exactly the same lower scene; independent of settings."""
    rng = _rng(seed, scene)
    height, width, scale = profile
    family_a = rng.choice(_base._TEMPLATE_FAMILIES[5])
    family_b = rng.choice([shape for shape in _base._TEMPLATE_FAMILIES[5] if shape not in _orbit(family_a)])
    templates = [_scale(_base._rotate(shape, rng.randrange(4)), scale) for shape in (family_a, family_b)]
    turn_a = rng.randrange(4)
    turns = [turn_a, (turn_a + rng.choice((1, 3))) % 4]
    shapes = []
    for template, turn in zip(templates, turns):
        shapes.extend((_base._rotate(template, turn),
                       _base._rotate(_base._reflect_lr(template), turn),
                       _base._rotate(_base._reflect_lr(template), turn + 2)))
    rng.shuffle(shapes)
    slot_size = 3 * scale
    sep = rng.randint(slot_size, height - (2 * slot_size + 2))
    grid = [[0] * width for _ in range(height)]
    grid[sep] = [9] * width
    color = rng.randrange(3, 9)
    column_gaps = _slack(width - (3 * slot_size + 2), 4, rng)
    row_gaps = _slack(height - sep - 1 - (2 * slot_size + 1), 3, rng)
    lefts = [column_gaps[0]]
    for i in range(2):
        lefts.append(lefts[-1] + slot_size + 1 + column_gaps[i + 1])
    tops = [sep + 1 + row_gaps[0], sep + 1 + row_gaps[0] + slot_size + 1 + row_gaps[1]]
    for index, shape in enumerate(shapes):
        sh, sw = _base._bbox(shape)
        top = tops[index // 3] + rng.randint(0, slot_size - sh)
        left = lefts[index % 3] + rng.randint(0, slot_size - sw)
        for row, col in shape:
            grid[top + row][left + col] = color
    result = []
    for template in templates:
        instance = deepcopy(grid)
        th, tw = _base._bbox(template)
        top, left = rng.randint(0, sep - th), rng.randint(0, width - tw)
        for row, col in template:
            instance[top + row][left + col] = 1
        analyze(instance)
        result.append(instance)
    return result


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = _paired_scene(seed, 0, PROFILES[0])
    seen = {json.dumps(grid) for grid in train}

    def novel(scene, profile, choice):
        for retry in range(16):
            grid = _paired_scene(seed, scene + 1000 * retry, profile)[choice]
            key = json.dumps(grid)
            if key not in seen:
                seen.add(key)
                return grid
        raise ValueError("bounded input uniqueness budget exhausted")

    for i in range(2, demos):
        train.append(novel(i, PROFILES[(i - 1) % len(PROFILES)], i % 2))
    test = [novel(100 + i, PROFILES[i], (seed + i) % 2) for i in range(queries)]
    episode = {"train": [{"input": grid, "output": expected_output(grid, settings)} for grid in train],
               "test": [{"input": grid, "output": expected_output(grid, settings)} for grid in test],
               "program_solution": program(settings), "settings": deepcopy(settings), "seed": seed}
    certificate = teaching_check(episode)
    if certificate["ambiguities"] or certificate["survivors"] != [settings["target"]]:
        raise ValueError(f"constructive teaching invariant failed: {certificate}")
    episode["teaching"] = certificate
    return episode


def model_view(episode, query_index):
    """Project one turn; no future query, query label, settings or count hint."""
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                       for pair in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][query_index]["input"])}]}

"""Native forward/reverse symbol traversal with constructive teaching examples.

Python outputs are claims. Native qualification and generation independently
execute the exact setting program with the protected Racket runtime.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes


TASK_ID = "f0f2806877da"
ORDERS = ("forward", "reverse")
HOME = Path(__file__).resolve().parent


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"read_order"}
            or type(settings["read_order"]) is not str
            or settings["read_order"] not in ORDERS):
        raise ValueError("settings must be exactly read_order=forward or reverse")
    return settings["read_order"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


@lru_cache(maxsize=1)
def _canonical():
    return (HOME / "canonical.rkt").read_text(encoding="utf-8")


def program(settings):
    order = _settings(settings)
    canonical = _canonical()
    if order == "forward":
        return canonical
    needle = "(types (map piece-type pieces))"
    if canonical.count(needle) != 1:
        raise ValueError("canonical decoder changed; review the reverse adapter")
    return canonical.replace(needle, "(types (reverse (map piece-type pieces)))")


@lru_cache(maxsize=1)
def _source():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


@lru_cache(maxsize=1)
def _banks():
    """Reuse the complete reviewed grammar, with a diagnostic teaching subset."""
    gen = _source()
    ordinary = defaultdict(list)
    diagnostic = defaultdict(list)
    contrast = defaultdict(list)
    for code, (grid, types) in enumerate(zip(gen.ENCODINGS, gen.ENCODING_TYPES)):
        ordinary[types].append(code)
        if types == types[::-1] or 1 not in types or 2 not in types:
            continue
        pieces, _ = gen._parse(grid)
        # A left symbol with upper row 00 and a right symbol with upper row 22
        # distinguish the actual upper-left decoder from the known upper-right
        # shortcut. Width-one upper-zero symbols expose width-first decoding.
        has_left_00 = any(t == 1 and grid[0][s] == grid[0][e] == 0
                          for s, e, t in pieces)
        has_right_22 = any(t == 2 and grid[0][s] == grid[0][e] == 2
                           for s, e, t in pieces)
        has_straight_0 = any(t == 0 and grid[0][s] == 0 for s, _, t in pieces)
        if has_left_00 and has_right_22 and has_straight_0:
            diagnostic[types].append(code)
        has_left_02 = any(t == 1 and grid[0][s] == 0 and grid[0][e] == 2
                          for s, e, t in pieces)
        has_right_20 = any(t == 2 and grid[0][s] == 2 and grid[0][e] == 0
                           for s, e, t in pieces)
        if has_left_02 and has_right_20:
            contrast[types].append(code)
    if any(sum(t.count(1) == n for t in bank) < 2
           for n in (1, 2) for bank in (diagnostic, contrast)):
        raise ValueError("the reviewed grammar no longer supports the teaching design")
    return dict(ordinary), dict(diagnostic), dict(contrast)


def predict(grid, settings):
    """Validated Python label claim; authoritative labels come from Racket."""
    order = _settings(settings)
    gen = _source()
    errors = gen.self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    pieces, _ = gen._parse(grid)
    types = tuple(piece[2] for piece in pieces)
    return gen._output(types if order == "forward" else types[::-1])


def generate(seed, settings, demos, queries):
    """Return one deterministic lesson, with counts independent of its rule.

    Always construct the same six-demo/four-query private plan, then take the
    requested prefixes. The query stream is unchanged by total query count,
    demo count, or rule setting. No rejection loop or short-batch fallback.
    """
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    gen = _source()
    ordinary, diagnostic, contrast = _banks()
    rng = random.Random(f"{TASK_ID}:read-order-inputs:{seed}")

    # Same command multiset, different order and path: a count-only or
    # endpoint-only interpretation cannot explain even the two-demo lesson.
    left_count = rng.choice((1, 2))
    teachers = sorted(t for t in diagnostic if t.count(1) == left_count)
    first_type = rng.choice(teachers)
    contrasts = sorted(t for t in contrast if t.count(1) == left_count and t != first_type)
    second_type = rng.choice(contrasts)
    first_types = (first_type, second_type)
    # The two lessons together expose 00, 02, 20 and 22 upper-row bend
    # patterns. A diagonal-only teacher leaves other plausible decoders alive.
    codes = [rng.choice(diagnostic[first_type]), rng.choice(contrast[second_type])]
    used = set(first_types)
    mixed = sorted(t for t in ordinary if 1 in t and 2 in t and t not in used)
    extra_types = rng.sample(mixed, 4)
    codes.extend(rng.choice(ordinary[t]) for t in extra_types)
    used.update(extra_types)

    query_types = []
    for left_bends in (3, 0, 1, 2):
        candidates = sorted(t for t in ordinary if t.count(1) == left_bends and t not in used)
        chosen = rng.choice(candidates)
        query_types.append(chosen)
        used.add(chosen)
    query_codes = [rng.choice(ordinary[t]) for t in query_types]

    def pair(code):
        grid = [list(row) for row in gen.ENCODINGS[code]]
        return {"input": grid, "output": predict(grid, settings)}

    return {"train": [pair(c) for c in codes[:demos]],
            "test": [pair(c) for c in query_codes[:queries]],
            "program_solution": program(settings),
            "settings": dict(settings)}


def public_turn(episode, query_index):
    """Exact visible bytes for one reveal; no future inputs or count hints."""
    tests = episode.get("test")
    if type(tests) is not list or not tests:
        raise ValueError("episode needs controller-side queries")
    _integer(query_index, 0, len(tests) - 1, "query_index")
    return public_challenge_bytes({"train": episode["train"],
                                   "test": [tests[query_index]]})

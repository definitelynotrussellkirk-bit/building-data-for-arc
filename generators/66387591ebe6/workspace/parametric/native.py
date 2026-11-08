"""Native parameter family: canonical keyed rotation / first-hit-size rotation.

Input sampling is independent of the hidden setting and of requested counts.
All returned labels are executed in the protected Racket runtime.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_rotation_rules_" + hashlib.sha256(str(HOME).encode()).hexdigest(), HOME / "rules.py")
_rules = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rules)

SETTINGS = ("key", "hit_size")
_DEMOS = ((9, 1, 2, 2), (9, 2, 1, 2), (13, 3, 4, 2),
          (15, 4, None, 0), (17, 1, 7, 2), (19, 2, 6, 4))
_QUERIES = ((9, 4, 1, 1), (17, 3, 6, 3), (23, 2, None, 0), (30, 1, 7, 9))
_SHAPE = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3))


def _integer(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an exact integer in {minimum}..{maximum}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"turn_source"}
            or type(settings["turn_source"]) is not str
            or settings["turn_source"] not in SETTINGS):
        raise ValueError("settings must be exactly {'turn_source': 'key'|'hit_size'}")
    return settings["turn_source"]


def program(settings):
    setting = _setting(settings)
    if setting == "key":
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    return _rules.build_rule()


def rival_programs(settings):
    return _rules.rivals(_setting(settings))


def _rng(seed, stream):
    digest = hashlib.sha256(f"66387591ebe6/{seed}/{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(profile, palette, rng):
    n, key, target_size, distance = profile
    if n == 30:
        pivot = rng.choice(((14, 15), (15, 14)))
    else:
        middle = n // 2
        offset = rng.choice(((0, 1), (1, 0), (0, -1), (-1, 0)))
        pivot = (middle + offset[0], middle + offset[1])
    radius = min(*pivot, n - 1 - pivot[0], n - 1 - pivot[1])
    dy, dx = ((-1, 0), (0, 1), (1, 0), (0, -1))[key - 1]
    grid = [[0] * n for _ in range(n)]
    grid[0][0], grid[pivot[0]][pivot[1]] = key, 9

    def put(forward, lateral, color):
        r = pivot[0] + forward * dy + lateral * dx
        c = pivot[1] + forward * dx - lateral * dy
        if not (-radius <= forward <= radius and -radius <= lateral <= radius):
            raise AssertionError("Profile exceeds its rotation-safe square")
        if (r, c) in {(0, 0), pivot} or grid[r][c] != 0:
            raise AssertionError("Constructive components overlap a reserved cell")
        grid[r][c] = color

    # Long, colored distractors make large-grid rotation substantive. They
    # span the complete safe square and must move with the selected payload.
    for f in range(-radius, radius + 1):
        put(f, -radius, palette[1])
        put(f, radius, palette[4])
        if f % 3 == rng.randrange(3) and f <= 0:
            put(f, -radius + 1, palette[1])
    for lateral in range(-radius + 2, radius - 1):
        put(-radius, lateral, palette[5])
    # A disconnected component of the target color rejects global-color count.
    put(-1, 1, palette[0])
    if target_size is not None:
        for f, lateral in _SHAPE[:target_size]:
            put(distance + f, lateral, palette[0])
        # Same-color diagonal neighbor; different-color orthogonal neighbor.
        put(distance + 1, -1, palette[0])
        put(distance, -1, palette[3])
        # A farther ray hit is a distinct component, not an accidental extension.
        put(radius, 0, palette[2])
    return grid


def sample_inputs(seed, demos=5, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 5, 6, "demos")
    _integer(queries, 1, 4, "queries")
    palette = list(range(1, 9))
    _rng(seed, "palette").shuffle(palette)
    train = [_scene(profile, palette, _rng(seed, f"demo/{i}"))
             for i, profile in enumerate(_DEMOS[:demos])]
    test = [_scene(profile, palette, _rng(seed, f"query/{i}"))
            for i, profile in enumerate(_QUERIES[:queries])]
    return train, test


def generate(seed, settings, demos=5, queries=4):
    source = program(settings)
    train, test = sample_inputs(seed, demos, queries)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("Labels require the protected Racket runtime")
        wrapped = wrap_rule(source)

        def pair(grid):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            return {"input": grid, "output": bridge.eval_text(f"({wrapped} {literal})")}

        return {"train": [pair(g) for g in train], "test": [pair(g) for g in test],
                "program_solution": source}
    finally:
        bridge.close()

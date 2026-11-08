"""Proposed transparent-object parameter for ARC family 0b8ba9bb3c63.

This task-local authoring prototype never changes the canonical generator or
its production rule.  Every label and every declared-rival prediction comes
from the protected Racket bridge; there is no Python labeling fallback.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shlex
import sys
import types


TASK_ID = "0b8ba9bb3c63"
PARENT = "training:6ffe8f07"
VERSION = "transparent-object-prototype-v1"
ALLOWED_TRANSPARENT_COLORS = (2, 3)
DEFAULT_TRANSPARENT_COLOR = 2
CANONICAL_NORMALIZED_SHA256 = (
    "757441c9ab4aa17070a3826de76e0b0f74e66636398f3f3aaa4392e47af17bcb"
)
HERE = Path(__file__).resolve().parent


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _integer(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def _transparent_color(value):
    if type(value) is not int or value not in ALLOWED_TRANSPARENT_COLORS:
        raise ValueError("transparent_color must be integer 2 or 3")
    return value


def _replace(source, before, after, expected=1):
    if source.count(before) != expected:
        raise RuntimeError(f"Canonical rule structure changed at {before!r}")
    return source.replace(before, after)


def materialize_rule(transparent_color=DEFAULT_TRANSPARENT_COLOR):
    """Return exact executable source; setting 2 retains all canonical bytes."""
    _transparent_color(transparent_color)
    source = (HERE / "canonical_rule.rkt").read_text(encoding="utf-8")
    if _sha(" ".join(source.split())) != CANONICAL_NORMALIZED_SHA256:
        raise RuntimeError("Canonical rule snapshot failed its normalized SHA-256 check")
    return _replace(source, "(!= (obj-color o) 2)",
                    f"(!= (obj-color o) {transparent_color})")


def declared_programs(transparent_color):
    """A finite, explicit rival family, all executed in Racket.

    Whole-arm clipping incorrectly lets a blocker in one ray stop every ray
    on that side.  No-clipping still restores opaque objects, so its mistake
    is visible behind a blocker rather than merely on the blocker itself.
    """
    source = materialize_rule(transparent_color)
    predicate = f"(and (!= (obj-color o) {transparent_color}) (!= (obj-color o) 8))"
    programs = {
        "transparent-2": materialize_rule(2),
        "transparent-3": materialize_rule(3),
        "all-opaque": _replace(source, predicate, "(!= (obj-color o) 8)"),
        "both-transparent": _replace(
            source, predicate,
            "(and (!= (obj-color o) 2) (!= (obj-color o) 3) (!= (obj-color o) 8))"),
    }
    no_clipping = source
    for initial in ("0 blockers", "(- w 1) blockers", "(- h 1) blockers"):
        expected = 2 if initial == "0 blockers" else 1
        no_clipping = _replace(no_clipping, initial,
                               initial.replace("blockers", "'()"), expected)
    programs["ignore-clipping"] = no_clipping
    whole_arm = _replace(
        source, "(<= (nth bb 0) r) (<= r (nth bb 2))",
        "(<= (nth bb 0) cr2) (<= cr1 (nth bb 2))", 2)
    whole_arm = _replace(
        whole_arm, "(<= (nth bb 1) c) (<= c (nth bb 3))",
        "(<= (nth bb 1) cc2) (<= cc1 (nth bb 3))", 2)
    programs["whole-arm-clipping"] = whole_arm
    programs["preserve-transparent-paint"] = _replace(
        source, "base3 blockers",
        "base3 (filter (lambda (o) (!= (obj-color o) 8)) objs)")
    return programs


def _validate_grid(grid, *, label="input"):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        raise ValueError(f"{label} must be a nonempty ARC grid with sides <= 30")
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError(f"{label} must be a nonempty rectangular ARC grid")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError(f"{label} must be a rectangular ARC grid with sides <= 30")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError(f"{label} grid cells must be integer ARC colors 0..9")


@lru_cache(maxsize=32)
def _wrapped(source):
    # The repository owns this pipeline.  Copied runtimes expose scripts/;
    # source checkouts keep those exact tools beside shared/runtime instead.
    # Bind that documented layout locally without changing shared files or
    # importing dependencies from a sibling checkout.
    from puzzle_generators import rule_wrap
    if importlib.util.find_spec("scripts") is None:
        local_tools = Path(rule_wrap.__file__).resolve().parents[2] / "tools"
        if not (local_tools / "comment_solutions.py").is_file():
            raise RuntimeError("Cannot find this runtime's local scripts.comment_solutions")
        scripts = types.ModuleType("scripts")
        scripts.__path__ = [str(local_tools)]
        scripts.__spec__ = importlib.util.spec_from_loader("scripts", loader=None, is_package=True)
        sys.modules["scripts"] = scripts
    return rule_wrap.wrap_rule(source)


def execute_program(source, grid, bridge):
    """Apply exact source through the shared bridge and reject malformed output."""
    _validate_grid(grid)
    literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    output = bridge.eval_text(f"({_wrapped(source)} '{literal})")
    _validate_grid(output, label="Racket output")
    return output


def _objects(grid):
    seen, objects = set(), []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color, todo, cells = grid[row][col], [(row, col)], []
            seen.add((row, col))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    pos = rr + dr, cc + dc
                    if (0 <= pos[0] < len(grid) and 0 <= pos[1] < len(grid[0])
                            and pos not in seen and grid[pos[0]][pos[1]] == color):
                        seen.add(pos)
                        todo.append(pos)
            rows, cols = zip(*cells)
            objects.append((color, cells, (min(rows), min(cols), max(rows), max(cols))))
    return objects


def validate_scene(grid):
    """Structural prototype checks, separate from Racket teaching checks."""
    try:
        _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if min(len(grid), len(grid[0])) < 17:
        errors.append("prototype sampler scenes require sides in 17..30")
    colors = {cell for row in grid for cell in row}
    if not {0, 1, 2, 3, 8} <= colors or 4 in colors:
        errors.append("require background, cyan, blue, red, green, and no yellow input")
    objects = _objects(grid)
    if sum(color == 8 for color, _, _ in objects) != 1:
        errors.append("require exactly one cyan emitter")
    for _, cells, (r1, c1, r2, c2) in objects:
        if len(cells) != (r2 - r1 + 1) * (c2 - c1 + 1):
            errors.append("source objects must be solid rectangles")
            break
    counts = {color: sum(row.count(color) for row in grid) for color in colors}
    if counts.get(0, 0) <= max((count for color, count in counts.items() if color), default=0):
        errors.append("black must be the unique modal background")
    return errors


def sample_input(rng, *, height=None, width=None):
    """Construct varied partial blockers and transparent fragments, 17..30.

    Layout draws do not depend on the hidden parameter.  Thus a paired seed
    changes the executed behavior while retaining identical input objects.
    The near/far blue blockers overlap some, but not all, horizontal rays.
    Reflections vary their absolute directions without violating exact sizes.
    """
    height = rng.randint(17, 30) if height is None else _integer(height, "height", 17, 30)
    width = rng.randint(17, 30) if width is None else _integer(width, "width", 17, 30)
    grid = [[0] * width for _ in range(height)]
    emitter_h, emitter_w = rng.randint(3, 6), rng.randint(3, 6)
    r1 = rng.randint(5, height - emitter_h - 4)
    c1 = rng.randint(5, width - emitter_w - 6)
    r2, c2 = r1 + emitter_h - 1, c1 + emitter_w - 1
    colors = [2, 3]
    rng.shuffle(colors)
    overlap_r = rng.randint(1, emitter_h - 1)
    overlap_c = rng.randint(1, emitter_w - 1)
    rectangles = (
        (8, r1, c1, emitter_h, emitter_w),
        (colors[0], r1 - 1, c1 - 3, overlap_r + 1, 2),
        (colors[1], r1 - 3, c1 - 1, 2, overlap_c + 1),
        (1, r1, c2 + 2, max(2, emitter_h // 2), rng.randint(1, 2)),
        (1, r1 + 1, c2 + 5, emitter_h - 1, 1),
        (5, r2 + 2, c1 + 1, 1, 1),
        (9, 1, 1, 2, 2),
        (rng.choice(colors), height - 3, 1, 2, 2),
    )
    for color, row, col, rect_h, rect_w in rectangles:
        for rr in range(row, row + rect_h):
            for cc in range(col, col + rect_w):
                if grid[rr][cc] != 0:
                    raise RuntimeError("Constructive layout unexpectedly overlapped objects")
                grid[rr][cc] = color
    if rng.getrandbits(1):
        grid.reverse()
    if rng.getrandbits(1):
        grid = [row[::-1] for row in grid]
    if height == width and rng.getrandbits(1):
        grid = [list(row) for row in zip(*grid)]
    errors = validate_scene(grid)
    if errors:
        raise RuntimeError("Constructive scene failed validation: " + "; ".join(errors))
    return grid


def _different_cells(left, right):
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return max(sum(map(len, left)), sum(map(len, right)))
    return sum(a != b for ra, rb in zip(left, right) for a, b in zip(ra, rb))


def check_identifiability(demonstrations, query_inputs, programs, bridge):
    """Eliminate rivals using demonstrations only, then compare predictions.

    There is deliberately no query-answer argument.  Every query receives its
    own agreement result among rules still compatible with ALL demonstrations.
    Finite declared-rival agreement is not a proof over all possible rules.
    """
    if not programs:
        raise ValueError("At least one declared program is required")
    compatible, eliminated = [], {}
    for name, source in programs.items():
        for index, pair in enumerate(demonstrations):
            _validate_grid(pair["output"], label="demonstration output")
            prediction = execute_program(source, pair["input"], bridge)
            different = _different_cells(prediction, pair["output"])
            if different:
                eliminated[name] = {"demo_index": index, "different_cells": different,
                                    "prediction_sha256": _sha(_json(prediction))}
                break
        else:
            compatible.append(name)
    query_checks = []
    for index, grid in enumerate(query_inputs):
        _validate_grid(grid)
        predictions = {
            name: _sha(_json(execute_program(programs[name], grid, bridge)))
            for name in compatible
        }
        query_checks.append({
            "query_index": index, "input_sha256": _sha(_json(grid)),
            "compatible_prediction_sha256": predictions,
            "identifiable": bool(predictions) and len(set(predictions.values())) == 1,
        })
    return {
        "scope": "finite declared Racket rivals; elimination uses demonstrations only",
        "compatible_rules": compatible, "eliminated_rules": eliminated,
        "query_checks": query_checks,
        "identified": bool(query_checks) and all(row["identifiable"] for row in query_checks),
    }


def _source_hashes():
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("prototype.py", "canonical_rule.rkt", "canonical_source.json")}


def generate_episode(*, seed, transparent_color=DEFAULT_TRANSPARENT_COLOR,
                     demo_count=3, query_count=4, height=None, width=None,
                     max_attempts=256, bridge=None):
    """Generate one episode with a single fixed rule and independent counts.

    None requests a seed-chosen parameter.  Omission retains canonical color 2.
    Sampling exhaustion or insufficient teaching evidence fails explicitly;
    no pair is cloned and no short episode is returned.
    """
    _integer(seed, "seed", -(2 ** 63), 2 ** 63 - 1)
    _integer(demo_count, "demo_count", 1, 32)
    _integer(query_count, "query_count", 1, 32)
    _integer(max_attempts, "max_attempts", 1, 10000)
    for value, name in ((height, "height"), (width, "width")):
        if value is not None:
            _integer(value, name, 17, 30)
    if transparent_color is None:
        parameter_seed = int(_sha(f"{VERSION}:{seed}:parameter"), 16)
        transparent_color = random.Random(parameter_seed).choice(ALLOWED_TRANSPARENT_COLORS)
    _transparent_color(transparent_color)
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=15) as owned:
            return generate_episode(seed=seed, transparent_color=transparent_color,
                                    demo_count=demo_count, query_count=query_count,
                                    height=height, width=width, max_attempts=max_attempts,
                                    bridge=owned)
    source = materialize_rule(transparent_color)
    rng = random.Random(int(_sha(f"{VERSION}:{seed}:layout"), 16))
    pairs, accepted, seen = [], [], set()
    requested = demo_count + query_count
    for attempt in range(max_attempts):
        grid = sample_input(rng, height=height, width=width)
        digest = _sha(_json(grid))
        if digest in seen:
            continue
        seen.add(digest)
        pairs.append({"input": grid, "output": execute_program(source, grid, bridge)})
        accepted.append(attempt)
        if len(pairs) == requested:
            break
    if len(pairs) != requested:
        raise RuntimeError(f"Only {len(pairs)} distinct inputs after {max_attempts} attempts; "
                           f"requested {requested}")
    train, test = pairs[:demo_count], pairs[demo_count:]
    programs = declared_programs(transparent_color)
    audit = check_identifiability(train, [pair["input"] for pair in test], programs, bridge)
    intended = f"transparent-{transparent_color}"
    if intended not in audit["compatible_rules"] or not audit["identified"]:
        raise RuntimeError("Demonstrations do not identify every requested query against declared rivals")
    return {
        "schema": "arc-parametric-beam-episode-v1", "status": "proposed prototype",
        "prototype_version": VERSION, "task_id": TASK_ID, "parent": PARENT,
        "seed": seed, "parameters": {"transparent_color": transparent_color},
        "requested_counts": {"demos": demo_count, "queries": query_count},
        "size_overrides": {"height": height, "width": width},
        "accepted_attempt_indices": accepted, "train": train, "test": test,
        "rule_source": source, "rule_sha256": _sha(source),
        "rule_normalized_sha256": _sha(" ".join(source.split())),
        "declared_programs": programs,
        "declared_program_sha256": {name: _sha(text) for name, text in programs.items()},
        "identifiability": audit, "source_sha256": _source_hashes(),
        "runtime_identity": bridge.runtime_identity,
        "limitations": [
            "This task-local prototype has no production parametric API or approval.",
            "Constructive sampling supports sides 17..30 and a bounded scene grammar.",
            "Only two transparent-color settings and the declared rivals are assessed.",
            "Identifiability is finite-rival agreement, not uniqueness among arbitrary programs.",
        ],
    }


def public_challenge(episode):
    """Whitelist public data; never copy metadata or held-out outputs."""
    return {"train": [{"input": copy.deepcopy(pair["input"]),
                        "output": copy.deepcopy(pair["output"])} for pair in episode["train"]],
            "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]]}


def write_episode(episode, destination, *, command=None):
    """Write a new evidence directory with exact text and artifact hashes."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    payloads = {
        "challenge.json": json.dumps(public_challenge(episode), indent=2) + "\n",
        "episode.private.json": json.dumps(episode, indent=2, sort_keys=True) + "\n",
        "rule.rkt": episode["rule_source"],
        "identifiability.json": json.dumps(episode["identifiability"], indent=2, sort_keys=True) + "\n",
    }
    payloads.update({f"rivals/{name}.rkt": source
                     for name, source in episode["declared_programs"].items()})
    for relative, text in payloads.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = {
        "schema": "arc-parametric-beam-evidence-v1", "status": "proposed prototype",
        "command": command or shlex.join([sys.executable, *sys.argv]),
        "source_sha256": episode["source_sha256"],
        "files_sha256": {name: _sha(text) for name, text in payloads.items()},
        "counts": {"demos": len(episode["train"]), "queries": len(episode["test"])},
        "all_query_inputs_identified_from_demonstrations": episode["identifiability"]["identified"],
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--transparent-color", choices=("2", "3", "sampled"), default="2")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--height", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--max-attempts", type=int, default=256)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        color = None if args.transparent_color == "sampled" else int(args.transparent_color)
        episode = generate_episode(seed=args.seed, transparent_color=color,
                                   demo_count=args.demos, query_count=args.queries,
                                   height=args.height, width=args.width, max_attempts=args.max_attempts)
        write_episode(episode, args.out)
    except (ValueError, RuntimeError, FileExistsError) as exc:
        parser.exit(2, f"prototype: {exc}\n")
    print(json.dumps({"status": "proposed prototype", "out": str(args.out),
                      "demos": len(episode["train"]), "queries": len(episode["test"]),
                      "rule_sha256": episode["rule_sha256"],
                      "identified": episode["identifiability"]["identified"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

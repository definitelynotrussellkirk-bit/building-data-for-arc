"""Proposed, task-local largest-rectangle rendering variants. Not approved."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys


TASK_ID = "061566027b67"
ROOT = Path(__file__).resolve().parents[4]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import (load_selected_generator, public_challenge_bytes,
                              public_challenge_id)


@dataclass(frozen=True)
class Parameters:
    shape_mode: str = "solid"
    paint_color: int | None = None

    def __post_init__(self):
        if type(self.shape_mode) is not str or self.shape_mode not in ("solid", "outline"):
            raise ValueError("shape_mode must be 'solid' or 'outline'")
        if self.paint_color is not None and (
            type(self.paint_color) is not int or not 1 <= self.paint_color <= 9
        ):
            raise ValueError("paint_color must be None or an exact integer 1..9")


SETTINGS = tuple(Parameters(shape, color)
                 for shape in ("solid", "outline")
                 for color in (None, *range(1, 10)))
_AUTHORITY = ROOT / "shared/data/base/solutions/training/91714a58__061566027b67.json"


def _params(params):
    if type(params) is not Parameters:
        raise ValueError("params must be Parameters")
    return params


@lru_cache(maxsize=1)
def _source():
    return load_selected_generator(TASK_ID, root=ROOT)


def canonical_program() -> str:
    """Return the authority's preserved executable source, byte-for-byte."""
    return json.loads(_AUTHORITY.read_text())["racket_target"]["target_code"]


def materialize_program(params: Parameters) -> str:
    """Change only the canonical rectangle's final rendering predicate/color."""
    _params(params)
    original = canonical_program()
    if params == Parameters():
        return original
    old = "((and (>= r br1) (<= r br2) (>= c bc1) (<= c bc2)) clr)"
    inside = "(and (>= r br1) (<= r br2) (>= c bc1) (<= c bc2))"
    if params.shape_mode == "outline":
        inside = ("(and " + inside +
                  " (or (= r br1) (= r br2) (= c bc1) (= c bc2)))")
    color = "clr" if params.paint_color is None else str(params.paint_color)
    if original.count(old) != 1:
        raise RuntimeError("canonical renderer changed; refusing an unreviewed mutation")
    return original.replace(old, f"({inside} {color})")


def _grid(grid, *, source=False):
    if type(grid) is not list or len(grid) != 16 or any(
        type(row) is not list or len(row) != 16 or any(
            type(cell) is not int or not 0 <= cell <= 9 for cell in row
        ) for row in grid
    ):
        raise ValueError("grid must be a 16x16 list of lists of exact integer colors 0..9")
    if source:
        errors = _source()[0].self_check(grid)
        if errors:
            raise ValueError("outside original source domain: " + "; ".join(errors))
    return grid


def solve_python(grid, params: Parameters):
    """Strict-domain mirror; executable Racket remains the labeling authority."""
    _params(params)
    _grid(grid, source=True)
    rectangle = _source()[0]._best_rect(grid)
    _area, top, left, bottom, right, source_color = rectangle
    color = source_color if params.paint_color is None else params.paint_color
    return [[color if (top <= row <= bottom and left <= col <= right and
                       (params.shape_mode == "solid" or row in (top, bottom)
                        or col in (left, right))) else 0
             for col in range(16)] for row in range(16)]


def _exact_int(value, name, lower=None, upper=None):
    if type(value) is not int or (lower is not None and value < lower) or (
        upper is not None and value > upper
    ):
        span = "" if lower is None else f" in {lower}..{upper}"
        raise ValueError(f"{name} must be an exact integer{span}")


def _sexpr_grid(grid):
    return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _racket_outputs(inputs, program, bridge):
    # The source has one known rule! wrapper. Applying its lambda directly
    # keeps the persistent bridge free of mutable rule-registration state.
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected one canonical rule! wrapper")
    fn = program[len("(rule! "):-1]
    grids = "(" + " ".join(_sexpr_grid(grid) for grid in inputs) + ")"
    outputs = bridge.eval_text(f"(map {fn} '{grids})")
    if type(outputs) is not list or len(outputs) != len(inputs):
        raise RuntimeError("Racket returned an unexpected label count")
    for output in outputs:
        _grid(output)
    return outputs


def _certificate(train, query_inputs, params):
    survivors = []
    for candidate in SETTINGS:
        if all(solve_python(pair["input"], candidate) == pair["output"] for pair in train):
            survivors.append(candidate)
    if params not in survivors:
        raise ValueError("demonstrations do not match the selected parameters")
    per_query = []
    for index, grid in enumerate(query_inputs):
        target = solve_python(grid, params)
        rivals = [asdict(candidate) for candidate in survivors
                  if candidate != params and solve_python(grid, candidate) != target]
        per_query.append({"index": index, "identified": not rivals,
                          "surviving_rivals": rivals})
    return {"method": "demonstration-only exhaustive finite-domain elimination",
            "query_labels_used": False, "alternatives": [asdict(p) for p in SETTINGS],
            "survivors": [asdict(p) for p in survivors], "per_query": per_query}


def demo_certificate(train, query_inputs, params: Parameters):
    """Eliminate hypotheses using demos only; query inputs assess agreement."""
    _params(params)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("train and query_inputs must be nonempty lists")
    for pair in train:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("demonstrations need input and output")
        _grid(pair["input"], source=True)
        _grid(pair["output"])
    for grid in query_inputs:
        _grid(grid, source=True)
    return _certificate(train, query_inputs, params)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_hashes():
    import reviewer_support
    from arc_repl import racket_bridge
    return {"prototype": _sha(__file__), "selected_generator": _source()[2],
            "canonical_authority": _sha(_AUTHORITY),
            "reviewer_support": _sha(reviewer_support.__file__),
            "racket_bridge": _sha(racket_bridge.__file__)}


def _build_episode(seed, params, train_count, test_count, bridge):
    _exact_int(seed, "seed")
    _params(params)
    _exact_int(train_count, "train_count", 2, 16)
    _exact_int(test_count, "test_count", 1, 16)
    generator = _source()[0]
    rng = random.Random(seed)
    first_color = rng.randint(1, 9)
    second_color = rng.choice([c for c in range(1, 10) if c != first_color])
    profiles = generator.RECTANGLE_PROFILES
    demo_profiles = ["3x3_tab", "3x4_tab"] + [profiles[i % 4] for i in range(train_count - 2)]
    query_profiles = [profiles[i % 4] for i in range(test_count)]
    inputs, seen = [], set()
    for index, profile in enumerate(demo_profiles + query_profiles):
        color = (first_color, second_color)[index] if index < 2 else rng.randint(1, 9)
        for attempt in range(64):
            grid = generator.generate(seed, index * 64 + attempt,
                                      rectangle_profile=profile, winner_color=color)
            _grid(grid, source=True)
            key = tuple(map(tuple, grid))
            if key not in seen:
                seen.add(key)
                inputs.append(grid)
                break
        else:
            raise RuntimeError("bounded distinct-input retry budget exhausted")
    program = materialize_program(params)
    outputs = _racket_outputs(inputs, program, bridge)
    for grid, output in zip(inputs, outputs):
        if output != solve_python(grid, params):
            raise RuntimeError("Racket/Python label disagreement")
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs)]
    train, test = pairs[:train_count], pairs[train_count:]
    certificate = demo_certificate(train, [p["input"] for p in test], params)
    if not all(q["identified"] for q in certificate["per_query"]):
        raise RuntimeError("demonstrations leave a query behavior ambiguous")
    return {"status": "proposed_unapproved_prototype", "seed": seed,
            "parameters": asdict(params), "train": train, "test": test,
            "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "source_hashes": _source_hashes(), "certificate": certificate,
            "label_validation": {"backend": "racket", "checked_pairs": len(pairs),
                                 "python_agreement": True},
            "runtime_identity": bridge.runtime_identity}


def build_episode(seed, params: Parameters = Parameters(), *, train_count=3, test_count=4):
    """Construct an episode; fail loudly if runtime, counts, or retries fail."""
    _exact_int(seed, "seed")
    _params(params)
    _exact_int(train_count, "train_count", 2, 16)
    _exact_int(test_count, "test_count", 1, 16)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=60.0) as bridge:
        return _build_episode(seed, params, train_count, test_count, bridge)


def write_batch(episodes, out_dir):
    """Export exact shared-helper public bytes; keep all authoring data private."""
    if type(episodes) not in (list, tuple) or not episodes:
        raise ValueError("episodes must be a nonempty list or tuple")
    out = Path(out_dir)
    if out.exists():
        raise FileExistsError("out_dir must be new")
    prepared, seen = [], set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if identifier in seen:
            raise ValueError("duplicate visible public payload")
        seen.add(identifier)
        # Serialize private metadata before creating any output directories.
        private = (json.dumps(episode, sort_keys=True, indent=2) + "\n").encode()
        prepared.append((identifier, payload, private))
    prepared.sort(key=lambda entry: entry[0])
    manifest = {"schema": "rectangle-modes-public-batch-v1",
                "status": "proposed_unapproved_prototype",
                "public": [{"id": identifier, "path": f"public/{identifier}.json"}
                           for identifier, _payload, _private in prepared]}
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    for identifier, payload, private in prepared:
        (out / "public" / f"{identifier}.json").write_bytes(payload)
        (out / "private" / f"{identifier}.json").write_bytes(private)
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train", type=int, default=3)
    parser.add_argument("--test", type=int, default=4)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--shape-mode", choices=("solid", "outline"), default="solid")
    parser.add_argument("--paint-color", choices=("source", *map(str, range(1, 10))), default="source")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    _exact_int(args.train, "train_count", 2, 16)
    _exact_int(args.test, "test_count", 1, 16)
    settings = SETTINGS if args.all_settings else (
        Parameters(args.shape_mode, None if args.paint_color == "source" else int(args.paint_color)),)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=60.0) as bridge:
        episodes = [_build_episode(args.seed, p, args.train, args.test, bridge) for p in settings]
    manifest = write_batch(episodes, args.out)
    print(json.dumps({"episodes": len(episodes), "pairs_checked": len(episodes) * (args.train + args.test),
                      "public_ids": [entry["id"] for entry in manifest["public"]],
                      "status": "proposed_unapproved_prototype"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

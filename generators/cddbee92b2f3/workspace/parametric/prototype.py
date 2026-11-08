"""Proposed source-side family for cddbee92b2f3; never canonical authority.

A full-height color-5 guide is visible in every scene.  The episode-fixed
``source_side`` rule chooses whether colored cells on the guide's left or right
are copied across it.  The same inputs are used for both settings.  Evidence
exports re-execute all labels with the packet's protected Racket runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "cddbee92b2f3"
DEFAULT = {"source_side": "left"}
PARAMETERS = {"source_side": ["left", "right"]}
SETTINGS = [{"source_side": side} for side in PARAMETERS["source_side"]]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule!
  (let ((guides (filter (lambda (c) (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g)))) (range 0 (cols g)))))
    (if (empty? guides)
        g
        (let ((gc (first guides)))
          (for*/fold ([out g]) ([r (in-range (rows g))] [c (in-range gc)])
            (let ((v (at g r c))
                  (mc (- (* 2 gc) c)))
              (if (and (not (= v 0)) (not (= v 5)) (in-bounds? r mc (rows g) (cols g)))
                  (set-cell out r mc v)
                  out)))))))'''

_RIGHT = '''(rule!
  (let ((guides (filter (lambda (c) (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g)))) (range 0 (cols g)))))
    (if (empty? guides)
        g
        (let ((gc (first guides)))
          (for*/fold ([out g]) ([r (in-range (rows g))] [c (in-range (+ gc 1) (cols g))])
            (let ((v (at g r c))
                  (mc (- (* 2 gc) c)))
              (if (and (not (= v 0)) (not (= v 5)) (in-bounds? r mc (rows g) (cols g)))
                  (set-cell out r mc v)
                  out)))))))'''

_DEMO_SHAPES = ((8, 11), (9, 13), (10, 15), (12, 17), (14, 19), (16, 21))
_QUERY_SHAPES = ((12, 15), (16, 20), (24, 27), (30, 30))
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"source_side"}:
        raise ValueError("settings must name exactly source_side")
    side = settings["source_side"]
    if type(side) is not str or side not in PARAMETERS["source_side"]:
        raise ValueError("source_side must be 'left' or 'right'")
    return {"source_side": side}


def _color_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _grid(grid: Any) -> list[list[int]]:
    value = _color_grid(grid)
    if len(value) < 2 or len(value[0]) < 5:
        raise ValueError("source-side inputs must be at least 2 by 5")
    return value


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return _CANONICAL if chosen["source_side"] == "left" else _RIGHT


def _guide(grid: list[list[int]]) -> int | None:
    width = len(grid[0])
    guides = [c for c in range(width) if all(row[c] == 5 for row in grid)]
    return guides[0] if guides else None


def _copy_side(grid: list[list[int]], side: str, *, clear_sources: bool = False) -> list[list[int]]:
    guide = _guide(grid)
    output = [list(row) for row in grid]
    if guide is None:
        return output
    columns = range(guide) if side == "left" else range(guide + 1, len(grid[0]))
    for r, row in enumerate(grid):
        for c in columns:
            value = row[c]
            mirror = 2 * guide - c
            if value not in (0, 5) and 0 <= mirror < len(row):
                output[r][mirror] = value
                if clear_sources:
                    output[r][c] = 0
    return output


def transform(grid: Any, settings: Any) -> list[list[int]]:
    """Python semantic mirror; retained evidence uses Racket as authority."""
    value = _grid(grid)
    side = _settings(settings)["source_side"]
    return _copy_side(value, side)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    token = _digest([TASK_ID, "source-side-v1", seed, domain, index])
    return random.Random(int(token, 16))


def _scene(seed: int, index: int, *, query_slot: int | None = None) -> list[list[int]]:
    rng = _rng(seed, "query" if query_slot is not None else "demo", index)
    if query_slot is None:
        height, width = _DEMO_SHAPES[index % len(_DEMO_SHAPES)]
    else:
        height, width = _QUERY_SHAPES[query_slot]

    # Keep at least three usable columns on each side.  On alternating scenes
    # the guide is off-center, exercising clipping for the wider side.
    center = width // 2
    guide = max(3, min(width - 4, center + (-1 if index % 2 else 0)))
    grid = [[0] * width for _ in range(height)]
    for row in grid:
        row[guide] = 5

    # A later full-height guide verifies that the first guide is authoritative.
    second = min(width - 1, guide + 4)
    if second > guide + 2:
        for row in grid:
            row[second] = 5

    # Conflicting mirror-pair colors make left and right settings distinguishable
    # in every demonstration while preserving identical visible inputs.
    r1 = 1 + (index * 2 + rng.randrange(height - 1)) % (height - 1)
    r2 = 1 + (index * 3 + rng.randrange(height - 1)) % (height - 1)
    if r2 == r1:
        r2 = 1 + (r2 % (height - 1))
    grid[r1][guide - 2] = 2
    grid[r1][guide + 2] = 7
    grid[r2][guide - 1] = 3
    grid[r2][guide + 1] = 8

    # Sparse side-neutral clutter, including occupied mirror targets, literal 5
    # sources that must be filtered, and possible off-canvas mirrors.
    candidates = [
        c for c in range(width)
        if c not in {guide, second}
    ]
    for r in range(height):
        for _ in range(1 + (r + index) % 3):
            c = rng.choice(candidates)
            grid[r][c] = rng.choice(_COLORS)
    literal_row = (r1 + 2) % height
    literal_col = guide - 3 if guide >= 3 else guide + 3
    if literal_col != second:
        grid[literal_row][literal_col] = 5

    # Restore the guaranteed discriminating cells after clutter.
    grid[r1][guide - 2] = 2
    grid[r1][guide + 2] = 7
    grid[r2][guide - 1] = 3
    grid[r2][guide + 1] = 8
    for row in grid:
        row[guide] = 5
        if second > guide + 2:
            row[second] = 5
    return grid


def _apply_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for setting in SETTINGS:
        if program(setting) == source:
            return transform(grid, setting)
    raise ValueError("unknown source-side program")


def _mirror_both(grid: list[list[int]]) -> list[list[int]]:
    left = _copy_side(grid, "left")
    right = _copy_side(grid, "right")
    guide = _guide(grid)
    if guide is None:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if c < guide:
                output[r][c] = right[r][c]
            elif c > guide:
                output[r][c] = left[r][c]
    return output


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must be exactly four")

    all_pairs = train + test
    inputs: set[str] = set()
    for pair in all_pairs:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each private pair must contain exactly input and output")
        grid = _grid(pair["input"])
        output = _color_grid(pair["output"])
        if len(output) != len(grid) or len(output[0]) != len(grid[0]):
            raise ValueError("source-side output must preserve grid dimensions")
        key = _digest(grid)
        if key in inputs:
            raise ValueError("all demonstration and query inputs must be distinct")
        inputs.add(key)

    apply = execute or _apply_python
    records = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        records.append(
            {
                "settings": dict(setting),
                "disagreeing_demo_indices": [
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, train))
                    if prediction != pair["output"]
                ],
            }
        )
    survivors = [row["settings"] for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the chosen setting: {survivors}")

    shortcut_refutations = {
        "mirror_both_sides": any(_mirror_both(pair["input"]) != pair["output"] for pair in train),
        "move_instead_of_copy": any(
            _copy_side(pair["input"], chosen["source_side"], clear_sources=True) != pair["output"]
            for pair in train
        ),
    }
    if not all(shortcut_refutations.values()):
        raise ValueError(f"demonstrations leave a declared shortcut alive: {shortcut_refutations}")

    for pair in all_pairs:
        if apply(program(chosen), pair["input"]) != pair["output"]:
            raise ValueError("retained label disagrees with selected rule")
    queries = [
        {
            "input_sha256": _digest(pair["input"]),
            "output_sha256": _digest(pair["output"]),
            "survivors": survivors,
            "unanimous": True,
        }
        for pair in test
    ]
    return {
        "scope": "two declared source-side rules plus two explicit shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": records,
        "shortcut_refutations": shortcut_refutations,
        "queries": queries,
    }


def generate(
    seed: int,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(_rng(seed, "settings").choice(SETTINGS) if settings is None else settings)

    train = []
    for index in range(demos):
        grid = _scene(seed, index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for slot in range(4):
        grid = _scene(seed, 10_000 + slot, query_slot=slot)
        test.append({"input": grid, "output": transform(grid, chosen)})

    episode = {
        "schema": "cdd-source-side-parametric-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


class RacketRunner:
    """One live protected bridge for a bounded evidence batch."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE.parents[1] / "generator.py",
        REPO / "shared/runtime/reviewer_support.py",
        REPO / "shared/runtime/arc_repl/racket_bridge.py",
        REPO / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        REPO / "shared/runtime/puzzle_generators/rule_wrap.py",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
        if path.is_file()
    }


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    """Model-visible one-query turn; never includes future inputs or count hints."""
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be the exact integer 0..3")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must contain demonstrations and exactly four controller queries")
    return public_challenge_bytes({"train": train, "test": [test[query_index]]})


def write_batch(episodes: list[dict[str, Any]], destination: Path, *, metadata=None) -> dict[str, Any]:
    destination = Path(destination)
    rows = []
    for episode in episodes:
        controller_body = public_challenge_bytes(episode)
        controller_id = hashlib.sha256(controller_body).hexdigest()
        turns = []
        for query_index in range(4):
            body = public_turn_bytes(episode, query_index)
            turns.append((hashlib.sha256(body).hexdigest(), body))
        rows.append((controller_id, controller_body, turns, episode))
    rows.sort(key=lambda row: row[0])
    controller_ids = [row[0] for row in rows]
    turn_ids = [identifier for _, _, turns, _ in rows for identifier, _ in turns]
    if not rows or len(set(controller_ids)) != len(controller_ids):
        raise ValueError("batch must be nonempty with distinct controller challenges")
    if len(set(turn_ids)) != len(turn_ids):
        raise ValueError("all model-visible turns must have distinct public bytes")
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public = destination / "public"
    controller = destination / "controller"
    public.mkdir()
    controller.mkdir()
    episode_index = []
    private_episodes = []
    for controller_id, controller_body, turns, episode in rows:
        controller_path = controller / f"{controller_id}.json"
        controller_path.write_bytes(controller_body)
        ordered_turn_ids = []
        for identifier, body in turns:
            (public / f"{identifier}.json").write_bytes(body)
            ordered_turn_ids.append(identifier)
        episode_index.append({
            "controller": str(controller_path.relative_to(destination)),
            "turn_ids": ordered_turn_ids,
        })
        private_episodes.append(dict(
            episode,
            controller_id=controller_id,
            turn_ids=ordered_turn_ids,
        ))
    private = {
        "schema": "cdd-source-side-evidence-v1",
        "status": "prototype_proposed",
        "source_sha256": source_hashes(),
        "metadata": metadata or {},
        "episodes": private_episodes,
    }
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n"
    )
    files = [
        destination / "private.json",
        *sorted(public.iterdir()),
        *sorted(controller.iterdir()),
    ]
    manifest = {
        "schema": "cdd-source-side-export-v2",
        "public_ids": turn_ids,
        "episodes": episode_index,
        "public_usage": "Serve only the next public/ file selected by controller/private state.",
        "controller_usage": "controller/ holds all four future inputs; it is not a model prompt.",
        "manifest_usage": "Controller metadata only; never place manifest.json in model context.",
        "writer_executes_racket": False,
        "files": {
            str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--source-side", choices=PARAMETERS["source_side"], default="left")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"source_side": args.source_side}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        manifest = write_batch(
            episodes,
            args.out,
            metadata={
                "payload_argv": sys.argv,
                "runtime_identity": execute.identity,
                "qualification": "not_run",
                "acceptance": "not_requested",
                "training_admitted": False,
            },
        )
    print(
        json.dumps(
            {
                "status": "prototype_proposed",
                "episodes": len(episodes),
                "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                "public_ids": manifest["public_ids"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

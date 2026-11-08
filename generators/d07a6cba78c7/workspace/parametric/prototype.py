"""Proposed marker-side family for d07a6cba78c7; never canonical authority.

The visible grammar places one magenta marker on each horizontal border in
*different* rows.  The episode-fixed rule chooses whether the left or right
marker selects the payload row.  Generated evidence re-executes retained labels
through protected Racket; ``generate`` alone returns deterministic Python claims.
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
TASK_ID = "d07a6cba78c7"
DEFAULT = {"marker_side": "left"}
PARAMETERS = {"marker_side": ["left", "right"]}
SETTINGS = [{"marker_side": side} for side in PARAMETERS["marker_side"]]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule!
 ;; Output the single row whose LEADING cell is magenta(6), marker dropped.
 (let ((r (first (filter (lambda (rr) (= (at g rr 0) 6)) (range 0 h)))))
   (list (for/list ((c (in-range 1 w))) (at g r c)))))'''

_RIGHT = '''(rule!
 ;; Output the single row whose TRAILING cell is magenta(6), marker dropped.
 (let ((r (first (filter (lambda (rr) (= (at g rr (- w 1)) 6)) (range 0 h)))))
   (list (for/list ((c (in-range 0 (- w 1)))) (at g r c)))))'''

_QUERY_SHAPES = ((9, 11), (13, 17), (20, 24), (30, 30))
_DEMO_SHAPES = ((6, 8), (7, 9), (8, 10), (9, 12), (10, 14), (12, 16))
_COLORS = (1, 2, 3, 4, 5, 7, 8, 9)


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"marker_side"}:
        raise ValueError("settings must name exactly marker_side")
    side = settings["marker_side"]
    if type(side) is not str or side not in PARAMETERS["marker_side"]:
        raise ValueError("marker_side must be 'left' or 'right'")
    return {"marker_side": side}


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
    if len(value) < 2 or len(value[0]) < 3:
        raise ValueError("marker-side inputs must be at least 2 by 3")
    return value


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return _CANONICAL if chosen["marker_side"] == "left" else _RIGHT


def transform(grid: Any, settings: Any) -> list[list[int]]:
    """Python semantic mirror; retained evidence uses Racket as authority."""
    value = _grid(grid)
    side = _settings(settings)["marker_side"]
    col = 0 if side == "left" else len(value[0]) - 1
    rows = [r for r, row in enumerate(value) if row[col] == 6]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one magenta marker on the {side} border")
    selected = rows[0]
    output = value[selected][1:] if side == "left" else value[selected][:-1]
    return [list(output)]


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(_digest([TASK_ID, "marker-side-v1", seed, domain, index]), 16))


def _scene(seed: int, index: int, *, query_slot: int | None = None) -> list[list[int]]:
    rng = _rng(seed, "query" if query_slot is not None else "demo", index)
    if query_slot is None:
        height, width = _DEMO_SHAPES[index % len(_DEMO_SHAPES)]
    else:
        height, width = _QUERY_SHAPES[query_slot]
    interior = width - 2
    density = min(interior, max(3, min(7, interior // 3 + 2)))

    # Keep row zero as an equal-density distractor so fixed-first/densest rules
    # are visibly wrong.  Both real markers stay off row zero and never coincide.
    left_row = 1 + ((index * 2 + rng.randrange(height - 1)) % (height - 1))
    right_row = 1 + ((index * 3 + rng.randrange(height - 1)) % (height - 1))
    if right_row == left_row:
        right_row = 1 + (right_row % (height - 1))

    grid = [[0] * width for _ in range(height)]
    seen_payloads: set[tuple[int, ...]] = set()
    for row in range(height):
        for _ in range(128):
            payload = [0] * interior
            positions = rng.sample(range(interior), density)
            palette = rng.sample(_COLORS, min(4, len(_COLORS)))
            for offset, col in enumerate(positions):
                payload[col] = palette[(offset + row) % len(palette)]
            key = tuple(payload)
            if key not in seen_payloads:
                seen_payloads.add(key)
                grid[row][1:-1] = payload
                break
        else:
            raise RuntimeError("could not construct distinct equal-density rows")
    grid[left_row][0] = 6
    grid[right_row][-1] = 6
    return grid


def _apply_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for setting in SETTINGS:
        if program(setting) == source:
            return transform(grid, setting)
    raise ValueError("unknown marker-side program")


def _first_row_rival(grid: list[list[int]], chosen: dict[str, str]) -> list[list[int]]:
    return [list(grid[0][1:] if chosen["marker_side"] == "left" else grid[0][:-1])]


def _interior_only_rival(grid: list[list[int]], chosen: dict[str, str]) -> list[list[int]]:
    side = chosen["marker_side"]
    col = 0 if side == "left" else len(grid[0]) - 1
    row = next(r for r, values in enumerate(grid) if values[col] == 6)
    return [list(grid[row][1:-1])]


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
        if len(output) != 1 or len(output[0]) != len(grid[0]) - 1:
            raise ValueError("marker-side output must be one cropped row")
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

    rival_refutations = {
        "fixed_first_row": any(
            _first_row_rival(pair["input"], chosen) != pair["output"] for pair in train
        ),
        "drop_both_borders": any(
            _interior_only_rival(pair["input"], chosen) != pair["output"] for pair in train
        ),
    }
    if not all(rival_refutations.values()):
        raise ValueError(f"demonstrations leave a declared shortcut alive: {rival_refutations}")

    query_records = []
    for pair in all_pairs:
        prediction = apply(program(chosen), pair["input"])
        if prediction != pair["output"]:
            raise ValueError("retained label disagrees with selected rule")
    for pair in test:
        query_records.append(
            {
                "input_sha256": _digest(pair["input"]),
                "output_sha256": _digest(pair["output"]),
                "survivors": survivors,
                "unanimous": True,
            }
        )
    return {
        "scope": "two declared marker-side rules plus two explicit shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": records,
        "shortcut_refutations": rival_refutations,
        "queries": query_records,
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
        "schema": "d07-marker-side-parametric-proposal-v1",
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
        "schema": "d07-marker-side-evidence-v1",
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
        "schema": "d07-marker-side-export-v2",
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
    parser.add_argument("--marker-side", choices=PARAMETERS["marker_side"], default="left")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"marker_side": args.marker_side}]
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

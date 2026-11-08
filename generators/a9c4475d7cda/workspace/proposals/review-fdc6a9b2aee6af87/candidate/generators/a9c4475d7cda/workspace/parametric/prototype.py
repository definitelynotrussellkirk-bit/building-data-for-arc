#!/usr/bin/env python3
"""Task-local threshold parameter prototype for ARC task a9c4475d7cda."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAMS = HERE / "programs"
THRESHOLDS = (1, 2, 3)
DEFAULT_THRESHOLD = 2


def _threshold(value) -> int:
    if type(value) is not int or value not in THRESHOLDS:
        raise ValueError(f"threshold must be one of {THRESHOLDS} as an exact integer")
    return value


def rule_text(threshold: int) -> str:
    """Return the exact materialized Racket program for ``threshold``."""
    value = _threshold(threshold)
    path = PROGRAMS / f"threshold-{value}.rkt"
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"empty Racket program: {path}")
    return text


def _panel_counts(grid) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(cell) is not int for row in grid for cell in row):
        raise ValueError("grid colors must be exact integers")
    height = len(grid)
    separator_rows = [
        row for row in range(height) if all(value == 8 for value in grid[row])
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(separator_rows) != 2 or len(separator_cols) != 2:
        raise ValueError("expected exactly two full divider rows and columns")
    row_bands = (
        (0, separator_rows[0]),
        (separator_rows[0] + 1, separator_rows[1]),
        (separator_rows[1] + 1, height),
    )
    col_bands = (
        (0, separator_cols[0]),
        (separator_cols[0] + 1, separator_cols[1]),
        (separator_cols[1] + 1, width),
    )
    return [
        [
            sum(
                grid[row][col] == 6
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]


def apply_python(grid, threshold: int) -> list[list[int]]:
    """Independent Python claim used by the prototype; Racket verifies evidence."""
    value = _threshold(threshold)
    return [
        [int(count >= value) for count in row]
        for row in _panel_counts(grid)
    ]


# Every profile below contains panel counts 0, 1, 2, and 3, so one
# demonstration distinguishes every declared threshold setting.
_EPISODE_PROFILES = ("balanced", "sparse", "dense")
MAX_DEMOS = 16
MAX_QUERIES = 16
DEFAULT_MAX_ATTEMPTS = 256
MAX_ATTEMPTS = 4096
TASK_ID = "a9c4475d7cda"
ROOT = HERE.parents[3]


def _bounded_int(value, *, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def choose_threshold(seed: int) -> int:
    """Choose one hidden threshold deterministically, once per episode."""
    import hashlib

    value = _bounded_int(seed, name="seed", low=0, high=2**63 - 1)
    digest = hashlib.sha256(
        f"{TASK_ID}:threshold-choice-v1:{value}".encode("ascii")
    ).digest()
    return THRESHOLDS[int.from_bytes(digest[:2], "big") % len(THRESHOLDS)]


def _selected_generator():
    from functools import lru_cache
    from reviewer_support import load_selected_generator

    @lru_cache(maxsize=1)
    def load():
        module, _path, _digest = load_selected_generator(TASK_ID, root=ROOT)
        return module

    # Defining the cache inside this function would recreate it, so retain it on
    # the function object while keeping imports local for copied-runtime use.
    cached = getattr(_selected_generator, "_cached", None)
    if cached is None:
        cached = load()
        _selected_generator._cached = cached
    return cached


def _input_spec(seed: int, attempt: int) -> tuple[int, int, int, str, str]:
    """Return deterministic generation controls independent of threshold."""
    import hashlib

    digest = hashlib.sha256(
        f"{TASK_ID}:threshold-input-v1:{seed}:{attempt}".encode("ascii")
    ).digest()
    sample_index = int.from_bytes(digest[:8], "big")
    height = 9 + digest[8] % 9
    width = 9 + digest[9] % 9
    profile = _EPISODE_PROFILES[digest[10] % len(_EPISODE_PROFILES)]
    difficulty = ("easy", "medium", "hard")[digest[11] % 3]
    return sample_index, height, width, profile, difficulty


def _grid_key(grid) -> str:
    import json

    return json.dumps(grid, sort_keys=False, separators=(",", ":"))


def surviving_thresholds(train) -> list[int]:
    """Fit declared threshold settings using demonstration pairs only."""
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty list of demonstration pairs")
    survivors = []
    for threshold in THRESHOLDS:
        try:
            matches = all(
                type(pair) is dict
                and apply_python(pair["input"], threshold) == pair["output"]
                for pair in train
            )
        except (KeyError, TypeError, ValueError):
            matches = False
        if matches:
            survivors.append(threshold)
    return survivors


def generate_episode(
    seed: int,
    threshold="auto",
    demos: int = 3,
    queries: int = 4,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
):
    """Generate one fixed-threshold supervised episode with distinct inputs."""
    seed = _bounded_int(seed, name="seed", low=0, high=2**63 - 1)
    demos = _bounded_int(demos, name="demos", low=1, high=MAX_DEMOS)
    queries = _bounded_int(queries, name="queries", low=1, high=MAX_QUERIES)
    max_attempts = _bounded_int(
        max_attempts, name="max_attempts", low=1, high=MAX_ATTEMPTS
    )
    if threshold == "auto":
        selected = choose_threshold(seed)
    else:
        selected = _threshold(threshold)

    generator = _selected_generator()
    needed = demos + queries
    pairs = []
    seen = set()
    accepted = []
    for attempt in range(max_attempts):
        sample_index, height, width, profile, difficulty = _input_spec(seed, attempt)
        grid = generator.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            grid_h=height,
            grid_w=width,
            count_profile=profile,
        )
        key = _grid_key(grid)
        if key in seen:
            continue
        seen.add(key)
        pairs.append({"input": grid, "output": apply_python(grid, selected)})
        accepted.append(
            {
                "attempt": attempt,
                "sample_index": sample_index,
                "grid_h": height,
                "grid_w": width,
                "count_profile": profile,
                "difficulty": difficulty,
            }
        )
        if len(pairs) == needed:
            break
    if len(pairs) != needed:
        raise RuntimeError(
            f"could not obtain {needed} distinct inputs in {max_attempts} attempts; "
            f"obtained {len(pairs)}"
        )
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "threshold": selected,
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": rule_text(selected),
        "accepted_inputs": accepted,
    }
    survivors = surviving_thresholds(episode["train"])
    if survivors != [selected]:
        raise RuntimeError(
            f"demonstrations do not identify threshold {selected}; survivors={survivors}"
        )
    return episode


def public_payload(episode) -> dict:
    """Return exactly the model-visible demonstration and query content."""
    import json
    from reviewer_support import public_challenge_bytes

    return json.loads(public_challenge_bytes(episode))


def public_id(episode) -> str:
    """Return a public identifier derived only from visible challenge bytes."""
    from reviewer_support import public_challenge_id

    return public_challenge_id(episode)


def _validate_episode(episode) -> int:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    selected = _threshold(episode.get("threshold"))
    if episode.get("program_solution") != rule_text(selected):
        raise ValueError("episode program does not match threshold")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode needs nonempty train and test lists")
    keys = []
    for pair in train + test:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("every episode pair needs input and output")
        if apply_python(pair["input"], selected) != pair["output"]:
            raise ValueError("episode label does not match threshold rule")
        keys.append(_grid_key(pair["input"]))
    if len(keys) != len(set(keys)):
        raise ValueError("episode inputs must be distinct")
    if surviving_thresholds(train) != [selected]:
        raise ValueError("demonstrations do not uniquely identify the threshold")
    return selected


def write_episodes(destination, episodes):
    """Write leakage-safe public files and separate private records atomically enough for review.

    All public payloads and identifiers are computed and checked before the output
    directory is created, so a duplicate visible challenge leaves no partial tree.
    """
    import hashlib
    import json
    from pathlib import Path
    from reviewer_support import public_challenge_bytes

    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")

    prepared = []
    for episode in episodes:
        selected = _validate_episode(episode)
        visible = public_challenge_bytes(episode)
        identifier = hashlib.sha256(visible).hexdigest()
        prepared.append((identifier, visible, selected, episode))
    identifiers = [row[0] for row in prepared]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate visible challenge payload")
    prepared.sort(key=lambda row: row[0])

    public_dir = destination / "public"
    private_dir = destination / "private"
    program_dir = private_dir / "programs"
    public_dir.mkdir(parents=True, exist_ok=False)
    program_dir.mkdir(parents=True, exist_ok=False)

    written = []
    manifest_rows = []
    for identifier, visible, selected, episode in prepared:
        public_path = public_dir / f"challenge-{identifier}.json"
        private_path = private_dir / f"episode-{identifier}.json"
        program_path = program_dir / f"program-{identifier}.rkt"
        public_path.write_bytes(visible)
        private_path.write_text(
            json.dumps(episode, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        program_path.write_text(rule_text(selected), encoding="utf-8")
        row = {
            "public_id": identifier,
            "public_path": str(public_path),
            "private_path": str(private_path),
            "program_path": str(program_path),
        }
        written.append(row)
        manifest_rows.append(
            {
                "public_id": identifier,
                "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
                "private_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
                "program_sha256": hashlib.sha256(program_path.read_bytes()).hexdigest(),
            }
        )
    (private_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "a9c4475d7cda-threshold-export-v1",
                "status": "proposed",
                "public_files_are_model_visible": True,
                "private_files_are_model_visible": False,
                "episodes": manifest_rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return written


class RacketEngine:
    """Small reusable protected-Racket evaluator with execution records."""

    def __init__(self):
        import hashlib
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        self._hashlib = hashlib
        self._wrap_rule = wrap_rule
        self._bridge = RacketBridge()
        identity = self._bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self._bridge.close()
            raise RuntimeError("prototype evidence requires protected Racket")
        self.runtime_identity = identity
        self._wrapped = {}
        self.executions = []

    def apply(self, grid, threshold: int):
        selected = _threshold(threshold)
        program = rule_text(selected)
        wrapped = self._wrapped.setdefault(program, self._wrap_rule(program))
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        output = self._bridge.eval_text(f"({wrapped} {literal})")
        self.executions.append(
            {
                "threshold": selected,
                "program_sha256": self._hashlib.sha256(program.encode()).hexdigest(),
                "input_sha256": self._hashlib.sha256(_grid_key(grid).encode()).hexdigest(),
                "output": output,
            }
        )
        return output

    def close(self):
        self._bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def verify_episode_racket(episode, *, engine=None) -> dict:
    """Re-execute labels and finite-rival teaching checks in protected Racket."""
    selected = _validate_episode(episode)
    own_engine = engine is None
    if own_engine:
        engine = RacketEngine()
    try:
        survivors = []
        demo_mismatches = {}
        for threshold in THRESHOLDS:
            mismatches = []
            for index, pair in enumerate(episode["train"]):
                if engine.apply(pair["input"], threshold) != pair["output"]:
                    mismatches.append(index)
            demo_mismatches[str(threshold)] = mismatches
            if not mismatches:
                survivors.append(threshold)
        if survivors != [selected]:
            raise ValueError(
                f"Racket demonstrations do not identify threshold {selected}; survivors={survivors}"
            )
        query_checks = []
        for index, pair in enumerate(episode["test"]):
            actual = engine.apply(pair["input"], selected)
            if actual != pair["output"]:
                raise ValueError(f"Racket query label mismatch at index {index}")
            query_checks.append({"index": index, "passed": True})
        return {
            "threshold": selected,
            "demo_survivors": survivors,
            "demo_mismatches": demo_mismatches,
            "query_checks": query_checks,
            "label_count": len(episode["train"]) + len(episode["test"]),
        }
    finally:
        if own_engine:
            engine.close()


def _cli(argv=None) -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--threshold", choices=("auto", "all", "1", "2", "3"), default="all")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.threshold == "all":
        settings = THRESHOLDS
    elif args.threshold == "auto":
        settings = (choose_threshold(args.seed),)
    else:
        settings = (int(args.threshold),)
    episodes = [
        generate_episode(
            args.seed,
            threshold=threshold,
            demos=args.demos,
            queries=args.queries,
            max_attempts=args.max_attempts,
        )
        for threshold in settings
    ]
    with RacketEngine() as engine:
        checks = [verify_episode_racket(episode, engine=engine) for episode in episodes]
        written = write_episodes(args.out, episodes)
        evidence = {
            "schema": "a9c4475d7cda-threshold-evidence-v1",
            "status": "proposed",
            "seed": args.seed,
            "demo_count": args.demos,
            "query_count": args.queries,
            "checks": checks,
            "written": written,
            "racket_runtime": engine.runtime_identity,
            "racket_execution_count": len(engine.executions),
            "racket_executions": engine.executions,
            "limits": [
                "Finite comparison among thresholds 1, 2, and 3 only.",
                "Task-local prototype; no production approval or training admission change.",
                "Inputs reuse the approved canonical generator grammar and its 9..17 size bounds.",
            ],
        }
    private = args.out / "private"
    (private / "verification.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "ok",
        "thresholds": list(settings),
        "demo_count": args.demos,
        "query_count": args.queries,
        "racket_execution_count": evidence["racket_execution_count"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

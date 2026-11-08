#!/usr/bin/env python3
"""Proposed task-local parametric rule family for ARC task 964b23808a3c.

The canonical generator and selected authority remain the production path.  This
prototype varies two small semantic choices while retaining the same reasoning
objects: detect marked columns, select columns using color 5, then fill the
vertical intervals delimited by ordered markers.

* ``selector_mode``: select columns that end in 5 (canonical) or contain 5.
* ``segment_mode``: assign each interval to its lower/current marker
  (canonical) or to the preceding marker.

One complete setting is chosen once per episode and held fixed for all three
labelled demonstrations and the unlabelled query.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import types
from typing import Any, NamedTuple

TASK_ID = "964b23808a3c"
PROTOTYPE_VERSION = "1.0.0"
SELECTOR_MODES = ("ends_in_5", "contains_5")
SEGMENT_MODES = ("current", "previous")

ROOT = Path(__file__).resolve().parents[4]
HOME = ROOT / "generators" / TASK_ID
GENERATOR_PATH = HOME / "generator.py"
RULE_DIR = Path(__file__).resolve().parent / "rules"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

CANONICAL_SELECTOR_REJECT = (
    "(!= (at g (nth marks (- (length marks) 1)) c) 5)"
)
CONTAINS_FIVE_REJECT = (
    "(empty? (filter (lambda (r) (= (at g r c) 5)) marks))"
)
CANONICAL_COLOR_BINDING = "(color (at g r c)))"
PREVIOUS_COLOR_BINDING = """(color (if (zero? i)
                                                       (at g r c)
                                                       (at g (nth marks (- i 1)) c)))
                                            (stop (if (zero? i)
                                                      (+ r 1)
                                                      r)))"""
CANONICAL_RANGE = "(range start (+ r 1))"
PREVIOUS_RANGE = "(range start stop)"

LIMITATIONS = [
    "Proposed task-local prototype only; it does not alter canonical labels, the selected rule hash, or production generator dispatch.",
    "The setting space is deliberately bounded to four nearby rules and does not establish uniqueness against undeclared hypotheses.",
    "Evidence uses one deterministic four-pair episode per setting; broader seed coverage would be required before training admission.",
    "The previous-marker variant preserves each current marker cell and colors only the open interval above it, matching the retained semantic rival.",
]


class RuleSetting(NamedTuple):
    selector_mode: str
    segment_mode: str

    def as_dict(self) -> dict[str, str]:
        return {
            "selector_mode": self.selector_mode,
            "segment_mode": self.segment_mode,
        }

    @property
    def slug(self) -> str:
        return f"{self.selector_mode}__{self.segment_mode}"


DEFAULT_SETTING = RuleSetting("ends_in_5", "current")
ALL_SETTINGS = tuple(
    RuleSetting(selector_mode, segment_mode)
    for selector_mode in SELECTOR_MODES
    for segment_mode in SEGMENT_MODES
)


def digest(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_setting(setting: RuleSetting) -> RuleSetting:
    if not isinstance(setting, RuleSetting):
        raise TypeError("setting must be a RuleSetting")
    if setting.selector_mode not in SELECTOR_MODES:
        raise ValueError(f"unsupported selector_mode: {setting.selector_mode!r}")
    if setting.segment_mode not in SEGMENT_MODES:
        raise ValueError(f"unsupported segment_mode: {setting.segment_mode!r}")
    return setting


def choose_setting(seed: int) -> RuleSetting:
    """Choose one hidden setting for an entire episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return ALL_SETTINGS[seed % len(ALL_SETTINGS)]


def canonical_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with CANONICAL_PATH.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if not rows:
        raise ValueError(f"no canonical row found for {TASK_ID}")
    programs = {row.get("program_solution") for row in rows}
    if None in programs or len(programs) != 1:
        raise ValueError("expected one exact selected program across canonical rows")
    return rows


def program(setting: RuleSetting = DEFAULT_SETTING) -> str:
    """Instantiate one exact Racket rule; default bytes equal the authority."""
    setting = _validate_setting(setting)
    source = canonical_rows()[0]["program_solution"]
    for fragment, expected_count in (
        (CANONICAL_SELECTOR_REJECT, 1),
        (CANONICAL_COLOR_BINDING, 1),
        (CANONICAL_RANGE, 1),
    ):
        if source.count(fragment) != expected_count:
            raise ValueError(
                f"canonical source edit anchor changed for {fragment!r}; explicit review required"
            )
    if setting.selector_mode == "contains_5":
        source = source.replace(
            CANONICAL_SELECTOR_REJECT, CONTAINS_FIVE_REJECT, 1
        )
    if setting.segment_mode == "previous":
        source = source.replace(
            CANONICAL_COLOR_BINDING, PREVIOUS_COLOR_BINDING, 1
        ).replace(CANONICAL_RANGE, PREVIOUS_RANGE, 1)
    return source


def generator():
    spec = importlib.util.spec_from_file_location(
        f"parametric_parent_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load parent generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        raise ValueError("grid must be a nonempty rectangular sequence")
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _selected(marks: list[tuple[int, int]], setting: RuleSetting) -> bool:
    if not marks:
        return False
    if setting.selector_mode == "ends_in_5":
        return marks[-1][1] == 5
    return any(color == 5 for _, color in marks)


def python_transform(grid: list[list[int]], setting: RuleSetting) -> list[list[int]]:
    """Independent Python mirror; Racket remains label authority in evidence."""
    setting = _validate_setting(setting)
    height, width = _validate_grid(grid)
    out = copy.deepcopy(grid)
    for column in range(width):
        marks = [
            (row, grid[row][column])
            for row in range(height)
            if grid[row][column] != 0
        ]
        if not _selected(marks, setting):
            continue
        if setting.segment_mode == "current":
            previous_row = -1
            for current_row, current_color in marks:
                for row in range(previous_row + 1, current_row + 1):
                    out[row][column] = current_color
                previous_row = current_row
            continue

        first_row, first_color = marks[0]
        for row in range(0, first_row + 1):
            out[row][column] = first_color
        for index in range(1, len(marks)):
            previous_row, previous_color = marks[index - 1]
            current_row, _current_color = marks[index]
            for row in range(previous_row + 1, current_row):
                out[row][column] = previous_color
    return out


def _ensure_scripts_namespace() -> None:
    """Expose the portable shared/tools namespace expected by rule_wrap."""
    if "scripts" in sys.modules:
        return
    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared" / "tools")]
    sys.modules["scripts"] = scripts


def execute(bridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute exact source through the shared protected Racket bridge."""
    _validate_grid(grid)
    _ensure_scripts_namespace()
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"
    result = bridge.eval_text(f"({wrap_rule(source)} {literal})")
    _validate_grid(result)
    return result


def outputs_for(bridge, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        setting.slug: execute(bridge, program(setting), grid)
        for setting in ALL_SETTINGS
    }


class EpisodeAmbiguityError(RuntimeError):
    pass


def build_episode(
    seed: int,
    bridge,
    setting: RuleSetting | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build three demonstrations plus one query under one fixed setting."""
    chosen = choose_setting(seed) if setting is None else _validate_setting(setting)
    gen = generator()
    pairs: list[dict[str, Any]] = []
    for sample_index in range(4):
        grid = gen.generate(seed, sample_index)
        errors = gen.self_check(grid)
        if errors:
            raise ValueError(f"parent generator returned unlawful input: {errors}")
        outputs = outputs_for(bridge, grid)
        for candidate in ALL_SETTINGS:
            expected = python_transform(grid, candidate)
            if outputs[candidate.slug] != expected:
                raise AssertionError(
                    f"Racket/Python mismatch for {candidate.slug} at sample {sample_index}"
                )
        pairs.append(
            {
                "sample_index": sample_index,
                "profile": gen.schedule_profile(seed, sample_index),
                "input": grid,
                "outputs": outputs,
            }
        )

    selected_slug = chosen.slug
    public = {
        "train": [
            {"input": pair["input"], "output": pair["outputs"][selected_slug]}
            for pair in pairs[:3]
        ],
        "test": [{"input": pairs[3]["input"]}],
    }
    rivals: dict[str, dict[str, Any]] = {}
    for rival in ALL_SETTINGS:
        if rival == chosen:
            continue
        rivals[rival.slug] = {
            "demo_mismatches": [
                index
                for index, pair in enumerate(pairs[:3])
                if pair["outputs"][rival.slug] != pair["outputs"][selected_slug]
            ],
            "query_differs": (
                pairs[3]["outputs"][rival.slug]
                != pairs[3]["outputs"][selected_slug]
            ),
        }
    ambiguous = {
        slug: result
        for slug, result in rivals.items()
        if not result["demo_mismatches"] or not result["query_differs"]
    }
    if ambiguous:
        raise EpisodeAmbiguityError(
            "episode does not distinguish every declared setting: "
            + encoded(ambiguous)
        )

    parent_source = GENERATOR_PATH.read_bytes()
    private = {
        "schema": "arc-task-local-parametric-column-segments-v1",
        "status": "proposed prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": chosen.as_dict(),
        "setting_slug": chosen.slug,
        "program": program(chosen),
        "program_sha256": digest(program(chosen)),
        "parent_generator_sha256": digest(parent_source),
        "parent_generator_version": gen.VERSION,
        "pairs": pairs,
        "query_output": pairs[3]["outputs"][selected_slug],
        "rivals": rivals,
        "public_sha256": digest(encoded(public)),
        "limitations": LIMITATIONS,
    }
    return public, private


def materialize_rules(directory: Path = RULE_DIR) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for setting in ALL_SETTINGS:
        path = directory / f"{setting.slug}.rkt"
        path.write_text(program(setting))
        paths[setting.slug] = path
    return paths


def public_filename(seed: int, public: dict[str, Any]) -> str:
    fingerprint = digest(encoded({"episode_seed": seed, "challenge": public}))[:20]
    return f"episode-{fingerprint}.json"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _source_hashes() -> dict[str, str]:
    paths = [
        GENERATOR_PATH,
        Path(__file__),
        Path(__file__).resolve().parent / "README.md",
        HOME / "tests" / "test_parametric_prototype.py",
        ROOT / "shared" / "runtime" / "arc_repl" / "racket_bridge.py",
        ROOT / "shared" / "runtime" / "puzzle_generators" / "rule_wrap.py",
        *sorted(RULE_DIR.glob("*.rkt")),
    ]
    return {
        str(path.relative_to(ROOT)): digest(path.read_bytes())
        for path in paths
        if path.is_file()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--out", type=Path, required=True, help="new evidence directory"
    )
    args = parser.parse_args(argv)
    choose_setting(args.seed)  # strict validation before creating output
    args.out.mkdir(parents=True, exist_ok=False)
    for name in ("programs", "public", "private"):
        (args.out / name).mkdir()

    source_rule_paths = materialize_rules()
    programs = {setting.slug: program(setting) for setting in ALL_SETTINGS}
    for slug, source in programs.items():
        (args.out / "programs" / f"{slug}.rkt").write_text(source)

    receipt: dict[str, Any] = {
        "schema": "arc-task-local-parametric-evidence-v1",
        "status": "proposed prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": args.seed,
        "default_setting": DEFAULT_SETTING.as_dict(),
        "auto_setting": choose_setting(args.seed).as_dict(),
        "settings": [setting.as_dict() for setting in ALL_SETTINGS],
        "command": shlex.join([sys.executable, *sys.argv]),
        "payload_cwd": "WORK/repo",
        "source_sha256": _source_hashes(),
        "parent_generator_sha256": digest(GENERATOR_PATH.read_bytes()),
        "programs": {
            slug: {
                "evidence_path": f"programs/{slug}.rkt",
                "task_workspace_path": str(
                    source_rule_paths[slug].relative_to(ROOT)
                ),
                "sha256": digest(source),
            }
            for slug, source in programs.items()
        },
        "canonical_pairs": {"checked": 0, "passed": 0},
        "episodes": [],
        "failures": [],
        "limitations": LIMITATIONS,
    }

    try:
        from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

        receipt["runtime"] = racket_runtime_status()
        with RacketBridge(max_calls_before_restart=64) as bridge:
            canonical_checks = []
            for row in canonical_rows():
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(row.get(split, [])):
                        actual = execute(bridge, programs[DEFAULT_SETTING.slug], pair["input"])
                        check = {
                            "split": split,
                            "pair_index": pair_index,
                            "passed": actual == pair["output"],
                            "input_sha256": digest(encoded(pair["input"])),
                            "output_sha256": digest(encoded(actual)),
                        }
                        canonical_checks.append(check)
            _write_json(args.out / "private" / "canonical-parity.json", canonical_checks)
            receipt["canonical_pairs"] = {
                "checked": len(canonical_checks),
                "passed": sum(check["passed"] for check in canonical_checks),
                "evidence_path": "private/canonical-parity.json",
            }
            if not all(check["passed"] for check in canonical_checks):
                raise AssertionError("canonical/default Racket parity failed")

            for setting in ALL_SETTINGS:
                public, private = build_episode(args.seed, bridge, setting)
                filename = public_filename(args.seed, public)
                public_path = args.out / "public" / filename
                private_path = args.out / "private" / filename
                _write_json(public_path, public)
                _write_json(private_path, private)
                receipt["episodes"].append(
                    {
                        "setting": setting.as_dict(),
                        "program_sha256": private["program_sha256"],
                        "public_path": str(public_path.relative_to(args.out)),
                        "private_path": str(private_path.relative_to(args.out)),
                        "demonstrations": 3,
                        "queries": 1,
                        "rivals": private["rivals"],
                        "all_demo_distinguishable": all(
                            value["demo_mismatches"]
                            for value in private["rivals"].values()
                        ),
                        "all_query_distinguishable": all(
                            value["query_differs"]
                            for value in private["rivals"].values()
                        ),
                    }
                )
    except Exception as exc:  # retain a machine-readable failed authoring run
        receipt["failures"].append(
            {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        )

    receipt["artifact_sha256"] = {
        str(path.relative_to(args.out)): digest(path.read_bytes())
        for path in sorted(args.out.rglob("*"))
        if path.is_file()
    }
    _write_json(args.out / "receipt.json", receipt)
    print(
        json.dumps(
            {
                "out": str(args.out),
                "canonical_pairs": receipt["canonical_pairs"],
                "episodes": len(receipt["episodes"]),
                "failures": receipt["failures"],
            },
            sort_keys=True,
        )
    )
    return 1 if receipt["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

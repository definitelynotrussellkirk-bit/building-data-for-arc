"""Racket-backed parametric extension of c1fd38e5812b.

The canonical setting is ``compression_axes=both`` and
``output_orientation=identity``.  Episodes vary the axis subset and optional
transpose while keeping the input generator fixed.  Public challenge files
contain only demonstrations and query inputs; parameters, programs, rival
outputs, and query labels stay in private evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol


GENERATOR_MODULE = "puzzle_generators.per_puzzle.c1fd38e5812b.generator"
AXES = ("both", "rows", "columns")
ORIENTATIONS = ("identity", "transpose")
CANONICAL_PARAMETERS = {
    "compression_axes": "both",
    "output_orientation": "identity",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _starts(values: list[int]) -> list[int]:
    return [0] + [i for i in range(1, len(values)) if values[i] != values[i - 1]]


def python_apply(grid: list[list[int]], *, compression_axes: str, output_orientation: str) -> list[list[int]]:
    """Independent mirror used only by unit tests, never for episode labels."""
    if compression_axes not in AXES:
        raise ValueError(compression_axes)
    if output_orientation not in ORIENTATIONS:
        raise ValueError(output_orientation)
    row_ids = _starts([row[0] for row in grid]) if compression_axes in {"both", "rows"} else list(range(len(grid)))
    col_ids = _starts(grid[0]) if compression_axes in {"both", "columns"} else list(range(len(grid[0])))
    result = [[grid[r][c] for c in col_ids] for r in row_ids]
    if output_orientation == "transpose":
        result = [list(row) for row in zip(*result)]
    return result


def materialize_program(*, compression_axes: str, output_orientation: str) -> str:
    """Return a closed Racket rule for one family member."""
    if compression_axes not in AXES:
        raise ValueError(f"unknown compression_axes: {compression_axes!r}")
    if output_orientation not in ORIENTATIONS:
        raise ValueError(f"unknown output_orientation: {output_orientation!r}")

    row_selector = "row-starts" if compression_axes in {"both", "rows"} else "(range height)"
    col_selector = "col-starts" if compression_axes in {"both", "columns"} else "(range width)"
    result = "(apply map list core)" if output_orientation == "transpose" else "core"
    return f"""(rule! (lambda (g)
  (let* ([height (length g)]
         [width (length (car g))]
         [row-starts
          (cons 0
                (for/list ([r (in-range 1 height)]
                           #:when
                           (not (= (list-ref (list-ref g r) 0)
                                   (list-ref (list-ref g (sub1 r)) 0))))
                  r))]
         [col-starts
          (cons 0
                (for/list ([c (in-range 1 width)]
                           #:when
                           (not (= (list-ref (car g) c)
                                   (list-ref (car g) (sub1 c)))))
                  c))]
         [selected-rows {row_selector}]
         [selected-cols {col_selector}]
         [core
          (for/list ([r (in-list selected-rows)])
            (for/list ([c (in-list selected-cols)])
              (list-ref (list-ref g r) c)))])
    {result})))"""


def all_settings() -> list[dict[str, str]]:
    return [
        {"compression_axes": axes, "output_orientation": orientation}
        for axes in AXES
        for orientation in ORIENTATIONS
    ]


class Oracle(Protocol):
    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]: ...


class PythonMirrorOracle:
    """Test-only oracle; production episode generation must use RacketOracle."""

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        for setting in all_settings():
            if program == materialize_program(**setting):
                return python_apply(grid, **setting)
        raise ValueError("program was not materialized by this family")


class RacketOracle:
    """Evaluate every label through the packet's persistent Racket bridge."""

    def __init__(self, timeout_s: float = 20.0):
        from arc_repl.racket_bridge import RacketBridge
        self._bridge = RacketBridge(timeout=timeout_s)
        self._functions: dict[str, str] = {}

    def close(self) -> None:
        self._bridge.shutdown()

    def __enter__(self) -> "RacketOracle":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @staticmethod
    def _unwrap(payload: Any) -> list[list[int]]:
        if isinstance(payload, str):
            try:
                return RacketOracle._unwrap(json.loads(payload))
            except json.JSONDecodeError as error:
                raise RuntimeError(f"Racket returned non-JSON text: {payload!r}") from error
        if isinstance(payload, dict):
            for key in ("value", "result", "grid", "output"):
                if key in payload:
                    return RacketOracle._unwrap(payload[key])
        if (
            isinstance(payload, list)
            and payload
            and all(isinstance(row, list) for row in payload)
            and all(isinstance(value, int) and not isinstance(value, bool) for row in payload for value in row)
        ):
            return payload
        raise RuntimeError(f"unexpected Racket payload: {payload!r}")

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import strip_rule_wrapper

        digest = hashlib.sha256(program.encode()).hexdigest()[:16]
        function = self._functions.get(digest)
        if function is None:
            function = f"__c1fd_parametric_{digest}"
            body = strip_rule_wrapper(program)
            self._bridge.eval_text(f"(define {function} {body})")
            self._functions[digest] = function
        self._bridge.define_grid("__c1fd_parametric_input", grid)
        return self._unwrap(
            self._bridge.eval_text(
                f"({function} __c1fd_parametric_input)"
            )
        )


@dataclass(frozen=True)
class Candidate:
    input: list[list[int]]
    chosen_output: list[list[int]]
    rival_outputs: dict[str, list[list[int]]]


def _setting_key(setting: dict[str, str]) -> str:
    return f"{setting['compression_axes']}__{setting['output_orientation']}"


def _grid_key(grid: list[list[int]]) -> str:
    return _canonical_json(grid)


def _load_selected_generator():
    """Load the selected generator in the packet or from this task workspace.

    ``review.py run`` exposes the normal ``puzzle_generators`` runtime package.
    The source-relative fallback keeps the proposed prototype testable when the
    small repair kit is inspected outside a fully extracted packet; it still
    executes the exact selected ``generator.py`` beside this workspace.
    """

    try:
        return importlib.import_module(GENERATOR_MODULE)
    except ModuleNotFoundError:
        source = Path(__file__).resolve().parents[2] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            "c1fd38e5812b_parametric_selected_generator",
            source,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load selected generator from {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _candidate_stream(seed: int, oracle: Oracle, chosen: dict[str, str]) -> Iterable[Candidate]:
    generator = _load_selected_generator()
    chosen_program = materialize_program(**chosen)
    rivals = [setting for setting in all_settings() if setting != chosen]
    profiles = (
        "uniform_rows",
        "uniform_cols",
        "nonuniform_runs",
        "interior_merges",
        "uniform_runs",
    )
    for sample_index in range(1000):
        profile = profiles[sample_index % len(profiles)]
        difficulty = ("easy", "medium", "hard")[sample_index % 3]
        grid = generator.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            scene_profile=profile,
        )
        chosen_output = oracle.apply(chosen_program, grid)
        rival_outputs = {
            _setting_key(setting): oracle.apply(materialize_program(**setting), grid)
            for setting in rivals
        }
        yield Candidate(grid, chosen_output, rival_outputs)


def build_episode(
    *,
    seed: int,
    chosen: dict[str, str],
    oracle: Oracle,
    demo_count: int = 4,
    query_count: int = 4,
) -> dict[str, Any]:
    if demo_count < 1:
        raise ValueError("demo_count must be positive")
    if query_count != 4:
        raise ValueError("query_count must be exactly four")
    if chosen not in all_settings():
        raise ValueError(f"unknown setting: {chosen}")

    rival_keys = {
        _setting_key(setting) for setting in all_settings() if setting != chosen
    }
    uncovered = set(rival_keys)
    demos: list[Candidate] = []
    queries: list[Candidate] = []
    seen_inputs: set[str] = set()

    for candidate in _candidate_stream(seed, oracle, chosen):
        key = _grid_key(candidate.input)
        if key in seen_inputs:
            continue
        mismatches = {
            rival
            for rival, output in candidate.rival_outputs.items()
            if output != candidate.chosen_output
        }
        if uncovered and mismatches & uncovered:
            demos.append(candidate)
            seen_inputs.add(key)
            uncovered -= mismatches
        elif not uncovered and len(demos) < demo_count:
            demos.append(candidate)
            seen_inputs.add(key)
        elif not uncovered and len(demos) >= demo_count and len(queries) < query_count:
            queries.append(candidate)
            seen_inputs.add(key)
        if not uncovered and len(demos) >= demo_count and len(queries) == query_count:
            break

    if uncovered:
        raise RuntimeError(f"demos did not refute rivals: {sorted(uncovered)}")
    if len(demos) != demo_count or len(queries) != query_count:
        raise RuntimeError("candidate budget exhausted")

    public = {
        "train": [
            {"input": candidate.input, "output": candidate.chosen_output}
            for candidate in demos
        ],
        "test": [{"input": candidate.input} for candidate in queries],
    }
    public_text = _canonical_json(public)
    challenge_id = hashlib.sha256(public_text.encode()).hexdigest()
    private = {
        "challenge_id": challenge_id,
        "seed": seed,
        "parameters": chosen,
        "program": materialize_program(**chosen),
        "queries": [
            {"input": candidate.input, "output": candidate.chosen_output}
            for candidate in queries
        ],
        "rival_programs": {
            _setting_key(setting): materialize_program(**setting)
            for setting in all_settings()
            if setting != chosen
        },
        "demo_rival_outputs": [candidate.rival_outputs for candidate in demos],
        "rivals_refuted_by_demos": sorted(rival_keys),
        "label_engine": type(oracle).__name__,
    }
    return {"public": public, "private": private}


def write_episode(episode: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    visible = episode["public"]
    challenge_id = episode["private"]["challenge_id"]
    # The public filename depends only on the exact visible public JSON.
    public_path = out_dir / f"challenge-{challenge_id[:16]}.json"
    private_path = out_dir / f"private-{challenge_id[:16]}.json"
    public_path.write_text(json.dumps(visible, indent=2) + "\n", encoding="utf-8")
    private_path.write_text(json.dumps(episode["private"], indent=2) + "\n", encoding="utf-8")
    return {"public": public_path, "private": private_path}


def write_programs(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for setting in all_settings():
        path = out_dir / f"{_setting_key(setting)}.rkt"
        path.write_text(materialize_program(**setting) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--compression-axes", choices=AXES, default="both")
    parser.add_argument("--output-orientation", choices=ORIENTATIONS, default="identity")
    parser.add_argument("--demo-count", type=int, default=4)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args()
    chosen = {
        "compression_axes": args.compression_axes,
        "output_orientation": args.output_orientation,
    }
    with RacketOracle() as oracle:
        episode = build_episode(
            seed=args.seed,
            chosen=chosen,
            oracle=oracle,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
    paths = write_episode(episode, args.out / "episodes")
    program_paths = write_programs(args.out / "rules")
    print(json.dumps({
        "challenge_id": episode["private"]["challenge_id"],
        "public": str(paths["public"]),
        "private": str(paths["private"]),
        "programs": [str(path) for path in program_paths],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

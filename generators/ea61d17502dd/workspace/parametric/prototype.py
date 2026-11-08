"""Proposed episode-level rule parameter for ``ea61d17502dd``.

The production generator and canonical authority remain untouched.  This
prototype varies one nearby semantic choice once per episode:

``vertical_bounds_mode``
    ``all_markers`` (canonical default)
        The vertical output bounds include the crossing row and both vertical
        special markers.
    ``crossing_to_farthest`` (proposed alternative)
        The vertical output bounds run only from the crossing row to the
        farther vertical special marker.

All other object roles, input grammar, crossing-priority cue, colors, and weave
logic are unchanged.  A straddled-marker demonstration is included in every
prototype episode so the two settings are observationally distinguishable.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

TASK_ID = "ea61d17502dd"
PROTOTYPE_ID = f"{TASK_ID}-vertical-bounds"
VERSION = "1.0.0-prototype"
PARAMETER_NAME = "vertical_bounds_mode"
MODES = ("all_markers", "crossing_to_farthest")
DEFAULT_MODE = "all_markers"

HERE = Path(__file__).resolve()
WORKSPACE = HERE.parents[1]
TASK_HOME = HERE.parents[2]
ROOT = HERE.parents[4]
REFERENCE_PATH = WORKSPACE / "reference_probe.py"
GENERATOR_PATH = TASK_HOME / "generator.py"

# Three labelled demonstrations and one query.  Pair 1 and the query straddle
# the crossing, so the parameter changes observable outputs in both places.
_INPUT_PROFILES = (
    {
        "grid_h": 12,
        "grid_w": 12,
        "primary": "horizontal",
        "vertical_relation": "outside",
        "strand_extent": "full",
    },
    {
        "grid_h": 15,
        "grid_w": 15,
        "primary": "vertical",
        "vertical_relation": "straddle",
        "strand_extent": "partial",
    },
    {
        "grid_h": 10,
        "grid_w": 10,
        "primary": "horizontal",
        "vertical_relation": "outside",
        "strand_extent": "partial",
    },
    {
        "grid_h": 25,
        "grid_w": 15,
        "primary": "vertical",
        "vertical_relation": "straddle",
        "strand_extent": "full",
    },
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _reference():
    return _load_module(REFERENCE_PATH, f"{TASK_ID}_parametric_reference")


@lru_cache(maxsize=1)
def _generator():
    return _reference().load_generator(GENERATOR_PATH)


def _validate_mode(mode: str) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {MODES}, got {mode!r}"
        )
    return mode


def normalized_program_hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def program_sha256(program: str) -> str:
    return hashlib.sha256(program.encode()).hexdigest()


def _crossing_to_farthest_program(canonical: str) -> str:
    old = """     (define min-row (min-list (cons horiz-row vert-spec-rows)))
     (define max-row (max-list (cons horiz-row vert-spec-rows)))"""
    new = """     (define min-row
       (min horiz-row
            (pick-max vert-spec-rows
                      (lambda (r) (abs (- r horiz-row))))))
     (define max-row
       (max horiz-row
            (pick-max vert-spec-rows
                      (lambda (r) (abs (- r horiz-row))))))"""
    if canonical.count(old) != 1:
        raise RuntimeError(
            "canonical authority no longer contains the expected vertical-bounds block"
        )
    changed = canonical.replace(old, new)
    if changed == canonical:
        raise RuntimeError("alternative program construction made no change")
    return changed


def program_for(mode: str) -> str:
    mode = _validate_mode(mode)
    canonical = _reference().canonical_program()
    if mode == DEFAULT_MODE:
        # Exact byte-for-byte authority preservation is intentional.
        return canonical
    return _crossing_to_farthest_program(canonical)


def choose_mode(seed: int) -> str:
    """Choose exactly one hidden mode for an episode from its deterministic seed."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    from puzzle_generators.base import gen_ctx

    ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=PROTOTYPE_ID,
        difficulty=None,
    )
    return ctx.draw_choice(PARAMETER_NAME, MODES)


def episode_inputs(seed: int, *, difficulty: str = "medium") -> list[list[list[int]]]:
    """Return deterministic lawful inputs; no parameter value is encoded in them."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    generator = _generator()
    grids = []
    for index, profile in enumerate(_INPUT_PROFILES):
        grid = generator.generate(
            seed + index * 104729,
            index,
            difficulty=difficulty,
            **profile,
        )
        errors = generator.self_check(grid)
        if errors:
            raise RuntimeError(f"prototype input {index} is unlawful: {errors}")
        grids.append(grid)
    return grids


def input_profile(grid: list[list[int]]) -> dict[str, Any]:
    return _reference().observed(grid)


def python_output(grid: list[list[int]], mode: str) -> list[list[int]]:
    mode = _validate_mode(mode)
    reference = _reference()
    if mode == DEFAULT_MODE:
        return reference.rule_output(deepcopy(grid))
    return reference.crossing_to_farthest_output(deepcopy(grid))


_RUNTIME_HOLDER: tempfile.TemporaryDirectory[str] | None = None
_RUNTIME_STAGE: Path | None = None
_RACKET_CACHE: dict[tuple[str, str], list[list[list[int]]]] = {}


def _runtime_stage() -> Path:
    """Prepare one task-local isolated runtime per Python process."""
    global _RUNTIME_HOLDER, _RUNTIME_STAGE
    if _RUNTIME_STAGE is None:
        from arcpuzzles import Catalog
        from arcpuzzles.runtime import prepare_runtime

        _RUNTIME_HOLDER = tempfile.TemporaryDirectory(
            prefix=f"{TASK_ID}-parametric-runtime-"
        )
        _RUNTIME_STAGE = Path(_RUNTIME_HOLDER.name)
        prepare_runtime(Catalog(ROOT), _RUNTIME_STAGE, TASK_ID)
    return _RUNTIME_STAGE


def racket_outputs(
    program: str, grids: list[list[list[int]]]
) -> list[list[list[int]]]:
    """Execute one exact Racket program on a batch; never fall back to Python."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket source")
    if not isinstance(grids, list):
        raise TypeError("grids must be a list")
    cache_key = (
        program_sha256(program),
        hashlib.sha256(
            json.dumps(grids, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest(),
    )
    cached = _RACKET_CACHE.get(cache_key)
    if cached is not None:
        return deepcopy(cached)

    from arcpuzzles.runtime import run_process

    stage = _runtime_stage()
    request_name = f"parametric-request-{cache_key[0][:12]}-{cache_key[1][:12]}.json"
    request_path = stage / request_name
    request_path.write_text(
        json.dumps({"program": program, "grids": grids}), encoding="utf-8"
    )
    script = f"""
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path({request_name!r}).read_text(encoding='utf-8'))
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request['grids']]))
finally:
    bridge.shutdown()
"""
    result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
    if result["exit_code"] or result["timed_out"]:
        raise RuntimeError(
            "Racket worker failed: "
            f"exit={result['exit_code']} timed_out={result['timed_out']} "
            f"stderr={result['stderr']!r} stdout={result['stdout']!r}"
        )
    outputs = json.loads(result["stdout"])
    if len(outputs) != len(grids):
        raise RuntimeError(
            f"Racket returned {len(outputs)} outputs for {len(grids)} inputs"
        )
    _RACKET_CACHE[cache_key] = outputs
    return deepcopy(outputs)


def _outputs_by_mode(
    grids: list[list[list[int]]], *, execute_racket: bool
) -> dict[str, list[list[list[int]]]]:
    outputs = {}
    for mode in MODES:
        if execute_racket:
            observed = racket_outputs(program_for(mode), grids)
            mirror = [python_output(grid, mode) for grid in grids]
            if observed != mirror:
                mismatches = [
                    index
                    for index, (left, right) in enumerate(zip(observed, mirror))
                    if left != right
                ]
                raise RuntimeError(
                    f"Racket/Python mismatch for {mode}: indices={mismatches}"
                )
            outputs[mode] = observed
        else:
            outputs[mode] = [python_output(grid, mode) for grid in grids]
    return outputs


def build_episode(
    *,
    seed: int,
    mode: str | None = None,
    difficulty: str = "medium",
    execute_racket: bool = True,
) -> dict[str, Any]:
    """Build one complete 3-train/1-test episode with a fixed hidden mode."""
    selected = choose_mode(seed) if mode is None else _validate_mode(mode)
    grids = episode_inputs(seed, difficulty=difficulty)
    outputs = _outputs_by_mode(grids, execute_racket=execute_racket)
    selected_outputs = outputs[selected]
    train = [
        {"input": deepcopy(grids[index]), "output": deepcopy(selected_outputs[index])}
        for index in range(3)
    ]
    test = [
        {"input": deepcopy(grids[3]), "output": deepcopy(selected_outputs[3])}
    ]

    rivals = [candidate for candidate in MODES if candidate != selected]
    surviving = [
        rival
        for rival in rivals
        if all(outputs[rival][index] == selected_outputs[index] for index in range(3))
    ]
    distinguishing = [
        index
        for index in range(3)
        if outputs[MODES[0]][index] != outputs[MODES[1]][index]
    ]
    query_differs = outputs[MODES[0]][3] != outputs[MODES[1]][3]
    if not distinguishing:
        raise RuntimeError("prototype episode has no parameter-distinguishing demo")
    if not query_differs:
        raise RuntimeError("prototype query does not depend on the parameter")

    program = program_for(selected)
    return {
        "schema": "ea61d17502dd-parametric-episode-v1",
        "status": "racket_verified" if execute_racket else "python_only_unverified",
        "task_id": TASK_ID,
        "prototype_id": PROTOTYPE_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "parameter": {
            "name": PARAMETER_NAME,
            "value": selected,
            "default": DEFAULT_MODE,
        },
        "input_constraints": {
            "grammar": "canonical crossed-strand generator",
            "teaching_requirement": (
                "at least one labelled straddled-marker input; this episode uses "
                "train index 1 and a straddled query"
            ),
        },
        "program": program,
        "program_sha256": program_sha256(program),
        "normalized_program_hash": normalized_program_hash(program),
        "train": train,
        "test": test,
        "input_profiles": [input_profile(grid) for grid in grids],
        "distinguishing_train_indices": distinguishing,
        "query_differs_between_modes": query_differs,
        "rival_survivors": surviving,
        "rival_results": {
            rival: {
                "fits_all_train": rival in surviving,
                "train_matches": [
                    outputs[rival][index] == selected_outputs[index]
                    for index in range(3)
                ],
                "query_matches": outputs[rival][3] == selected_outputs[3],
            }
            for rival in rivals
        },
        "output_authority": "exact Racket execution" if execute_racket else "Python mirror only",
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Redact hidden semantics, reference code, seed, and query answers."""
    return {
        "schema": "arcpuzzles-parametric-public-v1",
        "family": "crossed-strand-weave",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def write_episode(episode: dict[str, Any], directory: Path) -> dict[str, Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    public = public_challenge(episode)
    public_path = directory / "challenge.json"
    private_path = directory / "private_episode.json"
    program_path = directory / "program.rkt"
    manifest_path = directory / "manifest.json"
    public_path.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    private_path.write_text(json.dumps(episode, indent=2) + "\n", encoding="utf-8")
    program_path.write_text(episode["program"] + "\n", encoding="utf-8")
    manifest = {
        "schema": "ea61d17502dd-parametric-artifacts-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "files": {
            path.name: {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for path in (public_path, private_path, program_path)
        },
        "public_payload_sha256": _json_sha256(public),
        "private_payload_sha256": _json_sha256(episode),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "public": public_path,
        "private": private_path,
        "program": program_path,
        "manifest": manifest_path,
    }


def build_probe(
    *, seed: int, difficulty: str, out: Path, execute_racket: bool = True
) -> dict[str, Any]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    episodes = {}
    paths = {}
    for mode in MODES:
        episode = build_episode(
            seed=seed,
            mode=mode,
            difficulty=difficulty,
            execute_racket=execute_racket,
        )
        episodes[mode] = episode
        paths[mode] = write_episode(episode, out / mode)

    witness_index = episodes[DEFAULT_MODE]["distinguishing_train_indices"][0]
    witness = {
        "schema": "ea61d17502dd-parametric-witness-v1",
        "seed": seed,
        "input_index": witness_index,
        "input_profile": episodes[DEFAULT_MODE]["input_profiles"][witness_index],
        "input": episodes[DEFAULT_MODE]["train"][witness_index]["input"],
        "outputs": {
            mode: episodes[mode]["train"][witness_index]["output"] for mode in MODES
        },
        "outputs_differ": (
            episodes[MODES[0]]["train"][witness_index]["output"]
            != episodes[MODES[1]]["train"][witness_index]["output"]
        ),
    }
    witness_path = out / "distinguishing_witness.json"
    witness_path.write_text(json.dumps(witness, indent=2) + "\n", encoding="utf-8")

    canonical_program = program_for(DEFAULT_MODE)
    report = {
        "schema": "ea61d17502dd-parametric-probe-v1",
        "status": "passed",
        "scope": "proposed prototype; canonical production unchanged",
        "task_id": TASK_ID,
        "prototype_id": PROTOTYPE_ID,
        "prototype_version": VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(MODES),
            "default": DEFAULT_MODE,
            "selection_scope": "once per episode",
            "input_dependency": (
                "No grammar change; a straddled-marker labelled demonstration is "
                "required to distinguish the modes."
            ),
        },
        "seed": seed,
        "difficulty": difficulty,
        "execution": "Racket" if execute_racket else "Python only (not acceptance evidence)",
        "canonical_exact": canonical_program == _reference().canonical_program(),
        "canonical_rule_hash": normalized_program_hash(canonical_program),
        "source_hashes": {
            "prototype.py": hashlib.sha256(HERE.read_bytes()).hexdigest(),
            "generator.py": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
            "reference_probe.py": hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest(),
        },
        "settings": {
            mode: {
                "program_sha256": episodes[mode]["program_sha256"],
                "normalized_program_hash": episodes[mode]["normalized_program_hash"],
                "program_path": str(paths[mode]["program"].relative_to(out)),
                "private_episode_path": str(paths[mode]["private"].relative_to(out)),
                "public_challenge_path": str(paths[mode]["public"].relative_to(out)),
                "rival_survivors": episodes[mode]["rival_survivors"],
                "distinguishing_train_indices": episodes[mode]["distinguishing_train_indices"],
                "query_differs_between_modes": episodes[mode]["query_differs_between_modes"],
            }
            for mode in MODES
        },
        "witness_path": witness_path.name,
        "limitations": [
            "Evidence covers one deterministic seed and the two declared settings, not all inputs.",
            "The alternative is a proposed nearby rule, not an approved production authority.",
            "A lesson without a straddled-marker labelled example can leave the modes ambiguous.",
        ],
    }
    failures = []
    if not report["canonical_exact"]:
        failures.append("canonical default is not exact")
    if report["canonical_rule_hash"] != _reference().RULE_HASH:
        failures.append("canonical normalized hash drifted")
    if not witness["outputs_differ"]:
        failures.append("retained witness outputs do not differ")
    for mode in MODES:
        if episodes[mode]["rival_survivors"]:
            failures.append(f"{mode} episode leaves rivals: {episodes[mode]['rival_survivors']}")
    if failures:
        report["status"] = "failed"
        report["failures"] = failures
    report_path = out / "probe_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=271828)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="debug only: do not count as Racket execution evidence",
    )
    args = parser.parse_args(argv)
    report = build_probe(
        seed=args.seed,
        difficulty=args.difficulty,
        out=args.out,
        execute_racket=not args.python_only,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Proposed episode-level axis parameter for ARC family ``3f26d45b9f51``.

This is a task-local research prototype, not an approved production generator.
One ``axis_mode`` is chosen for an entire episode, then all demonstration and
query labels are executed by the matching Racket rule.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "3f26d45b9f51"
ORIGINAL_FAMILY = "training:06df4c85"
STATUS = "proposed_unapproved"
AXIS_MODES = ("both_axes", "horizontal_only", "vertical_only")
DEFAULT_AXIS_MODE = "both_axes"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def grid_sha256(grid: list[list[int]]) -> str:
    """Return a stable content hash for one ARC grid."""
    return _sha256_bytes(_json_bytes(grid))


@lru_cache(maxsize=1)
def canonical_record() -> dict[str, Any]:
    """Load the single canonical ledger row for this task from this source tree."""
    rows: list[dict[str, Any]] = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    row = rows[0]
    if not isinstance(row.get("program_solution"), str):
        raise ValueError(f"canonical row for {TASK_ID} has no Racket program_solution")
    return row


def _validate_axis_mode(axis_mode: Any) -> str:
    if type(axis_mode) is not str or axis_mode not in AXIS_MODES:
        raise ValueError(f"axis_mode must be one of {AXIS_MODES}, got {axis_mode!r}")
    return axis_mode


def _parameterized_program(*, horizontal: bool, vertical: bool) -> str:
    horizontal_flag = "#t" if horizontal else "#f"
    vertical_flag = "#t" if vertical else "#f"
    return f"""(rule! (lambda (g)
  ;; Proposed parameterized sibling of the canonical connect-dots rule.
  (let* ((lc (mode g))
         (mcolors (filter (lambda (kc) (and (!= kc 0) (!= kc lc)))
                    (unique (flatmap (lambda (r) r) (grid->list g))))))
    (reduce (lambda (acc mc)
      (let* ((positions (find-color g mc))
             (cpositions (map (lambda (p)
                 (list (floor (/ (+ (fst p) 1) 3))
                       (floor (/ (+ (snd p) 1) 3))))
               positions))
             (crow-set (unique (map fst cpositions)))
             (ccol-set (unique (map snd cpositions)))
             (after-horizontal
               (if {horizontal_flag}
                 (reduce (lambda (a cr)
                   (let* ((cols-here (map snd
                                      (filter (lambda (cp) (= (fst cp) cr)) cpositions))))
                     (if (< (length cols-here) 2) a
                       (let* ((cmin (min-list cols-here))
                              (cmax (max-list cols-here)))
                         (reduce (lambda (a2 cc)
                           (let* ((pr (* 3 cr)) (pc (* 3 cc)))
                             (set-cell (set-cell (set-cell (set-cell a2 pr pc mc)
                               pr (+ pc 1) mc) (+ pr 1) pc mc) (+ pr 1) (+ pc 1) mc)))
                           a (range cmin (+ cmax 1)))))))
                   acc crow-set)
                 acc))
             (after-vertical
               (if {vertical_flag}
                 (reduce (lambda (a cc)
                   (let* ((rows-here (map fst
                                      (filter (lambda (cp) (= (snd cp) cc)) cpositions))))
                     (if (< (length rows-here) 2) a
                       (let* ((rmin (min-list rows-here))
                              (rmax (max-list rows-here)))
                         (reduce (lambda (a2 cr)
                           (let* ((pr (* 3 cr)) (pc (* 3 cc)))
                             (set-cell (set-cell (set-cell (set-cell a2 pr pc mc)
                               pr (+ pc 1) mc) (+ pr 1) pc mc) (+ pr 1) (+ pc 1) mc)))
                           a (range rmin (+ rmax 1)))))))
                   after-horizontal ccol-set)
                 after-horizontal)))
        after-vertical))
      g mcolors))))"""


@lru_cache(maxsize=None)
def _program_for_validated(axis_mode: str) -> str:
    if axis_mode == DEFAULT_AXIS_MODE:
        return canonical_record()["program_solution"]
    if axis_mode == "horizontal_only":
        return _parameterized_program(horizontal=True, vertical=False)
    return _parameterized_program(horizontal=False, vertical=True)


def program_for(axis_mode: str = DEFAULT_AXIS_MODE) -> str:
    """Materialize the exact Racket rule for one episode setting.

    The default returns the canonical ledger text byte-for-byte. Alternate
    modes are explicit sibling programs; the production rule is never edited.
    Validation precedes caching so every invalid public value raises ValueError,
    including unhashable containers.
    """
    return _program_for_validated(_validate_axis_mode(axis_mode))


def program_sha256(axis_mode: str = DEFAULT_AXIS_MODE) -> str:
    return _sha256_bytes(program_for(axis_mode).encode("utf-8"))


def _racket_grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(cell) for cell in row) + ")" for row in grid)
    return f"'({rows})"


def execute_rule(program: str, grid: list[list[int]], *, bridge=None) -> list[list[int]]:
    """Execute ``program`` against ``grid`` through the real Racket bridge."""
    if type(program) is not str or not program.strip():
        raise ValueError("program must be nonempty Racket source")
    from puzzle_generators.rule_wrap import wrap_rule

    expression = f"({wrap_rule(program)} {_racket_grid_literal(grid)})"
    if bridge is not None:
        return bridge.eval_text(expression)

    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=30, max_calls_before_restart=256) as runtime:
        return runtime.eval_text(expression)


@lru_cache(maxsize=1)
def _selected_generator():
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module, source_path, source_sha256


def _validate_integer(name: str, value: Any, *, positive: bool) -> int:
    minimum = 1 if positive else 0
    if type(value) is not int or value < minimum:
        qualifier = "a positive exact integer" if positive else "a nonnegative exact integer"
        raise ValueError(f"{name} must be {qualifier}, got {value!r}")
    return value


def _derived_draw(seed: int, slot: int, attempt: int) -> tuple[int, int, str]:
    body = f"{TASK_ID}:axis-mode-v1:{seed}:{slot}:{attempt}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(body).digest(), "big")
    generated_seed = value & ((1 << 63) - 1)
    sample_index = (value >> 64) % 1_000_000
    difficulty = ("easy", "medium", "hard")[(slot + attempt) % 3]
    return generated_seed, sample_index, difficulty


def _draw_distinguishing_inputs(
    *, seed: int, count: int, bridge
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    generator, _source_path, _source_sha256 = _selected_generator()
    accepted: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    seen: set[str] = set()

    for slot in range(count):
        for attempt in range(64):
            generated_seed, sample_index, difficulty = _derived_draw(seed, slot, attempt)
            grid = generator.generate(generated_seed, sample_index, difficulty=difficulty)
            input_sha256 = grid_sha256(grid)
            if input_sha256 in seen:
                continue
            outputs = {
                mode: execute_rule(program_for(mode), grid, bridge=bridge) for mode in AXIS_MODES
            }
            if len({grid_sha256(output) for output in outputs.values()}) != len(AXIS_MODES):
                continue
            seen.add(input_sha256)
            accepted.append({"input": grid, "outputs": outputs})
            provenance.append(
                {
                    "slot": slot,
                    "attempt": attempt,
                    "generated_seed": generated_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "input_sha256": input_sha256,
                    "output_sha256": {
                        mode: grid_sha256(outputs[mode]) for mode in AXIS_MODES
                    },
                }
            )
            break
        else:
            raise ValueError(
                f"could not draw a unique three-way distinguishing input for slot {slot}"
            )
    return accepted, provenance


def make_episode(
    *,
    seed: int,
    axis_mode: str,
    demo_count: int = 3,
    query_count: int = 4,
    bridge=None,
) -> dict[str, Any]:
    """Build one fixed-setting episode with Racket-executed labels."""
    seed = _validate_integer("seed", seed, positive=False)
    axis_mode = _validate_axis_mode(axis_mode)
    demo_count = _validate_integer("demo_count", demo_count, positive=True)
    query_count = _validate_integer("query_count", query_count, positive=True)

    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=30, max_calls_before_restart=256) as runtime:
            return make_episode(
                seed=seed,
                axis_mode=axis_mode,
                demo_count=demo_count,
                query_count=query_count,
                bridge=runtime,
            )

    total = demo_count + query_count
    draws, provenance = _draw_distinguishing_inputs(seed=seed, count=total, bridge=bridge)
    selected_outputs = [draw["outputs"][axis_mode] for draw in draws]
    all_pairs = [
        {"input": copy.deepcopy(draw["input"]), "output": copy.deepcopy(output)}
        for draw, output in zip(draws, selected_outputs)
    ]

    consistent_settings = [
        mode
        for mode in AXIS_MODES
        if all(
            draws[index]["outputs"][mode] == selected_outputs[index]
            for index in range(demo_count)
        )
    ]
    rivals: dict[str, Any] = {}
    for mode in AXIS_MODES:
        if mode == axis_mode:
            continue
        rivals[mode] = {
            "demonstration_mismatch_indices": [
                index
                for index in range(demo_count)
                if draws[index]["outputs"][mode] != selected_outputs[index]
            ],
            "query_mismatch_indices": [
                index
                for index in range(query_count)
                if draws[demo_count + index]["outputs"][mode]
                != selected_outputs[demo_count + index]
            ],
        }
    if consistent_settings != [axis_mode]:
        raise ValueError(
            "demonstrations do not uniquely identify the selected axis_mode: "
            f"{consistent_settings!r}"
        )

    _module, source_path, source_sha256 = _selected_generator()
    program = program_for(axis_mode)
    return {
        "status": STATUS,
        "task_id": TASK_ID,
        "original_family": ORIGINAL_FAMILY,
        "seed": seed,
        "parameters": {"axis_mode": axis_mode},
        "program": program,
        "program_sha256": _sha256_bytes(program.encode("utf-8")),
        "train": all_pairs[:demo_count],
        "test": all_pairs[demo_count:],
        "declared_rival_analysis": {
            "declared_settings": list(AXIS_MODES),
            "consistent_settings": consistent_settings,
            "rivals": rivals,
        },
        "meta": {
            "generator_source": str(source_path.relative_to(ROOT)),
            "generator_source_sha256": source_sha256,
            "demo_count": demo_count,
            "query_count": query_count,
            "draws": provenance,
        },
    }


def public_challenge(private_episode: dict[str, Any]) -> dict[str, Any]:
    """Project private episode data to exactly visible ARC challenge fields."""
    return copy.deepcopy(
        {
            "train": private_episode["train"],
            "test": [{"input": pair["input"]} for pair in private_episode["test"]],
        }
    )


def public_bytes(private_episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(private_episode))


def public_id(private_episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(private_episode))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_settings(settings: Iterable[str]) -> tuple[str, ...]:
    values = tuple(settings)
    if not values:
        raise ValueError("settings must contain at least one axis_mode")
    for value in values:
        _validate_axis_mode(value)
    if len(set(values)) != len(values):
        raise ValueError("settings must not contain duplicate axis_mode values")
    return values


def write_evidence(
    *,
    seed: int,
    settings: Iterable[str],
    demo_count: int,
    query_count: int,
    out: Path | str,
    bridge=None,
) -> dict[str, Any]:
    """Create a fail-closed evidence directory without overwriting prior runs."""
    seed = _validate_integer("seed", seed, positive=False)
    demo_count = _validate_integer("demo_count", demo_count, positive=True)
    query_count = _validate_integer("query_count", query_count, positive=True)
    settings = _validate_settings(settings)
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)

    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=30, max_calls_before_restart=256) as runtime:
            return write_evidence(
                seed=seed,
                settings=settings,
                demo_count=demo_count,
                query_count=query_count,
                out=out,
                bridge=runtime,
            )

    parity: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)):
        observed = execute_rule(program_for(DEFAULT_AXIS_MODE), pair["input"], bridge=bridge)
        parity.append(
            {
                "index": index,
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": grid_sha256(pair["input"]),
                "expected_output_sha256": grid_sha256(pair["output"]),
                "observed_output_sha256": grid_sha256(observed),
                "matches": observed == pair["output"],
            }
        )
    if not parity or not all(row["matches"] for row in parity):
        raise ValueError("canonical default parity failed")

    prepared: list[dict[str, Any]] = []
    seen_public_payloads: set[bytes] = set()
    ambiguity_count = 0
    for setting in settings:
        private = make_episode(
            seed=seed,
            axis_mode=setting,
            demo_count=demo_count,
            query_count=query_count,
            bridge=bridge,
        )
        visible = public_bytes(private)
        if visible in seen_public_payloads:
            raise ValueError("duplicate visible public challenge payload")
        seen_public_payloads.add(visible)
        visible_id = _sha256_bytes(visible)
        if visible_id != public_id(private):
            raise ValueError("public challenge ID does not match visible bytes")
        if private["declared_rival_analysis"]["consistent_settings"] != [setting]:
            ambiguity_count += 1
        prepared.append(
            {
                "axis_mode": setting,
                "private": private,
                "public_bytes": visible,
                "public_id": visible_id,
            }
        )

    prepared.sort(key=lambda row: row["public_id"])

    # Materialize only after all semantic checks pass, so failed runs leave no
    # partial evidence directory and callers can safely retry with the same path.
    out.mkdir(parents=True, exist_ok=False)
    private_episodes = out / "private" / "episodes"
    private_rules = out / "private" / "rules"
    public_dir = out / "public"
    private_episodes.mkdir(parents=True)
    private_rules.mkdir(parents=True)
    public_dir.mkdir()

    rows: list[dict[str, Any]] = []
    for index, prepared_row in enumerate(prepared):
        setting = prepared_row["axis_mode"]
        private = prepared_row["private"]
        visible_id = prepared_row["public_id"]
        private_rel = Path("private") / "episodes" / f"episode-{index:03d}.json"
        rule_rel = Path("private") / "rules" / f"rule-{index:03d}.rkt"
        public_rel = Path("public") / f"challenge-{visible_id}.json"
        _write_json(out / private_rel, private)
        (out / rule_rel).write_text(private["program"], encoding="utf-8")
        (out / public_rel).write_bytes(prepared_row["public_bytes"])

        rows.append(
            {
                "index": index,
                "axis_mode": setting,
                "private_path": private_rel.as_posix(),
                "public_path": public_rel.as_posix(),
                "rule_path": rule_rel.as_posix(),
                "public_id": visible_id,
                "program_sha256": private["program_sha256"],
                "consistent_settings": private["declared_rival_analysis"][
                    "consistent_settings"
                ],
                "input_sha256": [
                    grid_sha256(pair["input"])
                    for pair in private["train"] + private["test"]
                ],
            }
        )

    report = {
        "schema": "arc-parametric-axis-mode-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "original_family": ORIGINAL_FAMILY,
        "seed": seed,
        "parameter_contract": {
            "name": "axis_mode",
            "settings": list(AXIS_MODES),
            "default": DEFAULT_AXIS_MODE,
            "scope": "chosen once per episode and fixed across demonstrations and queries",
        },
        "counts": {
            "episodes": len(rows),
            "demonstrations": len(rows) * demo_count,
            "queries": len(rows) * query_count,
            "canonical_pairs_checked": len(parity),
            "declared_rival_ambiguities": ambiguity_count,
        },
        "canonical_default_parity": parity,
        "episodes": rows,
        "limits": [
            "Research prototype only; the production generator and canonical rule remain unchanged.",
            "Rival analysis is complete only for the three declared axis_mode settings.",
            "Inputs are drawn from the current production generator, whose required L witness makes all settings distinguishable.",
        ],
    }
    _write_json(out / "report.json", report)

    files = []
    for path in sorted(candidate for candidate in out.rglob("*") if candidate.is_file()):
        relative = path.relative_to(out).as_posix()
        files.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_bytes(path.read_bytes()),
            }
        )
    manifest = {
        "schema": "arc-parametric-axis-mode-manifest-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return report


def select_axis_mode(seed: int) -> str:
    seed = _validate_integer("seed", seed, positive=False)
    digest = hashlib.sha256(f"{TASK_ID}:axis-mode-selection:{seed}".encode("utf-8")).digest()
    return AXIS_MODES[int.from_bytes(digest, "big") % len(AXIS_MODES)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--axis-mode", choices=AXIS_MODES)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.all_settings and args.axis_mode is not None:
        parser.error("--all-settings and --axis-mode are mutually exclusive")
    settings = AXIS_MODES if args.all_settings else (args.axis_mode or select_axis_mode(args.seed),)
    report = write_evidence(
        seed=args.seed,
        settings=settings,
        demo_count=args.demo_count,
        query_count=args.query_count,
        out=args.out,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "task_id": TASK_ID,
                "episodes": report["counts"]["episodes"],
                "canonical_pairs_checked": report["counts"]["canonical_pairs_checked"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

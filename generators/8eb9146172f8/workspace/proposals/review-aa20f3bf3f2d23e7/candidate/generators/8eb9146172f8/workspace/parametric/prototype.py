"""Proposed task-local step-size rule family for ``8eb9146172f8``.

This module is deliberately outside the production generator contract.  The
canonical setting is ``step_size=1``.  ``step_size=2`` preserves the same
markers, edge semantics, traversal order, and clipping behavior while doubling
each lateral deflection caused by a red marker.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import re
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "8eb9146172f8"
PROTOTYPE_VERSION = "1.0.0-proposed"
STEP_SIZES = (1, 2)
DEFAULT_STEP_SIZE = 1
ROOT = find_root(__file__)

_SHIFT_BLOCK = re.compile(
    r"\(shift-val\s+\(cond\s+"
    r"\(\(eq\? red-edge 'top\)\s+1\)\s+"
    r"\(\(eq\? red-edge 'bottom\)\s+-1\)\s+"
    r"\(\(eq\? red-edge 'left\)\s+1\)\s+"
    r"\(else\s+-1\)\)\)"
)


def validate_step_size(step_size: Any) -> int:
    """Return a declared step size, rejecting bools and coercions."""
    if type(step_size) is not int or step_size not in STEP_SIZES:
        raise ValueError(f"step_size must be an exact integer in {STEP_SIZES}")
    return step_size


@lru_cache(maxsize=1)
def canonical_rule() -> str:
    """Load the unique canonical Racket authority from this source tree."""
    rules: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                rules.add(row["program_solution"])
    if len(rules) != 1:
        raise RuntimeError(
            f"expected one canonical Racket authority for {TASK_ID}, got {len(rules)}"
        )
    return rules.pop()


def emit_rule(step_size: int = DEFAULT_STEP_SIZE) -> str:
    """Materialize one exact Racket rule, preserving default bytes verbatim."""
    step_size = validate_step_size(step_size)
    source = canonical_rule()
    if step_size == DEFAULT_STEP_SIZE:
        return source
    replacement = (
        "(shift-val (cond "
        f"((eq? red-edge 'top) {step_size}) "
        f"((eq? red-edge 'bottom) {-step_size}) "
        f"((eq? red-edge 'left) {step_size}) "
        f"(else {-step_size})))"
    )
    transformed, count = _SHIFT_BLOCK.subn(replacement, source)
    if count != 1:
        raise RuntimeError(
            "canonical rule structure changed: expected one shift-val block"
        )
    return transformed


@lru_cache(maxsize=1)
def _generator_record():
    return load_selected_generator(TASK_ID, root=ROOT)


def _generator():
    return _generator_record()[0]


def apply_python(
    grid: list[list[int]], step_size: int = DEFAULT_STEP_SIZE
) -> list[list[int]]:
    """Independent rule-loop mirror for audit; Racket remains label authority."""
    step_size = validate_step_size(step_size)
    generator = _generator()
    facts, errors = generator._analyze(grid)
    if errors or facts is None:
        raise ValueError("rule expects a lawful scene: " + "; ".join(errors))

    h = facts["grid_h"]
    w = facts["grid_w"]
    cyan_edge = facts["cyan_edge"]
    red_edge = facts["red_edge"]
    cyan_cells = list(facts["cyan_cells"])
    red_cells = list(facts["red_cells"])
    red_rows = {row for row, _ in red_cells}
    red_cols = {col for _, col in red_cells}
    direction = 1 if red_edge in ("top", "left") else -1
    shift = direction * step_size

    output = [row[:] for row in grid]
    for start_row, start_col in cyan_cells:
        row, col = start_row, start_col
        if cyan_edge == "top":
            for row in range(h):
                if row in red_rows:
                    col += shift
                if 0 <= col < w:
                    output[row][col] = 8
        elif cyan_edge == "bottom":
            for row in range(h - 1, -1, -1):
                if row in red_rows:
                    col += shift
                if 0 <= col < w:
                    output[row][col] = 8
        elif cyan_edge == "left":
            for col in range(w):
                if col in red_cols:
                    row += shift
                if 0 <= row < h:
                    output[row][col] = 8
        elif cyan_edge == "right":
            for col in range(w - 1, -1, -1):
                if col in red_cols:
                    row += shift
                if 0 <= row < h:
                    output[row][col] = 8
        else:  # pragma: no cover - the selected generator validates this.
            raise AssertionError(f"unexpected cyan edge {cyan_edge!r}")
    return output


class _Verifier:
    """Small owned Racket bridge wrapper used by tests and episode authoring."""

    def __init__(self) -> None:
        self.bridge = RacketBridge()

    def apply(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        body = strip_rule_wrapper(source)
        if not body.startswith("(lambda (g)"):
            raise ValueError("prototype accepts only an emitted self-contained rule")
        self.bridge.define_grid("g", grid)
        value = self.bridge.eval_text(f"({body} g)")
        if not isinstance(value, list):
            raise ValueError("Racket rule did not return a grid")
        return value

    def close(self) -> None:
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


def open_verifier() -> _Verifier:
    return _Verifier()


ORIENTATIONS = (
    ("top", "left"),
    ("top", "right"),
    ("bottom", "left"),
    ("bottom", "right"),
    ("left", "top"),
    ("left", "bottom"),
    ("right", "top"),
    ("right", "bottom"),
)
SCENE_DIMENSIONS = (
    (9, 9),
    (12, 12),
    (12, 17),
    (14, 10),
    (15, 19),
    (17, 12),
    (18, 13),
    (20, 22),
)
MAX_EPISODE_COUNT = 32


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_bytes(_json_bytes(grid))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not 1 <= value <= MAX_EPISODE_COUNT:
        raise ValueError(
            f"{name} must be an exact integer in 1..{MAX_EPISODE_COUNT}"
        )
    return value


def parameters_for_seed(seed: int) -> dict[str, int]:
    seed = _validate_seed(seed)
    return {"step_size": STEP_SIZES[seed % len(STEP_SIZES)]}


def _derived_seed(seed: int, label: str, index: int = 0) -> int:
    payload = (
        f"{TASK_ID}|{PROTOTYPE_VERSION}|{seed}|{label}|{index}".encode("utf-8")
    )
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _input_candidates(seed: int):
    order = list(ORIENTATIONS)
    random.Random(_derived_seed(seed, "orientation-order")).shuffle(order)
    index = 0
    while True:
        rng = random.Random(_derived_seed(seed, "scene", index))
        cyan_edge, red_edge = order[index % len(order)]
        h, w = SCENE_DIMENSIONS[rng.randrange(len(SCENE_DIMENSIONS))]
        overrides = {
            "grid_h": h,
            "grid_w": w,
            "cyan_edge": cyan_edge,
            "red_edge": red_edge,
            "n_red": 2 + rng.randrange(3),
            "n_cyan": 1 + rng.randrange(4),
        }
        generation_seed = _derived_seed(seed, "generator", index)
        grid = _generator().generate(
            generation_seed,
            index,
            difficulty=None,
            **overrides,
        )
        yield {
            "input": grid,
            "input_sha256": _grid_sha256(grid),
            "generation": {
                "seed": generation_seed,
                "sample_index": index,
                "overrides": overrides,
            },
        }
        index += 1


def _sample_inputs(seed: int, count: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts = max(128, count * 32)
    for attempt, candidate in enumerate(_input_candidates(seed), start=1):
        digest = candidate["input_sha256"]
        if digest in seen:
            if attempt >= max_attempts:
                break
            continue
        grid = candidate["input"]
        if apply_python(grid, 1) == apply_python(grid, 2):
            if attempt >= max_attempts:
                break
            continue
        seen.add(digest)
        selected.append(candidate)
        if len(selected) == count:
            return selected
        if attempt >= max_attempts:
            break
    raise RuntimeError(
        f"could not sample {count} unique parameter-distinguishing inputs "
        f"within {max_attempts} attempts"
    )


def make_episode(
    seed: int,
    *,
    step_size: int | None = None,
    n_train: int = 4,
    n_test: int = 4,
    bridge: _Verifier | None = None,
) -> dict[str, Any]:
    """Build one private episode with a rule selected once for every pair."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    if step_size is None:
        chosen = parameters_for_seed(seed)["step_size"]
        selection = "deterministic_seed_draw"
    else:
        chosen = validate_step_size(step_size)
        selection = "explicit_override"
    rival = next(value for value in STEP_SIZES if value != chosen)

    input_rows = _sample_inputs(seed, n_train + n_test)
    rules = {value: emit_rule(value) for value in STEP_SIZES}
    outputs: dict[int, list[list[list[int]]]] = {value: [] for value in STEP_SIZES}
    parity_count = 0
    manager = nullcontext(bridge) if bridge is not None else open_verifier()
    with manager as verifier:
        if verifier is None:
            raise AssertionError("missing Racket verifier")
        for candidate in input_rows:
            grid = candidate["input"]
            for value in STEP_SIZES:
                racket_output = verifier.apply(rules[value], grid)
                python_output = apply_python(grid, value)
                if racket_output != python_output:
                    raise AssertionError(
                        f"Racket/Python mismatch for step_size={value}, "
                        f"input={candidate['input_sha256']}"
                    )
                parity_count += 1
                outputs[value].append(racket_output)

    pairs: list[dict[str, Any]] = []
    for index, candidate in enumerate(input_rows):
        chosen_output = outputs[chosen][index]
        rival_output = outputs[rival][index]
        if chosen_output == rival_output:
            raise AssertionError(
                f"input {candidate['input_sha256']} does not distinguish step sizes"
            )
        pairs.append(
            {
                "pair_index": index,
                "step_size": chosen,
                "input": candidate["input"],
                "output": chosen_output,
                "input_sha256": candidate["input_sha256"],
                "output_sha256": _grid_sha256(chosen_output),
                "rival_step_size": rival,
                "rival_output_sha256": _grid_sha256(rival_output),
                "generation": candidate["generation"],
            }
        )

    demo_refutations = [
        index
        for index in range(n_train)
        if outputs[chosen][index] != outputs[rival][index]
    ]
    surviving = [chosen] if demo_refutations else [chosen, rival]
    query_rows = []
    for query_offset, pair_index in enumerate(range(n_train, n_train + n_test)):
        query_rows.append(
            {
                "query_index": query_offset,
                "input_sha256": input_rows[pair_index]["input_sha256"],
                "rival_step_size": rival,
                "rival_differs": outputs[chosen][pair_index]
                != outputs[rival][pair_index],
                "chosen_output_sha256": _grid_sha256(outputs[chosen][pair_index]),
                "rival_output_sha256": _grid_sha256(outputs[rival][pair_index]),
            }
        )

    generator, source_path, source_sha256 = _generator_record()
    del generator
    selected_rule = rules[chosen]
    return {
        "schema": "arcpuzzles-parametric-step-size-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": {"step_size": chosen},
        "parameter_selection": selection,
        "input_constraints_depend_on_parameter": False,
        "n_train": n_train,
        "n_test": n_test,
        "generator_source": {
            "path": source_path.relative_to(ROOT).as_posix(),
            "sha256": source_sha256,
        },
        "racket_source": selected_rule,
        "racket_sha256": _sha256_bytes(selected_rule.encode("utf-8")),
        "rival_racket_sha256": _sha256_bytes(rules[rival].encode("utf-8")),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "analysis": {
            "declared_settings": list(STEP_SIZES),
            "identified_from_demonstrations": surviving == [chosen],
            "surviving_step_sizes_after_demos": surviving,
            "demo_refutation_indices": demo_refutations,
            "queries": query_rows,
            "query_answers_used_for_identification": False,
        },
        "verification": {
            "label_authority": "RacketBridge",
            "racket_python_parity_count": parity_count,
            "all_inputs_distinguish_declared_settings": all(
                row["rival_differs"] for row in query_rows
            )
            and len(demo_refutations) == n_train,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project exactly the visible demonstrations and unlabeled query inputs."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def visible_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def visible_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def materialize(
    *,
    seed: int,
    step_size: int | None,
    all_settings: bool,
    n_train: int,
    n_test: int,
    out: Path | str,
) -> dict[str, Any]:
    """Write public challenges and separate private controller evidence."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    if type(all_settings) is not bool:
        raise ValueError("all_settings must be a boolean")
    if all_settings and step_size is not None:
        raise ValueError("all_settings cannot be combined with step_size")
    if step_size is not None:
        validate_step_size(step_size)

    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("out must not exist or must be an empty directory")
    out.mkdir(parents=True, exist_ok=True)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)

    requested = STEP_SIZES if all_settings else (step_size,)
    episodes: list[dict[str, Any]] = []
    with open_verifier() as verifier:
        for requested_step in requested:
            episodes.append(
                make_episode(
                    seed,
                    step_size=requested_step,
                    n_train=n_train,
                    n_test=n_test,
                    bridge=verifier,
                )
            )

    public_rows = sorted(
        ((visible_id(episode), visible_bytes(episode), episode) for episode in episodes),
        key=lambda row: row[0],
    )
    public_ids: list[str] = []
    private_rows: list[dict[str, Any]] = []
    for index, (public_id, raw, episode) in enumerate(public_rows, start=1):
        if _sha256_bytes(raw) != public_id:
            raise AssertionError("public identifier is not the exact visible-byte hash")
        if public_id in public_ids:
            raise ValueError("duplicate visible payload across requested episodes")
        public_ids.append(public_id)
        public_path = out / "public" / f"challenge-{public_id}.json"
        public_path.write_bytes(raw)

        private = dict(episode)
        private["public_id"] = public_id
        private["public_path"] = public_path.relative_to(out).as_posix()
        private_path = out / "private" / f"episode-{index:03d}.json"
        _write_json(private_path, private)
        private_rows.append(private)

        rule_path = out / "private/rules" / f"rule-{episode['racket_sha256']}.rkt"
        if not rule_path.exists():
            rule_path.write_bytes(episode["racket_source"].encode("utf-8"))

    same_inputs = True
    outputs_differ = False
    if len(private_rows) > 1:
        first_hashes = [
            pair["input_sha256"]
            for pair in [*private_rows[0]["train"], *private_rows[0]["test"]]
        ]
        for episode in private_rows[1:]:
            hashes = [
                pair["input_sha256"]
                for pair in [*episode["train"], *episode["test"]]
            ]
            same_inputs = same_inputs and hashes == first_hashes
        outputs_differ = all(
            left["output_sha256"] != right["output_sha256"]
            for left, right in zip(
                [*private_rows[0]["train"], *private_rows[0]["test"]],
                [*private_rows[1]["train"], *private_rows[1]["test"]],
                strict=True,
            )
        )

    prototype_path = Path(__file__).resolve()
    report = {
        "schema": "arcpuzzles-parametric-step-size-report-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "seed": seed,
        "n_train": n_train,
        "n_test": n_test,
        "episode_count": len(episodes),
        "public_ids": public_ids,
        "step_sizes": [row["parameters"]["step_size"] for row in private_rows],
        "cross_setting_same_inputs": same_inputs,
        "cross_setting_outputs_differ": outputs_differ,
        "all_identified_from_demonstrations": all(
            row["analysis"]["identified_from_demonstrations"]
            for row in private_rows
        ),
        "all_queries_refute_rival": all(
            query["rival_differs"]
            for row in private_rows
            for query in row["analysis"]["queries"]
        ),
        "source_hashes": {
            "prototype.py": _sha256_bytes(prototype_path.read_bytes()),
            "canonical_rule": _sha256_bytes(canonical_rule().encode("utf-8")),
            "generator.py": private_rows[0]["generator_source"]["sha256"],
        },
        "limitations": [
            "Identifiability is checked only against the declared step sizes 1 and 2.",
            "Inputs remain within the selected generator's 9..20 by 9..22 domain.",
            "The prototype is separate from production approval and training admission.",
        ],
    }
    _write_json(out / "report.json", report)

    manifest_rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        manifest_rows.append(
            {
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
        )
    _write_json(
        out / "manifest.json",
        {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "files": manifest_rows,
        },
    )
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--step-size", type=int, default=None)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--n-train", type=int, default=4)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = materialize(
        seed=args.seed,
        step_size=args.step_size,
        all_settings=args.all_settings,
        n_train=args.n_train,
        n_test=args.n_test,
        out=args.out,
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Isolated projection-polarity prototype for ARC task e937c5b85cdd.

The selected generator and canonical authority remain unchanged.  This proposal
adds one bounded episode-level parameter: whether each cross paints the frame
cell opposite its longest arm (the original rule) or the frame cell facing its
longest arm.  Every retained label is produced by applying an exact materialized
Racket program through the packet's protected Racket bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "e937c5b85cdd"
PARAMETER = "projection_polarity"
PROJECTION_POLARITIES = ("opposite", "facing")
CANONICAL_DEFAULT = "opposite"
PROTOTYPE_VERSION = "projection-polarity-v1"
CANONICAL_TEXT_SHA256 = (
    "ab0d4ff4a785fc9cfe6a0ad81dea9daab643a1c1d32fd5cd9d26aa231649c94c"
)
N_TRAIN = 3
N_TEST = 1

# The only transformation site changed by the alternative.  Keeping this as one
# exact source fragment makes canonical drift or a second ambiguous edit point
# fail closed instead of silently creating a different rule.
_CANONICAL_ACTIONS = """                             (cond
                               ((= max-arm up) (hash-set! result (list 0 cc) 0))
                               ((= max-arm dn) (hash-set! result (list (- hh 1) cc) 0))
                               ((= max-arm lt) (hash-set! result (list cr 0) 0))
                               ((= max-arm rt) (hash-set! result (list cr (- ww 1)) 0)))
                             (cond
                               ((= max-arm up) (hash-set! result (list (- hh 1) cc) color))
                               ((= max-arm dn) (hash-set! result (list 0 cc) color))
                               ((= max-arm lt) (hash-set! result (list cr (- ww 1)) color))
                               ((= max-arm rt) (hash-set! result (list cr 0) color)))"""

_FACING_ACTIONS = """                             (cond
                               ((= max-arm up) (hash-set! result (list (- hh 1) cc) 0))
                               ((= max-arm dn) (hash-set! result (list 0 cc) 0))
                               ((= max-arm lt) (hash-set! result (list cr (- ww 1)) 0))
                               ((= max-arm rt) (hash-set! result (list cr 0) 0)))
                             (cond
                               ((= max-arm up) (hash-set! result (list 0 cc) color))
                               ((= max-arm dn) (hash-set! result (list (- hh 1) cc) color))
                               ((= max-arm lt) (hash-set! result (list cr 0) color))
                               ((= max-arm rt) (hash-set! result (list cr (- ww 1)) color)))"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return _sha256_bytes(payload)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer (not bool)")
    return seed


def validate_projection_polarity(value: Any) -> str:
    if type(value) is not str or value not in PROJECTION_POLARITIES:
        raise ValueError(
            f"projection_polarity must be one of {PROJECTION_POLARITIES}, got {value!r}"
        )
    return value


def choose_projection_polarity(seed: Any) -> str:
    """Choose the hidden transformation once for the complete episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{seed}".encode()).digest()
    return PROJECTION_POLARITIES[int.from_bytes(digest[:8], "big") % 2]


def canonical_program(*, root: Path | str | None = None) -> str:
    root_path = Path(root).resolve() if root is not None else find_root(__file__)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"canonical row for {TASK_ID} has no program_solution")
                sources.add(program)
    if len(sources) != 1:
        raise ValueError(
            f"prototype requires one unambiguous canonical program, found {len(sources)}"
        )
    source = sources.pop()
    actual = _sha256_text(source)
    if actual != CANONICAL_TEXT_SHA256:
        raise ValueError(
            "canonical program changed; review the projection edit point again "
            f"({actual} != {CANONICAL_TEXT_SHA256})"
        )
    return source


def program_for(
    projection_polarity: Any = CANONICAL_DEFAULT,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact original rule or its one-site polarity variant."""
    selected = validate_projection_polarity(projection_polarity)
    source = canonical_program(root=root)
    count = source.count(_CANONICAL_ACTIONS)
    if count != 1:
        raise ValueError(
            f"canonical rule drift: expected one projection action block, found {count}"
        )
    if _FACING_ACTIONS in source:
        raise ValueError("canonical rule unexpectedly already contains the alternative block")
    if selected == CANONICAL_DEFAULT:
        return source
    return source.replace(_CANONICAL_ACTIONS, _FACING_ACTIONS, 1)


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule! "
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be one plain (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def execute_outputs(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
) -> list[list[list[int]]]:
    """Apply one exact materialized Racket lambda to each supplied grid."""
    body = _rule_body(program)
    outputs: list[list[list[int]]] = []
    for grid in grids:
        normalized = normalize_grid(grid)
        bridge.define_grid("parametric_input", normalized)
        # Evaluating BODY alone would serialize a procedure descriptor.  Apply
        # the lambda explicitly so every retained value is an executed label.
        result = bridge.eval_text(f"({body} parametric_input)")
        outputs.append(normalize_grid(result))
    return outputs


def episode_inputs(
    seed: Any,
    *,
    root: Path | str | None = None,
) -> tuple[list[list[list[int]]], str, str]:
    """Draw one deterministic four-profile episode from the selected generator."""
    seed = _validate_seed(seed)
    root_path = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root_path
    )
    grids = [
        normalize_grid(generator.generate(seed, index, difficulty="medium"))
        for index in range(N_TRAIN + N_TEST)
    ]
    return grids, str(generator_path), generator_sha


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden parameter, Racket source, and query label."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def build_episode(
    seed: Any,
    *,
    bridge: RacketBridge,
    root: Path | str | None = None,
    projection_polarity: Any | None = None,
) -> dict[str, Any]:
    """Build a complete, parameter-consistent, Racket-labeled episode."""
    seed = _validate_seed(seed)
    selected = (
        choose_projection_polarity(seed)
        if projection_polarity is None
        else validate_projection_polarity(projection_polarity)
    )
    rival = next(value for value in PROJECTION_POLARITIES if value != selected)
    root_path = Path(root).resolve() if root is not None else find_root(__file__)
    grids, generator_path, generator_sha = episode_inputs(seed, root=root_path)
    selected_program = program_for(selected, root=root_path)
    rival_program = program_for(rival, root=root_path)
    selected_outputs = execute_outputs(bridge, selected_program, grids)
    rival_outputs = execute_outputs(bridge, rival_program, grids)
    pairs = [
        {"input": copy.deepcopy(grid), "output": output}
        for grid, output in zip(grids, selected_outputs, strict=True)
    ]
    differing_train = [
        index
        for index in range(N_TRAIN)
        if selected_outputs[index] != rival_outputs[index]
    ]
    query_differs = selected_outputs[N_TRAIN] != rival_outputs[N_TRAIN]
    status = "refuted_by_demonstrations" if differing_train else "ambiguous"
    return {
        "schema": "e937c5b85cdd-parametric-episode-v1",
        "scope": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_selection": (
            "seeded_once" if projection_polarity is None else "explicit_once"
        ),
        "parameters": {PARAMETER: selected},
        "generator_path": generator_path,
        "generator_sha256": generator_sha,
        "program": selected_program,
        "program_sha256": _sha256_text(selected_program),
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "input_sha256": [_sha256_json(grid) for grid in grids],
        "rival": {
            "parameters": {PARAMETER: rival},
            "program": rival_program,
            "program_sha256": _sha256_text(rival_program),
            "predictions": rival_outputs,
            "status": status,
            "differing_train_indices": differing_train,
            "query_differs": query_differs,
        },
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _seed_for_setting(setting: str, start: int, used: set[int]) -> int:
    setting = validate_projection_polarity(setting)
    seed = _validate_seed(start)
    while seed in used or choose_projection_polarity(seed) != setting:
        seed += 1
    return seed


def materialize(
    out_dir: Path | str,
    *,
    seed_start: int = 731,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute both settings and retain public/private, hash-bound evidence."""
    seed_start = _validate_seed(seed_start)
    output = Path(out_dir)
    if output.exists():
        raise FileExistsError(
            f"refusing to overwrite existing evidence directory: {output}"
        )
    output.mkdir(parents=True)
    root_path = Path(root).resolve() if root is not None else find_root(__file__)

    programs = {
        setting: program_for(setting, root=root_path)
        for setting in PROJECTION_POLARITIES
    }
    for setting, program in programs.items():
        rule_path = output / "private" / "rules" / f"{setting}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(
            program + ("" if program.endswith("\n") else "\n"), encoding="utf-8"
        )

    summaries: list[dict[str, Any]] = []
    private_episodes: list[dict[str, Any]] = []
    used: set[int] = set()
    with RacketBridge(
        timeout=30, startup_timeout=60, max_calls_before_restart=128
    ) as bridge:
        for index, setting in enumerate(PROJECTION_POLARITIES):
            seed = _seed_for_setting(setting, seed_start + index, used)
            used.add(seed)
            episode = build_episode(seed, bridge=bridge, root=root_path)
            if episode["parameters"][PARAMETER] != setting:
                raise AssertionError("seed search returned the wrong parameter setting")
            if episode["rival"]["status"] != "refuted_by_demonstrations":
                raise AssertionError("demonstrations do not identify the selected setting")
            if not episode["rival"]["query_differs"]:
                raise AssertionError("query does not require the selected setting")

            public = public_challenge(episode)
            public_path = Path("public") / f"episode-{index:03d}.json"
            private_path = Path("private") / f"episode-{index:03d}.json"
            _write_json(output / public_path, public)
            _write_json(output / private_path, episode)
            private_episodes.append(episode)
            summaries.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "generator_sha256": episode["generator_sha256"],
                    "program_sha256": episode["program_sha256"],
                    "rival_status": episode["rival"]["status"],
                    "differing_train_indices": episode["rival"][
                        "differing_train_indices"
                    ],
                    "query_differs": episode["rival"]["query_differs"],
                    "public_path": public_path.as_posix(),
                    "private_path": private_path.as_posix(),
                    "public_sha256": _sha256_json(public),
                }
            )

        witness_input = private_episodes[0]["train"][0]["input"]
        witness_outputs = {
            setting: execute_outputs(bridge, programs[setting], [witness_input])[0]
            for setting in PROJECTION_POLARITIES
        }
    witness = {
        "input": witness_input,
        "outputs": witness_outputs,
        "outputs_differ": witness_outputs["opposite"] != witness_outputs["facing"],
    }
    if not witness["outputs_differ"]:
        raise AssertionError("retained parameter witness does not distinguish settings")
    _write_json(output / "private" / "differing-witness.json", witness)

    source_path = Path(__file__).resolve()
    report = {
        "schema": "e937c5b85cdd-parametric-evidence-v1",
        "status": "passed",
        "scope": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(PROJECTION_POLARITIES),
            "original_default": CANONICAL_DEFAULT,
            "selected_once_per_episode": True,
            "semantics": {
                "opposite": (
                    "clear the frame cell facing each longest arm and paint the "
                    "opposite frame cell with the cross color"
                ),
                "facing": (
                    "clear the opposite frame cell and paint the frame cell facing "
                    "each longest arm with the cross color"
                ),
            },
            "input_constraints": (
                "Inputs retain the selected generator's collision-free framed-cross "
                "grammar; only the executed frame-projection polarity changes."
            ),
        },
        "canonical_program_sha256": CANONICAL_TEXT_SHA256,
        "prototype_source": str(source_path),
        "prototype_source_sha256": _sha256_bytes(source_path.read_bytes()),
        "episodes": summaries,
        "differing_witness": "private/differing-witness.json",
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric/projection-polarity-v1",
        ],
        "limitations": [
            "This is an isolated proposal; canonical authority, RULE_HASH, and the selected generator's output rule remain the original opposite projection.",
            "Evidence covers two deterministic four-pair episodes and one declared rival, not every seed or every conceivable rule family.",
            "The polarity is intentionally identifiable from any lawful nonempty demonstration; this prototype tests coherent episode-level parameterization, not difficult latent-rule inference.",
        ],
    }
    _write_json(output / "report.json", report)

    files = {
        path.relative_to(output).as_posix(): _sha256_bytes(path.read_bytes())
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema": "e937c5b85cdd-parametric-manifest-v1",
        "scope": "prototype",
        "files": files,
    }
    _write_json(output / "manifest.json", manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=731)
    args = parser.parse_args()
    report = materialize(args.out, seed_start=args.seed_start)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

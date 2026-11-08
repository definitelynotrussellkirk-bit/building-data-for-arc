#!/usr/bin/env python3
"""Proposed episode-level destination-decoder variants for c5905adcd2cb.

This is a bounded authoring prototype. It does not change the selected
canonical generator, authority, catalog entry, or approval state.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys

# Bind to the source tree containing this file. Do not use cwd or a sibling tree.
for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break

from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

TASK_ID = "c5905adcd2cb"
ROOT = find_root(__file__)
GENERATOR, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DEFAULT_DESTINATION_DECODER = "direct"
ALLOWED_DESTINATION_DECODERS = ("direct", "transpose")
RULE_WRAPPER = "(define (rule! f) f)"
PROFILE_CYCLE = (
    "empty_destination",
    "dense_destination",
    "same_destination",
    "full_source",
    "light_destination",
    "marker_only",
)
LIMITATIONS = [
    "Proposed prototype only; canonical production generation and approval are unchanged.",
    "Only direct and transposed destination-coordinate decoding are in scope.",
    "Inputs retain the canonical 11x11 lattice grammar and color-4 marker encoding.",
    "The demonstrations distinguish only the two declared settings, not every possible program.",
    "Evidence is finite, seed-bound, and source-bound rather than a proof over all episodes.",
    "The narrow rule! adapter supports these declared lambda programs only.",
]


def _canonical_program() -> str:
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("source") == "training":
            rows.append(row["program_solution"])
    if len(rows) != 1:
        raise ValueError(f"expected one training authority for {TASK_ID}, found {len(rows)}")
    return rows[0]


def programs() -> dict[str, str]:
    """Return exact direct authority and one nearby transposed decoder program."""
    direct = _canonical_program()
    old = """                (dst-r1 (* (- fr src-r1) 4))
                (dst-c1 (* (- fc src-c1) 4))"""
    new = """                (dst-r1 (* (- fc src-c1) 4))
                (dst-c1 (* (- fr src-r1) 4))"""
    if direct.count(old) != 1:
        raise ValueError("canonical destination bindings no longer match prototype transform")
    transpose = direct.replace(old, new, 1)
    return {"direct": direct, "transpose": transpose}


def open_bridge() -> RacketBridge:
    """Open the included Racket bridge and install the narrow rule! adapter."""
    bridge = RacketBridge()
    try:
        bridge.eval_text(RULE_WRAPPER)
    except BaseException:
        bridge.shutdown()
        raise
    return bridge


def execute(bridge: RacketBridge, destination_decoder: str, grids: list[list[list[int]]]):
    """Execute one exact declared Racket program over every supplied grid."""
    declared = programs()
    if destination_decoder not in declared:
        raise ValueError(
            f"destination_decoder must be one of {ALLOWED_DESTINATION_DECODERS}, "
            f"got {destination_decoder!r}"
        )
    bridge.eval_text(f"(define prototype-rule {declared[destination_decoder]})")
    outputs = []
    for grid in grids:
        bridge.define_grid("prototype-input", normalize_grid(grid))
        outputs.append(normalize_grid(bridge.eval_text("(prototype-rule prototype-input)")))
    return outputs


def destination_coordinates(grid: list[list[int]]) -> tuple[int, int]:
    """Return the canonical local row/column encoded by the first yellow marker."""
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 4:
                source_row = row // 4 * 4
                source_col = col // 4 * 4
                return row - source_row, col - source_col
    raise ValueError("grid has no color-4 marker")


def _draw_inputs(rng: random.Random, *, n_train: int, n_test: int):
    """Draw independent lawful inputs; every demonstration uses an off-diagonal code."""
    grids = []
    metadata = []
    seen = set()
    total = n_train + n_test
    profile_offset = rng.randrange(len(PROFILE_CYCLE))
    for slot in range(total):
        profile = PROFILE_CYCLE[(profile_offset + slot) % len(PROFILE_CYCLE)]
        difficulty = ("easy", "medium", "hard")[slot % 3]
        require_off_diagonal = slot < n_train
        for attempt in range(400):
            generator_seed = rng.randrange(0, 2**32)
            sample_index = rng.randrange(0, 2**31)
            grid = GENERATOR.generate(
                generator_seed,
                sample_index,
                difficulty=difficulty,
                scene_profile=profile,
            )
            frozen = tuple(tuple(row) for row in grid)
            local_row, local_col = destination_coordinates(grid)
            if frozen in seen:
                continue
            if require_off_diagonal and local_row == local_col:
                continue
            seen.add(frozen)
            grids.append(grid)
            metadata.append(
                {
                    "slot": slot,
                    "profile": profile,
                    "difficulty": difficulty,
                    "generator_seed": generator_seed,
                    "sample_index": sample_index,
                    "canonical_destination": [local_row, local_col],
                    "attempt": attempt,
                }
            )
            break
        else:
            raise RuntimeError(
                f"could not draw unique {'off-diagonal ' if require_off_diagonal else ''}"
                f"input for slot {slot}"
            )
    return grids, metadata


def assess_episode(bridge: RacketBridge, episode: dict) -> dict:
    """Run both parameter settings; infer survivors from demonstrations only."""
    pairs = episode["train"] + episode["test"]
    split = len(episode["train"])
    rivals = {}
    for setting in ALLOWED_DESTINATION_DECODERS:
        outputs = execute(bridge, setting, [pair["input"] for pair in pairs])
        matches = [actual == pair["output"] for actual, pair in zip(outputs, pairs)]
        rivals[setting] = {
            "outputs": outputs,
            "demo_matches": matches[:split],
            "query_matches": matches[split:],
            "demo_consistent": all(matches[:split]),
            "full_episode_consistent": all(matches),
        }
    survivors = [
        setting for setting in ALLOWED_DESTINATION_DECODERS
        if rivals[setting]["demo_consistent"]
    ]
    return {
        "rivals": rivals,
        "demo_survivors": survivors,
        "identifiable_from_demos": len(survivors) == 1,
    }


def build_episode(
    bridge: RacketBridge,
    *,
    seed: int,
    destination_decoder: str | None = None,
    n_train: int = 3,
    n_test: int = 2,
) -> dict:
    """Choose one hidden decoder, then label a complete episode with its Racket."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if type(n_train) is not int or not 1 <= n_train <= 20:
        raise ValueError("n_train must be a literal integer in 1..20")
    if type(n_test) is not int or not 1 <= n_test <= 20:
        raise ValueError("n_test must be a literal integer in 1..20")
    if destination_decoder is not None and destination_decoder not in ALLOWED_DESTINATION_DECODERS:
        raise ValueError(f"unknown destination_decoder: {destination_decoder!r}")

    rng = random.Random(seed)
    selected = rng.choice(ALLOWED_DESTINATION_DECODERS)
    if destination_decoder is not None:
        selected = destination_decoder
    grids, input_metadata = _draw_inputs(rng, n_train=n_train, n_test=n_test)
    outputs = execute(bridge, selected, grids)
    pairs = [
        {"input": deepcopy(grid), "output": output}
        for grid, output in zip(grids, outputs)
    ]
    source = programs()[selected]
    episode = {
        "schema": "c5905adcd2cb-parametric-destination-decoder-episode-v1",
        "seed": seed,
        "destination_decoder": selected,
        "program": source,
        "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "input_metadata": input_metadata,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }
    episode["rival_check"] = assess_episode(bridge, episode)
    if episode["rival_check"]["demo_survivors"] != [selected]:
        raise ValueError(
            "demonstrations do not uniquely distinguish the selected destination decoder"
        )
    return episode


def public_challenge(episode: dict) -> dict:
    """Strip seed, hidden setting, programs, provenance, and query labels."""
    return deepcopy(
        {
            "train": episode["train"],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    runtime = Path(sys.modules["arc_repl.racket_bridge"].__file__).resolve().parent
    files = [
        Path(__file__).resolve(),
        GENERATOR_SOURCE.resolve(),
        canonical_path(ROOT).resolve(),
        Path(sys.modules["reviewer_support"].__file__).resolve(),
        runtime / "racket_bridge.py",
        runtime / "racket_prelude/arc-prelude.rkt",
    ]
    return {str(path.relative_to(ROOT)): _sha256(path) for path in files}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument(
        "--destination-decoder",
        choices=ALLOWED_DESTINATION_DECODERS,
        default=None,
        help="optional explicit setting for every requested episode",
    )
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out.exists():
        parser.error("--out must not already exist")

    with open_bridge() as bridge:
        episodes = [
            build_episode(
                bridge,
                seed=seed,
                destination_decoder=args.destination_decoder,
            )
            for seed in args.seeds
        ]
        witness = episodes[0]["train"][0]["input"]
        witness_outputs = {
            setting: execute(bridge, setting, [witness])[0]
            for setting in ALLOWED_DESTINATION_DECODERS
        }

    public_dir = out / "public"
    private_dir = out / "private"
    programs_dir = out / "programs"
    public_dir.mkdir(parents=True)
    private_dir.mkdir()
    programs_dir.mkdir()

    files = []
    for setting, source in programs().items():
        path = programs_dir / f"{setting}.rkt"
        path.write_text(source + "\n")
        files.append({"path": str(path.relative_to(out)), "sha256": _sha256(path)})
    for index, episode in enumerate(episodes):
        name = f"episode-{index:03d}.json"
        for folder, payload in (
            (public_dir, public_challenge(episode)),
            (private_dir, episode),
        ):
            path = folder / name
            _write_json(path, payload)
            files.append({"path": str(path.relative_to(out)), "sha256": _sha256(path)})

    declared_programs = programs()
    evidence = {
        "schema": "c5905adcd2cb-parametric-destination-decoder-evidence-v1",
        "status": "proposed prototype; not production approval",
        "parameter": {
            "name": "destination_decoder",
            "allowed": list(ALLOWED_DESTINATION_DECODERS),
            "original_default": DEFAULT_DESTINATION_DECODER,
            "selection": "random.Random(seed).choice once per episode unless explicitly overridden",
            "direct": "marker local (row, col) selects destination macro (row, col)",
            "transpose": "marker local (row, col) selects destination macro (col, row)",
            "input_constraints_depend_on_parameter": False,
        },
        "invariants": [
            "marker quotient coordinates select the source macro-cell",
            "all non-gray cells are cleared before copying",
            "all nonzero/non-gray source cells, including marker 4, are copied",
            "source-local offsets are preserved inside the selected destination",
        ],
        "programs": {
            setting: {
                "text": source,
                "sha256": hashlib.sha256(source.encode()).hexdigest(),
            }
            for setting, source in declared_programs.items()
        },
        "rule_wrapper": RULE_WRAPPER,
        "rule_wrapper_sha256": hashlib.sha256(RULE_WRAPPER.encode()).hexdigest(),
        "selected_generator": {
            "path": str(GENERATOR_SOURCE.relative_to(ROOT)),
            "sha256": GENERATOR_SHA256,
        },
        "source_sha256": source_hashes(),
        "racket_runtime": racket_runtime_status(),
        "payload_command": [sys.executable, str(Path(__file__).relative_to(ROOT)), *sys.argv[1:]],
        "episodes": len(episodes),
        "demonstrations": sum(len(episode["train"]) for episode in episodes),
        "queries": sum(len(episode["test"]) for episode in episodes),
        "settings_exercised": sorted({episode["destination_decoder"] for episode in episodes}),
        "identifiable_episodes": sum(
            episode["rival_check"]["identifiable_from_demos"] for episode in episodes
        ),
        "shared_witness": {
            "input": witness,
            "canonical_destination": list(destination_coordinates(witness)),
            "outputs": witness_outputs,
            "distinct": witness_outputs["direct"] != witness_outputs["transpose"],
        },
        "files": files,
        "limitations": LIMITATIONS,
    }
    evidence_path = private_dir / "evidence.json"
    _write_json(evidence_path, evidence)
    print(
        json.dumps(
            {
                "out": str(out),
                "episodes": len(episodes),
                "settings": evidence["settings_exercised"],
                "identifiable": evidence["identifiable_episodes"],
                "witness_distinct": evidence["shared_witness"]["distinct"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

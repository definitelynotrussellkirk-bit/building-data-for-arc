"""Task-local parametric rule prototype for ARC family f1bcbc2c.

The canonical production generator and authority remain unchanged.  This module
materializes a nearby episode-level rule parameter:

``turn_half = larger`` (canonical) or ``turn_half = smaller``.

Only the bend-marker branch changes.  The no-marker and straight-marker branches,
latent channel selection, orange-wall geometry, marker role, and cyan output color
stay identical.  The parameter is chosen once per episode, and demonstrations
include turn-marker witnesses before a turn-marker query requires the choice.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Iterable

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
TASK_HOME = WORKSPACE.parent
REPO_ROOT = TASK_HOME.parents[1]
TASK_ID = "b9e736518d82"
TURN_POLICIES = ("larger", "smaller")
DEFAULT_TURN_POLICY = "larger"
PARAMETERS = {
    "turn_half": {
        "type": "enum",
        "allowed": list(TURN_POLICIES),
        "default": DEFAULT_TURN_POLICY,
        "canonical": DEFAULT_TURN_POLICY,
        "meaning": "which unequal component adjacent to a bend marker is recolored cyan",
        "input_constraints": "turn-marker examples must split the selected channel into unequal halves",
    }
}

if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
from reference_probe import authority_channel, canonical_program, load_generator  # noqa: E402

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TURN_COMPARISON = "> (length half1) (length half2)"
_PAIR_SPECS = (
    {"marker_mode": "none", "grid_h": 10, "grid_w": 10, "turn_count": 4},
    {"marker_mode": "straight", "grid_h": 12, "grid_w": 10, "turn_count": 3},
    {"marker_mode": "turn", "grid_h": 10, "grid_w": 12, "turn_count": 4},
    {"marker_mode": "turn", "grid_h": 14, "grid_w": 11, "turn_count": 5},
    {"marker_mode": "turn", "grid_h": 11, "grid_w": 14, "turn_count": 4},
)


def _validate_policy(policy: str) -> None:
    if type(policy) is not str or policy not in TURN_POLICIES:
        raise ValueError(f"turn_half must be one of {TURN_POLICIES}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise ValueError("episode seed must be an integer")


def _neighbors(point: tuple[int, int]) -> Iterable[tuple[int, int]]:
    row, col = point
    for row_step, col_step in _CARDINAL:
        yield row + row_step, col + col_step


def _component(start: tuple[int, int], pool: set[tuple[int, int]]) -> set[tuple[int, int]]:
    visited = {start}
    queue = deque([start])
    while queue:
        point = queue.popleft()
        for neighbor in _neighbors(point):
            if neighbor in pool and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited


def normalized_program_hash(program: str) -> str:
    """Return the repository's normalized twelve-hex Racket authority hash."""
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def full_program_hash(program: str) -> str:
    return hashlib.sha256(program.encode()).hexdigest()


def program_for(turn_policy: str) -> str:
    """Materialize exact Racket for one parameter setting."""
    _validate_policy(turn_policy)
    program = canonical_program()
    if program.count(_TURN_COMPARISON) != 1:
        raise ValueError("canonical program no longer has one identifiable turn-half comparison")
    if turn_policy == "larger":
        return program
    return program.replace(
        _TURN_COMPARISON,
        "< (length half1) (length half2)",
        1,
    )


def other_policy(turn_policy: str) -> str:
    _validate_policy(turn_policy)
    return "smaller" if turn_policy == "larger" else "larger"


def _episode_policy(seed: int) -> str:
    digest = hashlib.sha256(f"{TASK_ID}:turn_half:{seed}".encode()).digest()
    return TURN_POLICIES[digest[0] % len(TURN_POLICIES)]


def _pair_seed(seed: int, pair_index: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}:pair:{seed}:{pair_index}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % (2**31 - 1)


def _marker_kind(grid, channel: set[tuple[int, int]]) -> str:
    marker = next((point for point in channel if grid[point[0]][point[1]] == 9), None)
    if marker is None:
        return "none"
    neighbors = [point for point in _neighbors(marker) if point in channel]
    same_col = all(point[1] == marker[1] for point in neighbors)
    same_row = all(point[0] == marker[0] for point in neighbors)
    return "straight" if same_col or same_row else "turn"


def apply_policy(grid: list[list[int]], turn_policy: str) -> list[list[int]]:
    """Python mirror used only for prototype tests; Racket supplies evidence labels."""
    _validate_policy(turn_policy)
    channel = authority_channel(grid)
    marker = next((point for point in channel if grid[point[0]][point[1]] == 9), None)
    if marker is None or _marker_kind(grid, channel) == "straight":
        fill = channel
    else:
        without_marker = channel - {marker}
        first_half = _component(min(without_marker), without_marker)
        second_half = without_marker - first_half
        if len(first_half) == len(second_half):
            raise ValueError("turn_half prototype requires unequal marker halves")
        first_is_selected = (
            len(first_half) > len(second_half)
            if turn_policy == "larger"
            else len(first_half) < len(second_half)
        )
        fill = first_half if first_is_selected else second_half

    output = deepcopy(grid)
    for row, col in fill:
        output[row][col] = 8
    return output


def generate_episode(
    seed: int,
    *,
    turn_policy: str | None = None,
    difficulty: str | None = "medium",
) -> dict:
    """Build a complete 4-demo/1-query episode with one fixed hidden policy."""
    _validate_seed(seed)
    policy = _episode_policy(seed) if turn_policy is None else turn_policy
    _validate_policy(policy)
    generator = load_generator()
    pairs: list[dict] = []
    for index, options in enumerate(_PAIR_SPECS):
        grid = generator.generate(
            _pair_seed(seed, index),
            100 + index,
            difficulty=difficulty,
            **options,
        )
        pairs.append({"input": grid, "output": apply_policy(grid, policy)})

    episode = {
        "train": pairs[:4],
        "test": pairs[4:],
        "program": program_for(policy),
        "chain": [
            "find_adjacent_orange_channel",
            "interpret_optional_marker",
            f"fill_{policy}_turn_half",
        ],
        "meta": {
            "prototype": True,
            "task_id": TASK_ID,
            "episode_seed": seed,
            "turn_policy": policy,
            "parameter_scope": "one fixed setting for every pair in this episode",
            "canonical_production_unchanged": True,
        },
    }
    return episode


def public_challenge(episode: dict) -> dict:
    """Strip hidden semantics, Racket, metadata, and query answers."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute an exact materialized program with the packet's real Racket bridge."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
        request = {"program": program, "grids": grids}
        (stage / "request.json").write_text(json.dumps(request))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                "Racket worker failed: "
                + result.get("stderr", "")
                + "\n"
                + result.get("stdout", "")
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete output batch")
        return outputs


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_evidence(seed: int, examples_dir: Path) -> dict:
    """Execute both settings and retain complete, source-bound evidence."""
    examples_dir.mkdir(parents=True, exist_ok=True)
    settings: dict[str, dict] = {}
    public_names = {"larger": "episode-a.json", "smaller": "episode-b.json"}

    for policy in TURN_POLICIES:
        episode = generate_episode(seed, turn_policy=policy)
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        program = episode["program"]
        executed = racket_outputs(program, inputs)
        if executed != expected:
            mismatches = [
                index
                for index, (actual, wanted) in enumerate(zip(executed, expected))
                if actual != wanted
            ]
            raise RuntimeError(f"Racket/Python mismatch for {policy}: {mismatches}")

        rival = other_policy(policy)
        train_disagreements = [
            index
            for index, pair in enumerate(episode["train"])
            if apply_policy(pair["input"], rival) != pair["output"]
        ]
        query_disagreements = [
            index
            for index, pair in enumerate(episode["test"])
            if apply_policy(pair["input"], rival) != pair["output"]
        ]
        if not train_disagreements or not query_disagreements:
            raise RuntimeError(f"episode for {policy} does not distinguish rival {rival}")

        public_path = examples_dir / public_names[policy]
        public_path.write_text(json.dumps(public_challenge(episode), indent=2) + "\n")
        settings[policy] = {
            "parameter": {"turn_half": policy},
            "program": program,
            "program_sha256": full_program_hash(program),
            "normalized_program_hash": normalized_program_hash(program),
            "episode": episode,
            "public_challenge_path": str(public_path.relative_to(REPO_ROOT)),
            "public_challenge_sha256": _sha256_file(public_path),
            "racket": {"checked_pairs": len(inputs), "status": "passed"},
            "rival": rival,
            "rival_train_disagreements": train_disagreements,
            "rival_query_disagreements": query_disagreements,
        }

    witness_input = deepcopy(settings["larger"]["episode"]["test"][0]["input"])
    witness_outputs = {
        policy: apply_policy(witness_input, policy) for policy in TURN_POLICIES
    }
    if witness_outputs["larger"] == witness_outputs["smaller"]:
        raise RuntimeError("retained query witness does not distinguish parameter settings")

    generator_path = TASK_HOME / "generator.py"
    reference_probe_path = WORKSPACE / "reference_probe.py"
    canonical_path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    return {
        "schema": "b9e736518d82-parametric-turn-half-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "episode_seed": seed,
        "parameters": PARAMETERS,
        "invariants": [
            "orange walls identify the latent adjacent channel",
            "no-marker and straight-marker branches remain canonical",
            "a bend marker splits one simple channel into two unequal halves",
            "the selected half is recolored cyan while the bend marker remains maroon",
        ],
        "source_hashes": {
            "prototype.py": _sha256_file(Path(__file__)),
            "generator.py": _sha256_file(generator_path),
            "reference_probe.py": _sha256_file(reference_probe_path),
            "canonical_puzzles.jsonl": _sha256_file(canonical_path),
        },
        "settings": settings,
        "distinguishing_witness": {
            "input": witness_input,
            "outputs": witness_outputs,
            "different": True,
        },
        "limitations": [
            "This is a task-local authoring prototype, not an approved production rule API.",
            "Evidence covers one deterministic episode seed per setting, not every seed.",
            "The variant changes only the unequal bend-marker choice; all other branches stay fixed.",
            "Public challenge files omit parameter labels, Racket text, metadata, and query answers.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=314159)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--examples-dir", type=Path, default=HERE / "examples")
    args = parser.parse_args()
    evidence = build_evidence(args.seed, args.examples_dir.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "seed": evidence["episode_seed"],
                "settings": {
                    name: {
                        "program_sha256": row["program_sha256"],
                        "racket": row["racket"],
                        "rival_train_disagreements": row["rival_train_disagreements"],
                        "rival_query_disagreements": row["rival_query_disagreements"],
                    }
                    for name, row in evidence["settings"].items()
                },
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

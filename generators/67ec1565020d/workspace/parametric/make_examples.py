"""Write Racket-checked private episodes and exact public projections."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "adapter.py"
MODES = ("canonical", "wide_region_relay")


def _load_adapter():
    name = "_67ec_parametric_examples_" + hashlib.sha256(str(ADAPTER_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _validate_request(seed: object, demos: object, queries: object) -> tuple[int, int, int]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    return seed, demos, queries


def _racket_verify(adapter, episodes: dict[str, dict[str, Any]]) -> tuple[int, dict[str, Any]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    evaluations = 0
    wrapped: dict[str, str] = {}
    with RacketBridge(timeout=20) as bridge:
        identity = {
            key: bridge.runtime_identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in bridge.runtime_identity
        }
        if identity.get("protected") is not True:
            raise ValueError("example labels require protected Racket")
        for mode, episode in episodes.items():
            program = adapter.program({"mode": mode})
            wrapped.setdefault(program, wrap_rule(program))
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                actual = bridge.eval_text(f"({wrapped[program]} {literal})")
                evaluations += 1
                if actual != pair["output"]:
                    raise ValueError(f"protected Racket label mismatch for {mode}")
    return evaluations, identity


def write_examples(
    output: Path | str,
    *,
    seed: int = 0,
    demos: int = 3,
    queries: int = 4,
    verify_racket: bool = True,
) -> dict[str, Any]:
    seed, demos, queries = _validate_request(seed, demos, queries)
    destination = Path(output)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    adapter = _load_adapter()
    episodes = {
        mode: adapter.generate(seed, {"mode": mode}, demos, queries)
        for mode in MODES
    }
    if [pair["input"] for pair in episodes[MODES[0]]["train"] + episodes[MODES[0]]["test"]] != [
        pair["input"] for pair in episodes[MODES[1]]["train"] + episodes[MODES[1]]["test"]
    ]:
        raise ValueError("settings must use matched inputs")

    files: list[tuple[Path, bytes]] = []
    seen_public_ids: set[str] = set()
    first_turn_stable = True
    for mode, episode in episodes.items():
        all_public = public_challenge_bytes(episode)
        all_id = public_challenge_id(episode)
        if all_id in seen_public_ids:
            raise ValueError("duplicate visible public batch")
        seen_public_ids.add(all_id)
        files.append((Path("public") / f"{all_id}.json", all_public))

        one_query = adapter.generate(seed, {"mode": mode}, demos, 1)
        for query_index in range(queries):
            turn = adapter.public_turn(episode, query_index)
            raw = public_challenge_bytes(turn)
            turn_id = public_challenge_id(turn)
            if query_index == 0 and raw != public_challenge_bytes(one_query):
                first_turn_stable = False
            files.append((Path("turns") / mode / f"{turn_id}.json", raw))
        private = (json.dumps(episode, indent=2, sort_keys=True) + "\n").encode("utf-8")
        files.append((Path("private") / f"{mode}.json", private))

    if not first_turn_stable:
        raise ValueError("first turn differs from a one-query generation call")
    racket_evaluations = 0
    racket_identity = None
    if verify_racket:
        racket_evaluations, racket_identity = _racket_verify(adapter, episodes)

    report: dict[str, Any] = {
        "schema": "arcpuzzles-67ec1565020d-examples-v1",
        "status": "written",
        "task_id": "67ec1565020d",
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "settings": len(episodes),
        "public_batches": len(episodes),
        "public_turns": len(episodes) * queries,
        "private_episodes": len(episodes),
        "first_turn_prefix_stable": first_turn_stable,
        "racket_evaluations": racket_evaluations,
        "racket": racket_identity,
        "limits": "Public batch files are authoring projections; actor turns use one file under turns/ at a time.",
    }

    destination.mkdir(parents=True, exist_ok=False)
    for relative, data in files:
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (destination / "manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    report = write_examples(
        args.out,
        seed=args.seed,
        demos=args.demos,
        queries=args.queries,
        verify_racket=True,
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

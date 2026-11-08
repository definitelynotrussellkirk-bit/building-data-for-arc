#!/usr/bin/env python3
"""Build source-bound Racket evidence for both border-policy settings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

from prototype import (
    ALLOWED_BORDER_POLICIES,
    DEFAULT_BORDER_POLICY,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    TASK_ID,
    canonical_source,
    choose_parameters,
    execute_rule,
    materialize_rule,
    public_challenge,
    python_reference,
    restore_canonical,
)

BANDS = ("easy", "medium", "hard")


def _sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256(path.read_bytes())


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _first_seed_for(policy: str) -> int:
    for seed in range(10000):
        if choose_parameters(seed)[PARAMETER_NAME] == policy:
            return seed
    raise AssertionError(f"no deterministic seed found for {policy}")


def _canonical_replay(root: Path, bridge: RacketBridge, source: str) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    mismatches = []
    for pair in pairs:
        actual = execute_rule(source, pair["input"], bridge=bridge)
        if actual != pair["output"]:
            mismatches.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                }
            )
    return {
        "pairs": len(pairs),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def _build_episode(
    generator: Any,
    bridge: RacketBridge,
    *,
    seed: int,
    canonical: str,
) -> dict[str, Any]:
    parameters = choose_parameters(seed)
    selected = parameters[PARAMETER_NAME]
    sources = {
        policy: materialize_rule(policy, source=canonical)
        for policy in ALLOWED_BORDER_POLICIES
    }
    pairs: list[dict[str, Any]] = []
    rival_outputs: list[dict[str, list[list[int]]]] = []
    for index in range(4):
        band = BANDS[index % len(BANDS)]
        grid = generator.generate(
            seed * 1009 + 137,
            index,
            difficulty=band,
            scene_profile="close_runner_up",
        )
        if generator.self_check(grid):
            raise AssertionError("prototype fixture is outside the canonical grammar")
        outputs = {
            policy: execute_rule(source, grid, bridge=bridge)
            for policy, source in sources.items()
        }
        for policy, output in outputs.items():
            mirror = python_reference(grid, border_policy=policy)
            if output != mirror:
                raise AssertionError(
                    f"Python mirror disagrees with executed Racket for {policy}"
                )
        if outputs[DEFAULT_BORDER_POLICY] != generator.rule_mirror(grid):
            raise AssertionError("default prototype setting diverges from canonical rule")
        if len({json.dumps(value) for value in outputs.values()}) != len(outputs):
            raise AssertionError("fixture does not distinguish both border policies")
        pairs.append({"input": grid, "output": outputs[selected]})
        rival_outputs.append(outputs)

    episode = {"demos": pairs[:3], "query": pairs[3]}
    rivals = [policy for policy in ALLOWED_BORDER_POLICIES if policy != selected]
    demo_distinction = {
        rival: any(
            rival_outputs[index][rival] != pairs[index]["output"]
            for index in range(3)
        )
        for rival in rivals
    }
    if not all(demo_distinction.values()):
        raise AssertionError("demonstrations do not distinguish the hidden setting")
    return {
        "schema": "arc-parametric-episode-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": parameters,
        "parameter_spec": PARAMETER_SPEC,
        "racket_programs": sources,
        "racket_sha256": {
            policy: _sha256(source) for policy, source in sources.items()
        },
        "episode": episode,
        "all_setting_outputs": rival_outputs,
        "checks": {
            "parameter_chosen_once_for_episode": True,
            "three_demonstrations": len(episode["demos"]) == 3,
            "query_answer_retained_privately": "output" in episode["query"],
            "all_labels_from_executed_racket": True,
            "python_mirror_parity": True,
            "default_matches_selected_canonical_rule": True,
            "demos_distinguish_each_alternative": demo_distinction,
            "every_pair_distinguishes_settings": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; use a new path to retain evidence")
    out.mkdir(parents=True)

    root = find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    source_dir = Path(__file__).resolve().parent
    canonical = canonical_source(root=root)
    sources = {
        policy: materialize_rule(policy, source=canonical)
        for policy in ALLOWED_BORDER_POLICIES
    }
    for policy, source in sources.items():
        restore_canonical(source)
        (out / f"rule-{policy}.rkt").write_text(source + "\n", encoding="utf-8")

    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}
    episodes = []
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        canonical_replay = _canonical_replay(
            root,
            bridge,
            sources[DEFAULT_BORDER_POLICY],
        )
        if not canonical_replay["passed"]:
            raise AssertionError("default setting failed canonical replay")
        for index, policy in enumerate(ALLOWED_BORDER_POLICIES):
            seed = _first_seed_for(policy)
            evidence = _build_episode(
                generator,
                bridge,
                seed=seed,
                canonical=canonical,
            )
            challenge = public_challenge(evidence["episode"])
            challenge_path = out / f"challenge-{index:03d}-{policy}.json"
            evidence_path = out / f"evidence-{index:03d}-{policy}.json"
            _write_json(challenge_path, challenge)
            evidence.update(
                {
                    "public_challenge": challenge_path.name,
                    "public_challenge_sha256": _sha256_file(challenge_path),
                    "canonical_replay": canonical_replay,
                    "source_hashes": {
                        "prototype.py": _sha256_file(source_dir / "prototype.py"),
                        "build_prototype.py": _sha256_file(Path(__file__).resolve()),
                        "selected_generator.py": generator_sha256,
                        "canonical_source": _sha256(canonical),
                    },
                    "selected_generator_path": str(
                        Path(generator_path).resolve().relative_to(root)
                    ),
                    "command": command,
                }
            )
            _write_json(evidence_path, evidence)
            episodes.append(
                {
                    "setting": policy,
                    "seed": seed,
                    "challenge": challenge_path.name,
                    "challenge_sha256": _sha256_file(challenge_path),
                    "evidence": evidence_path.name,
                    "evidence_sha256": _sha256_file(evidence_path),
                    "racket_sha256": evidence["racket_sha256"][policy],
                    "checks": evidence["checks"],
                }
            )

    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "selected_canonical_execution_path_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": [item["setting"] for item in episodes],
        "canonical_replay": canonical_replay,
        "episodes": episodes,
        "command": command,
        "limitations": [
            "This is an isolated authoring prototype, not a production rule API or training approval.",
            "Only two bounded border-policy settings and one retained episode per setting were executed.",
            "Retained fixtures intentionally make the border policy observable; broader grammars and additional plausible parameter rivals remain untested.",
        ],
        "passed": (
            set(item["setting"] for item in episodes)
            == set(ALLOWED_BORDER_POLICIES)
            and canonical_replay["passed"]
            and all(
                item["checks"]["all_labels_from_executed_racket"]
                and all(
                    item["checks"]["demos_distinguish_each_alternative"].values()
                )
                for item in episodes
            )
        ),
    }
    _write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

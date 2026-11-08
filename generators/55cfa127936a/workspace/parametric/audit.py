"""Bounded teaching census and protected-Racket parity for the parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "55cfa127936a"


def _load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("_audit_55cfa_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)

    adapter = _load_adapter()
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    from arcpuzzles import Catalog
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    canonical = {
        variant["program_solution"]
        for variant in Catalog(ROOT).get(TASK_ID)["variants"]
    }
    assert canonical == {adapter.program({"selection": "topmost"})}

    python_episodes = 0
    profile_dimensions: set[tuple[int, int]] = set()
    for seed in range(32):
        for selection in adapter.SELECTIONS:
            for demos in range(2, 7):
                episode = adapter.generate(seed, {"selection": selection}, demos, 4)
                certificate = adapter.teaching_check(episode)
                assert certificate["ok"] and not certificate["surviving_rivals"]
                assert len(episode["train"]) == demos and len(episode["test"]) == 4
                profile_dimensions.update((len(pair["input"]), len(pair["input"][0])) for pair in episode["test"])
                python_episodes += 1
    assert (30, 30) in profile_dimensions

    bridge = RacketBridge(timeout=30)
    calls = 0
    retained: dict[str, dict] = {}
    episode_summaries = []

    def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
        nonlocal calls
        adapter.analyze(grid)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        value = bridge.eval_text(f"({wrap_rule(program)} {literal})")
        adapter._validate_grid(value)
        calls += 1
        return value

    try:
        assert bridge.runtime_identity.get("backend") == "racket"
        assert bridge.runtime_identity.get("protected") is True
        for seed in (0, 17):
            for selection in adapter.SELECTIONS:
                settings = {"selection": selection}
                episode = adapter.generate(seed, settings, 2, 4)
                finite_survivors = []
                for candidate in adapter.SELECTIONS:
                    candidate_program = adapter.program({"selection": candidate})
                    outputs = [apply(candidate_program, pair["input"]) for pair in episode["train"]]
                    if outputs == [pair["output"] for pair in episode["train"]]:
                        finite_survivors.append(candidate)
                assert finite_survivors == [selection]

                surviving_rivals = []
                rival_differences = {}
                for rival in adapter.RIVALS:
                    rival_program = adapter.rival_program(rival)
                    outputs = []
                    for demo_index, pair in enumerate(episode["train"]):
                        output = apply(rival_program, pair["input"])
                        assert output == adapter.rival_output(pair["input"], rival)
                        outputs.append(output)
                        if output != pair["output"] and rival not in retained:
                            retained[rival] = {
                                "seed": seed,
                                "settings": settings,
                                "demo_index": demo_index,
                                "input": pair["input"],
                                "selected_output": pair["output"],
                                "rival_output": output,
                                "selected_program": adapter.program(settings),
                                "rival_program": rival_program,
                            }
                    if outputs == [pair["output"] for pair in episode["train"]]:
                        surviving_rivals.append(rival)
                    rival_differences[rival] = [
                        index for index, (actual, pair) in enumerate(zip(outputs, episode["train"]))
                        if actual != pair["output"]
                    ]
                assert not surviving_rivals

                for pair in episode["test"]:
                    assert apply(adapter.program(settings), pair["input"]) == pair["output"]
                episode_summaries.append({
                    "seed": seed,
                    "settings": settings,
                    "finite_survivors": finite_survivors,
                    "surviving_rivals": surviving_rivals,
                    "rival_differing_demo_indices": rival_differences,
                    "query_dimensions": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
                })
        assert set(retained) == set(adapter.RIVALS)

        sources = [
            ROOT / f"generators/{TASK_ID}/generator.py",
            HOME / "adapter.py",
            HOME / "canonical.rkt",
            HOME / "singleton_anchor_nearest.rkt",
            HOME / "promotion.json",
            Path(__file__),
            ROOT / f"generators/{TASK_ID}/tests/test_parametric_{TASK_ID}.py",
        ]
        result = {
            "schema": "arcpuzzles-singleton-anchor-teaching-audit-v1",
            "status": "passed",
            "task_id": TASK_ID,
            "python_episodes": python_episodes,
            "python_seed_range": [0, 31],
            "demo_counts": [2, 3, 4, 5, 6],
            "queries_per_episode": 4,
            "protected_racket_evaluations": calls,
            "racket": bridge.runtime_identity,
            "episode_summaries": episode_summaries,
            "rival_counterexamples": retained,
            "query_dimensions_seen": [list(item) for item in sorted(profile_dimensions)],
            "source_files": [
                {
                    "path": source.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                }
                for source in sources
            ],
            "limits": [
                "Finite two-setting and seven-rival check; not unrestricted uniqueness.",
                "Python census covers 32 seeds and all supported demo counts; protected Racket covers seeds 0 and 17 at the minimum two-demo lesson.",
                "This reviewer evidence grants neither owner acceptance nor training admission.",
            ],
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
        print(json.dumps({
            "status": result["status"],
            "python_episodes": python_episodes,
            "protected_racket_evaluations": calls,
            "rivals": len(retained),
            "out": str(args.out),
        }, indent=2))
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    run()

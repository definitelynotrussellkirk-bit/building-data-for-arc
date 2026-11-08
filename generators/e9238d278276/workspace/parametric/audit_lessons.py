"""Reusable bounded lesson audit for e9238d278276's native family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_e923_audit_family", HERE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent family")
FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(FAMILY)


def _inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def build_report(
    *,
    seeds: Iterable[int],
    demo_counts: Iterable[int] = (2, 3, 6),
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    public_failures: list[dict[str, Any]] = []
    episodes = 0
    stress = 0
    differences = 0
    harmful_survivors = 0

    for seed in seeds:
        for demos in demo_counts:
            generated = {}
            for settings in FAMILY.SETTINGS:
                try:
                    episode = FAMILY.generate(seed, settings, demos, 4)
                    generated[settings["gravity_policy"]] = episode
                    episodes += 1
                    check = FAMILY.teaching_check(episode, settings)
                    harmful_survivors += len(check["surviving_rivals"])
                    if check["survivors"] != [settings] or check["surviving_rivals"]:
                        failures.append({"seed": seed, "demos": demos, "settings": settings, "check": check})
                    pair = episode["test"][3]
                    if len(pair["input"]) == len(pair["input"][0]) == 30:
                        stress += 1
                    public = FAMILY.public_turn(episode, 0)
                    if (
                        set(public) != {"train", "test"}
                        or len(public["test"]) != 1
                        or set(public["test"][0]) != {"input"}
                        or "settings" in json.dumps(public)
                    ):
                        public_failures.append({"seed": seed, "demos": demos, "settings": settings})
                    prefix = FAMILY.generate(seed, settings, demos, 2)
                    if episode["test"][:2] != prefix["test"]:
                        failures.append({"seed": seed, "demos": demos, "settings": settings, "reason": "query prefix drift"})
                except Exception as error:  # retained as an explicit finite audit finding
                    failures.append({"seed": seed, "demos": demos, "settings": settings, "error": repr(error)})
            if set(generated) == set(FAMILY.POLICIES):
                left = generated["all_up"]
                right = generated["signal_ranked_down"]
                if _inputs(left) != _inputs(right):
                    failures.append({"seed": seed, "demos": demos, "reason": "setting-dependent inputs"})
                differences += sum(
                    a["output"] != b["output"]
                    for split in ("train", "test")
                    for a, b in zip(left[split], right[split], strict=True)
                )

    return {
        "schema": "arcpuzzles-parametric-lesson-audit-v1",
        "task_id": "e9238d278276",
        "status": "passed" if not failures and not public_failures else "failed",
        "episodes": episodes,
        "exact_30x30_pairs": stress,
        "setting_dependent_answer_differences": differences,
        "harmful_survivors": harmful_survivors,
        "failures": failures,
        "public_projection_failures": public_failures,
        "limitations": [
            "Finite audit over supplied seeds, counts, two settings, and the declared rival bank.",
            "Passing does not establish universal rule uniqueness or measured downstream learning benefit.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64, help="audit seeds 0..N-1")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    report = build_report(seeds=range(args.seeds))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

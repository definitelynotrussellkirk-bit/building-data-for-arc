"""Bounded semantic, privacy, rival, and protected-Racket audit.

Run through the packet launcher, for example::

  python3 review.py run python3 generators/TASK/workspace/parametric/audit.py \
      --out ../checks/TASK/audit --seeds 12

The finite rival bank and bounded seeds are evidence against named shortcuts,
not a uniqueness proof. This tool performs no owner acceptance or training
admission.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HOME.parents[1]
TASK = HOME.name


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_bounded_audit_" + TASK + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def source_files() -> list[dict[str, str]]:
    paths = [
        path for path in HOME.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and (path.suffix in {".py", ".rkt", ".md"}
             or path.name in {"promotion.json", "public-parent.json", "public-eval-creation.json"})
    ]
    return [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(paths)
    ]


def _write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=12)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 64:
        raise ValueError("seeds must be in 1..64")
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(f"choose a fresh output directory: {args.out}")

    from arcpuzzles.parametric_worker import _grid, _real_evaluator
    from reviewer_support import public_challenge_bytes

    adapter = _load_adapter()
    promotion = json.loads((HERE / "promotion.json").read_text())
    parameter, options = next(iter(promotion["parameters"].items()))
    options = tuple(options)
    rivals = tuple(adapter.impl.RIVALS)
    initial_sources = source_files()

    failures: list[object] = []
    counterexamples: dict[str, object] = {}
    not_refuted: set[str] = set()
    episodes = pair_instances = rival_checks = public_views = large_pairs = matched_banks = 0
    distinct_inputs: set[str] = set()
    first_query_digests: set[str] = set()
    public_payloads: dict[str, bytes] = {}

    for seed in range(args.seeds):
        query_by_option: dict[str, object] = {}
        for demos in (2, 3, 6):
            bank = {
                option: adapter.generate(seed, {parameter: option}, demos, 4)
                for option in options
            }
            reference_inputs = [
                pair["input"] for split in ("train", "test") for pair in bank[options[0]][split]
            ]
            for option in options[1:]:
                other_inputs = [pair["input"] for split in ("train", "test") for pair in bank[option][split]]
                if other_inputs != reference_inputs:
                    failures.append(["setting-input-mismatch", seed, demos, option])
            matched_banks += 1

            for option, episode in bank.items():
                episodes += 1
                pairs = episode["train"] + episode["test"]
                pair_instances += len(pairs)
                digests = [_digest(pair["input"]) for pair in pairs]
                distinct_inputs.update(digests)
                if len(set(digests)) != len(digests):
                    failures.append(["duplicate-input", seed, demos, option])
                queries = [pair["input"] for pair in episode["test"]]
                if option in query_by_option and query_by_option[option] != queries:
                    failures.append(["query-instability", seed, demos, option])
                query_by_option.setdefault(option, copy.deepcopy(queries))
                first_query_digests.add(_digest(queries[0]))

                for pair in pairs:
                    if adapter.impl.solve(pair["input"], option) != pair["output"]:
                        failures.append(["python-label", seed, demos, option])
                    h, w = len(pair["input"]), len(pair["input"][0])
                    oh, ow = len(pair["output"]), len(pair["output"][0])
                    large_pairs += int(max(h, w, oh, ow) >= 25)

                views = adapter.impl.public_turns(episode, seed)
                public_views += len(views)
                if not all(
                    set(view) == {"train", "test"}
                    and len(view["test"]) == 1
                    and set(view["test"][0]) == {"input"}
                    for view in views
                ):
                    failures.append(["public-shape", seed, demos, option])
                mutant = copy.deepcopy(episode)
                mutant["settings"] = {"private": True}
                mutant["program_solution"] = "PRIVATE CANARY"
                mutant["seed"] = 999
                for pair in mutant["test"]:
                    pair["output"] = [[9]]
                if adapter.impl.public_turns(mutant, seed) != views:
                    failures.append(["public-private-dependence", seed, demos, option])

                if seed == min(7, args.seeds - 1) and demos == 2:
                    for view in views:
                        payload = public_challenge_bytes(view)
                        public_payloads[hashlib.sha256(payload).hexdigest()] = payload

                other = options[1] if option == options[0] else options[0]
                if not any(
                    adapter.impl.solve(pair["input"], other) != pair["output"]
                    for pair in episode["train"]
                ):
                    failures.append(["setting-not-taught", seed, demos, option])

                if demos == 2:
                    for rival in rivals:
                        rival_checks += 1
                        rival_train = [adapter.impl.solve(pair["input"], option, rival) for pair in episode["train"]]
                        fits = all(actual == pair["output"] for actual, pair in zip(rival_train, episode["train"]))
                        harms = any(
                            adapter.impl.solve(pair["input"], option, rival) != pair["output"]
                            for pair in episode["test"]
                        )
                        name = f"{option}:{rival}"
                        if fits and harms:
                            failures.append(["harmful-rival", seed, option, rival])
                        if not fits and name not in counterexamples:
                            index = next(i for i, (actual, pair) in enumerate(zip(rival_train, episode["train"]))
                                         if actual != pair["output"])
                            counterexamples[name] = {"seed": seed, "demo_index": index}
                        if fits and not harms:
                            not_refuted.add(name)

    run, racket_identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    racket_evaluations = 0
    try:
        for seed in sorted({0, min(7, args.seeds - 1)}):
            for option in options:
                episode = adapter.generate(seed, {parameter: option}, 2, 4)
                for pair in episode["train"] + episode["test"]:
                    actual = _grid(run(episode["program_solution"], pair["input"]))
                    racket_evaluations += 1
                    if actual != pair["output"]:
                        failures.append(["racket-parity", seed, option])
    finally:
        bridge.close()

    if source_files() != initial_sources:
        failures.append(["source-changed-during-audit"])

    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    for digest, payload in sorted(public_payloads.items()):
        (public_dir / f"{digest}.json").write_bytes(payload)

    report = {
        "schema": "public-family-bounded-audit-v1",
        "task_id": TASK,
        "status": "passed" if not failures else "failed",
        "parameter": parameter,
        "settings": list(options),
        "seeds": list(range(args.seeds)),
        "demonstration_counts": [2, 3, 6],
        "episodes": episodes,
        "pair_instances": pair_instances,
        "matched_setting_banks": matched_banks,
        "distinct_inputs": len(distinct_inputs),
        "distinct_first_queries": len(first_query_digests),
        "large_pair_instances": large_pairs,
        "finite_rival_checks": rival_checks,
        "rivals": list(rivals),
        "counterexample_seeds": counterexamples,
        "sampled_equivalences_not_refuted": sorted(not_refuted - set(counterexamples)),
        "public_views_checked": public_views,
        "saved_public_views": len(public_payloads),
        "protected_racket_evaluations": racket_evaluations,
        "racket": racket_identity,
        "source_binding": initial_sources,
        "failures": failures,
        "limits": (
            "Finite named rivals and bounded seeds, not universal uniqueness. "
            "Only selected labels are replayed through protected Racket. "
            "No owner acceptance, native qualification, or training admission."
        ),
    }
    _write_new(args.out / "audit.json", report)
    print(json.dumps({
        key: report[key] for key in (
            "status", "episodes", "pair_instances", "finite_rival_checks",
            "public_views_checked", "protected_racket_evaluations", "failures"
        )
    }, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

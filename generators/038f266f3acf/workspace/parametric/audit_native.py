"""Deterministic bounded audit for the native beam-width adapter.

This auditor is deliberately Racket-free: it pressure-tests deterministic
construction, matched inputs, labels against the independent Python mirror,
and the declared finite rival family.  Native qualification remains the
protected-Racket authority for labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def _load_adapter():
    source = Path(__file__).resolve().with_name("adapter.py")
    if source.is_symlink() or not source.is_file():
        raise ImportError("audit_native requires adjacent regular adapter.py")
    body = source.read_bytes()
    name = "_beam_width_audit_adapter_" + hashlib.sha256(
        str(source).encode() + body
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load adjacent adapter: {source}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(body, str(source), "exec"), module.__dict__)
    return module


_adapter = _load_adapter()
_prototype = _adapter._prototype


def _typed_int_list(name, values, low, high):
    if (
        type(values) is not list
        or not values
        or any(type(value) is not int or not low <= value <= high for value in values)
        or len(values) != len(set(values))
    ):
        raise ValueError(f"{name} must be distinct exact integers in {low}..{high}")
    return list(values)


def _payload(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def _sha(value):
    return hashlib.sha256(_payload(value)).hexdigest()


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _outputs(episode):
    return [pair["output"] for pair in episode["train"] + episode["test"]]


def _survivors(episode):
    survivors = []
    for name, (multiplier, cap) in _prototype.MODELS.items():
        predictions = [
            _prototype.simulate(pair["input"], multiplier, cap_depth=cap)
            for pair in episode["train"]
        ]
        if predictions == [pair["output"] for pair in episode["train"]]:
            survivors.append(name)
    return survivors


def _check_episode(episode, *, seed, multiplier, demos):
    if set(episode) != {"train", "test", "program_solution"}:
        raise AssertionError("adapter returned unexpected public/private fields")
    if len(episode["train"]) != demos or len(episode["test"]) != 4:
        raise AssertionError("adapter returned wrong pair counts")
    if episode["program_solution"] != _adapter.program(
        {"wing_multiplier": multiplier}
    ):
        raise AssertionError("adapter program differs from setting program")
    inputs = _inputs(episode)
    if len({_sha(grid) for grid in inputs}) != len(inputs):
        raise AssertionError("episode contains duplicate inputs")
    chosen = f"multiplier_{multiplier}"
    if _survivors(episode) != [chosen]:
        raise AssertionError("demonstrations do not isolate selected finite model")
    for pair in episode["train"] + episode["test"]:
        expected = _prototype.simulate(pair["input"], multiplier)
        if pair["output"] != expected:
            raise AssertionError("adapter label differs from Python mirror")
        predictions = {
            name: _prototype.simulate(pair["input"], value, cap_depth=cap)
            for name, (value, cap) in _prototype.MODELS.items()
        }
        if len({_sha(grid) for grid in predictions.values()}) != len(predictions):
            raise AssertionError("declared finite models are observationally aliased")
    if episode != _adapter.generate(
        seed, {"wing_multiplier": multiplier}, demos, 4
    ):
        raise AssertionError("adapter is not deterministic")


def audit_matrix(*, seeds, demo_counts):
    seeds = _typed_int_list("seeds", seeds, 0, 2**63 - 1)
    demo_counts = _typed_int_list("demo_counts", demo_counts, 2, 6)
    records = []
    by_seed_setting = {}
    pair_total = 0
    for seed in seeds:
        for demos in demo_counts:
            episodes = {}
            for multiplier in (1, 2):
                episode = _adapter.generate(
                    seed, {"wing_multiplier": multiplier}, demos, 4
                )
                _check_episode(
                    episode, seed=seed, multiplier=multiplier, demos=demos
                )
                episodes[multiplier] = episode
                pair_total += demos + 4
                by_seed_setting[(seed, multiplier, demos)] = episode
            left, right = episodes[1], episodes[2]
            matched = _inputs(left) == _inputs(right)
            disagree = all(
                a != b for a, b in zip(_outputs(left), _outputs(right))
            )
            if not matched:
                raise AssertionError("settings do not share identical input streams")
            if not disagree:
                raise AssertionError("a retained pair does not expose the setting")
            records.append(
                {
                    "seed": seed,
                    "demos": demos,
                    "queries": 4,
                    "matched_input_streams": matched,
                    "all_outputs_disagree": disagree,
                    "input_sha256": [_sha(grid) for grid in _inputs(left)],
                    "query_shapes": [
                        [len(pair["input"]), len(pair["input"][0])]
                        for pair in left["test"]
                    ],
                    "survivors": {
                        "1": _survivors(left),
                        "2": _survivors(right),
                    },
                }
            )
    ordered_counts = sorted(demo_counts)
    for seed in seeds:
        for multiplier in (1, 2):
            for low, high in zip(ordered_counts, ordered_counts[1:]):
                smaller = by_seed_setting[(seed, multiplier, low)]
                larger = by_seed_setting[(seed, multiplier, high)]
                if smaller["train"] != larger["train"][:low]:
                    raise AssertionError("demonstrations are not prefix-stable")
                if smaller["test"] != larger["test"]:
                    raise AssertionError("query schedule changes with demo count")

    here = Path(__file__).resolve().parent
    source_names = ("adapter.py", "beam_width.py", "promotion.json", "audit_native.py")
    return {
        "schema": "038f266f3acf-native-audit-v1",
        "status": "passed",
        "task_id": _prototype.TASK_ID,
        "label_backend": "python_mirror_claims; protected Racket is native qualification",
        "summary": {
            "seeds": len(seeds),
            "demo_counts": len(demo_counts),
            "settings": 2,
            "episodes": len(seeds) * len(demo_counts) * 2,
            "pairs": pair_total,
            "failures": 0,
        },
        "records": records,
        "source_sha256": {
            name: hashlib.sha256((here / name).read_bytes()).hexdigest()
            for name in source_names
        },
        "limits": (
            "Bounded deterministic mirror audit only; protected-Racket qualification "
            "is retained separately and owner acceptance/training admission are not performed."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(32)))
    parser.add_argument("--demos", type=int, nargs="+", default=list(range(2, 7)))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = audit_matrix(seeds=args.seeds, demo_counts=args.demos)
        if args.out.exists() or args.out.is_symlink():
            raise FileExistsError(f"Choose a new output path: {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
    except (OSError, ValueError, AssertionError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(receipt["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

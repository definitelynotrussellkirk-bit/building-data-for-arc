"""Bounded Racket-backed teaching audit for the b98cdd1751a7 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge


HERE = Path(__file__).resolve().parent
_NATIVE_PATH = HERE / "native.py"
_NATIVE_NAME = "_b98cdd1751a7_audit_native_" + hashlib.sha256(
    str(_NATIVE_PATH).encode("utf-8")
).hexdigest()[:12]
_NATIVE_SPEC = importlib.util.spec_from_file_location(_NATIVE_NAME, _NATIVE_PATH)
_NATIVE = importlib.util.module_from_spec(_NATIVE_SPEC)
_NATIVE_SPEC.loader.exec_module(_NATIVE)


def _replace_bottom(replacement):
    source = _NATIVE.CANONICAL_SOURCE
    needle = _NATIVE._BOTTOM_BINDING
    if source.count(needle) != 1:
        raise ValueError("canonical lower-row binding no longer matches audit rivals")
    return source.replace(needle, replacement, 1)


def rival_programs():
    """Return total finite rivals beyond the two declared family settings."""
    spatial = (
        "(bot-spatial (sort-by (filter (lambda (o) (>= (min-of fst (obj-cells o)) mid-r)) objs) "
        "(lambda (o) (min-of snd (obj-cells o)))))"
    )
    return {
        "reverse_bottom": _replace_bottom(f"{spatial} (bot (reverse bot-spatial))"),
        "numeric_color_ascending": _replace_bottom(
            "(bot (sort-by (filter (lambda (o) (>= (min-of fst (obj-cells o)) mid-r)) objs) "
            "(lambda (o) (obj-color o))))"
        ),
        "match_top_right_color": _replace_bottom(
            f"{spatial} "
            "(cue-color (obj-color (nth top 1))) "
            "(bot (append "
            "(filter (lambda (o) (= (obj-color o) cue-color)) bot-spatial) "
            "(filter (lambda (o) (not (= (obj-color o) cue-color))) bot-spatial)))"
        ),
    }


def audit_episode(inputs, selected_source, rivals, apply):
    """Report any rival fitting all demos; retain its first query comparison."""
    if type(inputs) is not dict or set(inputs) != {"train", "test"}:
        raise ValueError("inputs must contain exactly train/test grid lists")
    if not inputs["train"] or not inputs["test"]:
        raise ValueError("audit requires nonempty demonstrations and queries")
    if not isinstance(selected_source, str) or type(rivals) is not dict:
        raise ValueError("audit requires materialized selected and rival programs")

    selected_train = [apply(selected_source, grid) for grid in inputs["train"]]
    selected_test = [apply(selected_source, grid) for grid in inputs["test"]]
    findings = []
    for name, source in sorted(rivals.items()):
        if source == selected_source:
            continue
        try:
            rival_train = [apply(source, grid) for grid in inputs["train"]]
            rival_test = [apply(source, grid) for grid in inputs["test"]]
        except Exception as error:
            findings.append({
                "kind": "rival_runtime_error",
                "rival": name,
                "error": f"{type(error).__name__}: {error}",
            })
            continue
        if rival_train != selected_train:
            continue
        differing = [index for index, (want, got) in enumerate(zip(selected_test, rival_test))
                     if want != got]
        index = differing[0] if differing else 0
        findings.append({
            "kind": ("demo_fit_query_disagreement" if differing
                     else "demo_fit_all_queries"),
            "rival": name,
            "query_index": index,
            "input": inputs["test"][index],
            "selected_output": selected_test[index],
            "rival_output": rival_test[index],
        })
    return findings


def run_audit(seeds, demo_counts, queries=4):
    report = {
        "schema": "arcpuzzles-b98cdd1751a7-self-audit-v1",
        "task_id": _NATIVE.TASK_ID,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": queries,
        "settings": list(_NATIVE.SETTINGS),
        "rivals": sorted(rival_programs()),
        "jobs": [],
        "findings": [],
    }
    extras = rival_programs()
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("self-audit requires protected Racket")
        report["runtime_identity"] = identity

        def apply(source, grid):
            return _NATIVE.execute(source, grid, bridge)

        for seed in seeds:
            for demos in demo_counts:
                inputs = _NATIVE.sample_inputs(seed, demos, queries)
                for setting in _NATIVE.SETTINGS:
                    selected = _NATIVE.program(setting)
                    rivals = dict(extras)
                    for other in _NATIVE.SETTINGS:
                        source = _NATIVE.program(other)
                        if source != selected:
                            rivals[other["bottom_order"]] = source
                    findings = audit_episode(inputs, selected, rivals, apply)
                    job = {
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "settings": setting,
                        "rival_count": len(rivals),
                        "finding_count": len(findings),
                    }
                    report["jobs"].append(job)
                    for finding in findings:
                        report["findings"].append({**job, **finding})
    report["passed"] = not report["findings"]
    report["job_count"] = len(report["jobs"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--demos", nargs="+", type=int, default=[2, 3, 4, 5, 6])
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = run_audit(args.seeds, args.demos, args.queries)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": report["passed"],
        "job_count": report["job_count"],
        "finding_count": len(report["findings"]),
        "out": str(out),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

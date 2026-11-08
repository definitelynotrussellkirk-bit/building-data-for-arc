"""Bounded adversarial and protected-Racket audit for 91c488d9ffdc."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("rect_audit_target", _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
p = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = p
_SPEC.loader.exec_module(p)


def _blank(grid):
    return [[0 for _ in row] for row in grid]


def _outline_item(grid, item):
    out = _blank(grid)
    for r, c in p.border_cells(item["bbox"]):
        out[r][c] = item["color"]
    return out


def _fixed_candidate(index):
    def rival(grid):
        info = p.analyze(grid)
        return _outline_item(grid, info["candidates"][index % len(info["candidates"])])
    return rival


def _anchor_only(grid):
    return _outline_item(grid, p.analyze(grid)["anchor"])


def _largest_candidate(grid):
    info = p.analyze(grid)
    return _outline_item(grid, max(info["candidates"], key=lambda item: item["area"]))


def _smallest_candidate(grid):
    info = p.analyze(grid)
    return _outline_item(grid, min(info["candidates"], key=lambda item: item["area"]))


def _perimeter_selector(grid):
    info = p.analyze(grid)
    anchor = info["anchor"]
    perimeter = 2 * (anchor["height"] + anchor["width"]) - 4
    index = (perimeter - 1) % len(info["candidates"])
    return _outline_item(grid, info["candidates"][index])


def _color_order_selector(grid):
    info = p.analyze(grid)
    by_color = sorted(info["rectangles"], key=lambda item: item["color"])
    anchor = by_color[0]
    candidates = by_color[1:]
    index = (anchor["area"] - 1) % len(candidates)
    return _outline_item(grid, candidates[index])


RIVALS = {
    "all_rectangles": lambda grid: p.apply_mode(grid, "all_rectangles"),
    "anchor_area_select": lambda grid: p.apply_mode(grid, "anchor_area_select"),
    "anchor_only": _anchor_only,
    "fixed_candidate_0": _fixed_candidate(0),
    "fixed_candidate_1": _fixed_candidate(1),
    "fixed_candidate_2": _fixed_candidate(2),
    "largest_candidate": _largest_candidate,
    "smallest_candidate": _smallest_candidate,
    "off_by_one_area": p.apply_wrong_plus_one,
    "anchor_perimeter_select": _perimeter_selector,
    "color_order_area_select": _color_order_selector,
}


def python_audit(*, seeds=(0, 17, 101), demo_counts=range(2, 7)):
    ambiguities = []
    episodes = pairs = rival_checks = public_checks = stress = 0
    branches = set()
    for seed in seeds:
        for demos in demo_counts:
            for mode in p.MODES:
                maximum = p.generate_episode(seed, outline_mode=mode, demos=6, queries=4)
                episode = p.generate_episode(seed, outline_mode=mode, demos=demos, queries=4)
                episodes += 1
                all_pairs = episode["train"] + episode["test"]
                pairs += len(all_pairs)
                serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
                if len(serial) != len(set(serial)):
                    ambiguities.append({"seed": seed, "demos": demos, "mode": mode, "failure": "duplicate_input"})
                if episode["train"] != maximum["train"][:demos] or episode["test"] != maximum["test"]:
                    ambiguities.append({"seed": seed, "demos": demos, "mode": mode, "failure": "prefix_instability"})
                if (len(episode["test"][3]["input"]), len(episode["test"][3]["input"][0])) == (30, 30):
                    stress += 1
                for pair in all_pairs:
                    branches.add(p.analyze(pair["input"])["target_index"])
                for qi in range(4):
                    view = p.public_turn(episode, qi)
                    public_checks += 1
                    if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
                        ambiguities.append({"seed": seed, "demos": demos, "mode": mode, "failure": "public_projection"})
                intended = [pair["output"] for pair in episode["train"]]
                for name, rival in RIVALS.items():
                    if name == mode:
                        continue
                    rival_checks += 1
                    survives = [rival(pair["input"]) for pair in episode["train"]] == intended
                    changed = [i for i, pair in enumerate(episode["test"]) if rival(pair["input"]) != pair["output"]]
                    if survives and changed:
                        ambiguities.append({"seed": seed, "demos": demos, "mode": mode, "rival": name, "changed_queries": changed})
    return {
        "episodes": episodes,
        "pairs": pairs,
        "rival_checks": rival_checks,
        "public_checks": public_checks,
        "stress_30x30": stress,
        "target_index_branches": sorted(branches),
        "rivals": sorted(RIVALS),
        "ambiguities": ambiguities,
        "limits": "Finite declared rivals over seeds 0,17,101 and demo counts 2..6; not universal uniqueness.",
    }


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def racket_audit(seeds=(0, 17)):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    programs = {mode: p.rule_text(mode) for mode in p.MODES}
    programs["wrong_plus_one"] = p.counterfactual_program()
    mismatches = []
    evaluations = 0
    changed = 0
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires protected Racket")
        wrapped = {name: wrap_rule(program) for name, program in programs.items()}
        for seed in seeds:
            episode = p.generate_episode(seed, outline_mode="anchor_area_select", demos=6, queries=4)
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    for mode in p.MODES:
                        actual = bridge.eval_text(f"({wrapped[mode]} {_literal(pair['input'])})")
                        expected = p.apply_mode(pair["input"], mode)
                        evaluations += 1
                        if actual != expected:
                            mismatches.append({"seed": seed, "split": split, "index": index, "program": mode})
            pair = episode["test"][0]
            correct = bridge.eval_text(f"({wrapped['anchor_area_select']} {_literal(pair['input'])})")
            wrong = bridge.eval_text(f"({wrapped['wrong_plus_one']} {_literal(pair['input'])})")
            evaluations += 2
            if correct != wrong:
                changed += 1
            else:
                mismatches.append({"seed": seed, "failure": "counterfactual_unchanged"})
        keep = ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256")
        return {
            "runtime": {key: identity[key] for key in keep if key in identity},
            "evaluations": evaluations,
            "counterfactual_changes": changed,
            "mismatches": mismatches,
        }


def build_report(out_root: Path):
    py = python_audit()
    racket = racket_audit()
    examples = out_root / "examples"
    private = []
    public_paths = []
    for setting_index, mode in enumerate(p.MODES):
        episode = p.generate_episode(900 + setting_index, outline_mode=mode, demos=3, queries=4)
        private.append({"seed": 900 + setting_index, "settings": {"outline_mode": mode}, **episode})
        for query_index in range(4):
            data = p.public_bytes(episode, query_index)
            path = examples / "public" / f"{hashlib.sha256(data).hexdigest()}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            public_paths.append(path.relative_to(out_root).as_posix())
    (examples / "private.json").parent.mkdir(parents=True, exist_ok=True)
    (examples / "private.json").write_text(json.dumps(private, indent=2, sort_keys=True) + "\n")
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": p.TASK_ID,
        "status": "passed" if not py["ambiguities"] and not racket["mismatches"] else "failed",
        "python": py,
        "racket": racket,
        "program_sha256": {mode: hashlib.sha256(p.rule_text(mode).encode()).hexdigest() for mode in p.MODES},
        "counterfactual_program_sha256": hashlib.sha256(p.counterfactual_program().encode()).hexdigest(),
        "examples": {"private": "examples/private.json", "public": public_paths},
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    report = build_report(args.out)
    (args.out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["python"]["episodes"],
        "rival_checks": report["python"]["rival_checks"],
        "ambiguities": len(report["python"]["ambiguities"]),
        "racket_evaluations": report["racket"]["evaluations"],
        "mismatches": len(report["racket"]["mismatches"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Bounded adversarial and protected-Racket audit for a2d8f0cb0fdb."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("a2d8_audit_target", _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
p = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = p
_SPEC.loader.exec_module(p)


def _blank(grid):
    return [[0 for _ in row] for row in grid]


def _paint_cells(grid, cells, color):
    out = _blank(grid)
    for r, c in cells:
        out[r][c] = color
    return out


def _paint_all_blue(grid, color):
    out = _blank(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if r > 0 and value == 1:
                out[r][c] = color
    return out


def _largest_fixed_header(index):
    def rival(grid):
        info = p.analyze(grid)
        return _paint_cells(grid, info["largest_cells"], info["header_colors"][index])
    return rival


def _smallest_relay(grid):
    return p.apply_wrong_smallest(grid)


def _largest_all_selected(grid):
    info = p.analyze(grid)
    return _paint_all_blue(grid, info["selected_header_color"])


def _largest_first_header(grid):
    info = p.analyze(grid)
    return _paint_cells(grid, info["largest_cells"], info["header_colors"][0])


def _largest_last_header(grid):
    info = p.analyze(grid)
    return _paint_cells(grid, info["largest_cells"], info["header_colors"][-1])


def _component_count_header(grid):
    info = p.analyze(grid)
    index = (len(info["components"]) - 1) % 3
    return _paint_cells(grid, info["largest_cells"], info["header_colors"][index])


RIVALS = {
    "first_header_all": lambda grid: p.apply_mode(grid, "first_header_all"),
    "largest_component_indexed_header": lambda grid: p.apply_mode(grid, "largest_component_indexed_header"),
    "largest_first_header": _largest_first_header,
    "largest_last_header": _largest_last_header,
    "largest_fixed_header_0": _largest_fixed_header(0),
    "largest_fixed_header_1": _largest_fixed_header(1),
    "largest_fixed_header_2": _largest_fixed_header(2),
    "selected_header_all_components": _largest_all_selected,
    "smallest_component_relay": _smallest_relay,
    "component_count_selects_header": _component_count_header,
}


def python_audit(*, seeds=(0, 17, 101), demo_counts=range(2, 7)):
    ambiguities = []
    episodes = pairs = rival_checks = public_checks = stress = 0
    branches = set()
    for seed in seeds:
        for demos in demo_counts:
            for mode in p.MODES:
                maximum = p.generate_episode(seed, selection_mode=mode, demos=6, queries=4)
                episode = p.generate_episode(seed, selection_mode=mode, demos=demos, queries=4)
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
                    branches.add(p.analyze(pair["input"])["selected_header_index"])
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
        "header_index_branches": sorted(branches),
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
    programs["wrong_smallest"] = p.counterfactual_program()
    mismatches = []
    evaluations = 0
    changed = 0
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires protected Racket")
        wrapped = {name: wrap_rule(program) for name, program in programs.items()}
        for seed in seeds:
            episode = p.generate_episode(seed, selection_mode="largest_component_indexed_header", demos=6, queries=4)
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    for mode in p.MODES:
                        actual = bridge.eval_text(f"({wrapped[mode]} {_literal(pair['input'])})")
                        expected = p.apply_mode(pair["input"], mode)
                        evaluations += 1
                        if actual != expected:
                            mismatches.append({"seed": seed, "split": split, "index": index, "program": mode})
            pair = episode["test"][0]
            correct = bridge.eval_text(f"({wrapped['largest_component_indexed_header']} {_literal(pair['input'])})")
            wrong = bridge.eval_text(f"({wrapped['wrong_smallest']} {_literal(pair['input'])})")
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
        episode = p.generate_episode(900 + setting_index, selection_mode=mode, demos=3, queries=4)
        private.append({"seed": 900 + setting_index, "settings": {"selection_mode": mode}, **episode})
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

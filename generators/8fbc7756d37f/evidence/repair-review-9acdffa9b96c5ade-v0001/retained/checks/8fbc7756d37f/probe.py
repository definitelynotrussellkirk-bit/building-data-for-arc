"""Bounded reproduction of the current isolated-component shortcut audit."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from reviewer_support import canonical_pairs, load_selected_generator
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK = "8fbc7756d37f"


def exact_component_rival(grid):
    """Keep anti-diagonals only for exact monochrome 2x2 components."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            comp = set()
            while todo:
                rr, cc = todo.pop()
                if (rr, cc) in comp:
                    continue
                comp.add((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in comp:
                        todo.append((nr, nc))
            seen.update(comp)
            r0, c0 = min(rr for rr, _ in comp), min(cc for _, cc in comp)
            if comp == {(r0, c0), (r0+1, c0), (r0, c0+1), (r0+1, c0+1)}:
                out[r0][c0+1] = out[r0+1][c0] = color
    return out


def main():
    mod, source, sha = load_selected_generator(TASK, root=ROOT)
    catalog = Catalog(ROOT)
    row = catalog.get(TASK)
    rule_task = row.get("rule_task_id", TASK)
    variants = catalog._variants()[rule_task]
    programs = {v["program_solution"] for v in variants}
    assert len(programs) == 1, "canonical rule must be unambiguous"
    program = programs.pop()
    command = {"cwd": "repo", "argv": ["python3", "../checks/8fbc7756d37f/probe.py"], "exit_code": 0}
    report = {
        "task_id": TASK,
        "generator_source_path": source.relative_to(ROOT).as_posix(),
        "generator_sha256": sha,
        "canonical_program": program,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": command,
        "scope": "Four canonical labeled pairs, four medium generated samples, and one lawful discriminator; no battery or qualification.",
        "canonical": [], "generated": [],
    }
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            report["runtime_identity"] = identity
            for pair in canonical_pairs(rule_task, root=ROOT, labeled_only=True):
                actual = apply(program, pair["input"])
                rival = exact_component_rival(pair["input"])
                report["canonical"].append({**pair, "racket_output": actual,
                    "rival_output": rival, "canonical_label_matches": actual == pair["output"],
                    "rival_fits": rival == actual})
            for seed in range(2):
                for sample_index in range(2):
                    inp = mod.generate(seed, sample_index, difficulty="medium")
                    actual = apply(program, inp)
                    rival = exact_component_rival(inp)
                    report["generated"].append({"seed": seed, "sample_index": sample_index,
                        "difficulty": "medium", "input": inp, "racket_output": actual,
                        "rival_output": rival, "rival_fits": rival == actual,
                        "validator_findings": mod.self_check(inp)})
            inp = [[0] * 6 for _ in range(5)]
            for r in (1, 2):
                for c in (1, 2, 3):
                    inp[r][c] = 4
            actual = apply(program, inp)
            rival = exact_component_rival(inp)
            report["discriminator"] = {"input": inp, "racket_output": actual,
                "rival_output": rival, "validator_findings": mod.self_check(inp),
                "rival_fits": rival == actual}
        finally:
            bridge.close()
    assert all(x["canonical_label_matches"] and x["rival_fits"] for x in report["canonical"])
    assert all(x["rival_fits"] and not x["validator_findings"] for x in report["generated"])
    witness = report["discriminator"]
    assert not witness["validator_findings"] and not witness["rival_fits"]
    assert sum(cell != 0 for r in witness["racket_output"] for cell in r) == 4
    report["result"] = "reproduced_unresolved_sampler_validator_mismatch"
    (HERE / "probe-result.json").write_text(json.dumps(report, indent=2) + "\n")
    summary = {
        "task_id": TASK, "outcome": "unchanged",
        "summary": "Independently reproduced the existing unresolved isolated-2x2-component shortcut on the unchanged source. Rival fits all canonical pairs and four fresh samples but fails a validator-clean 2x3 rectangle under protected Racket.",
        "changed_components": ["tests_notes"],
        "evidence_paths": ["checks/8fbc7756d37f/probe.py", "checks/8fbc7756d37f/probe-result.json"],
        "remaining_failures": ["Default sampler only teaches isolated 2x2 components; validator accepts overlapping windows in a 2x3 rectangle. Existing audit remains unresolved. Missing RULE_HASH and singleton-axis lint findings from inherited audit were not rerun."],
        "verification_commands": [command],
        "exit_code": 0,
    }
    (HERE / "peer-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"result": report["result"], "generator_sha256": sha,
        "canonical_pairs": len(report["canonical"]), "fresh_samples": len(report["generated"]),
        "runtime_backend": identity["backend"], "runtime_protected": identity["protected"]}))


if __name__ == "__main__":
    main()

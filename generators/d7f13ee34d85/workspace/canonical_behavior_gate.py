"""Compare canonical input behaviors with a bounded ordinary generator sample.

Direct use from a library checkout:
  python generators/d7f13ee34d85/workspace/canonical_behavior_gate.py --out report.json
Use --generator-file to inspect a retained baseline. This command computes no
output labels and executes no reference rule. Ordered windows are raw consecutive
generate calls, not the runner's accepted/Racket-labelled production lessons.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

# Permit direct invocation without relying on cwd or another checkout's imports.
for _parent in Path(__file__).resolve().parents:
    _runtime = _parent / "shared/runtime"
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
    if (_parent / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_parent))
        break
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "d7f13ee34d85"
FEATURES = ("negative_centering_offset", "shared_frame_colors", "nonsquare_frame")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def extract_features(grid):
    """Input-only four-connected monochrome components; independent of generator hooks."""
    grid = normalize_grid(grid)
    seen, frames, shapes = set(), [], []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            pending, cells = [(r, c)], set()
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            rs, cs = zip(*cells)
            top, bottom, left, right = min(rs), max(rs), min(cs), max(cs)
            height, width = bottom - top + 1, right - left + 1
            border = {(rr, cc) for rr in range(top, bottom + 1) for cc in range(left, right + 1)
                      if rr in (top, bottom) or cc in (left, right)}
            if height >= 3 and width >= 3 and cells == border:
                frames.append((color, height - 2, width - 2))
            else:
                shapes.append((len(cells), height, width))
    paired = zip(sorted(frames, key=lambda x: x[1] * x[2]), sorted(shapes, key=lambda x: x[0]))
    return {"negative_centering_offset": any(sh > fh or sw > fw for (_, fh, fw), (_, sh, sw) in paired),
            "shared_frame_colors": len({f[0] for f in frames}) < len(frames),
            "nonsquare_frame": any(f[1] != f[2] for f in frames)}


def summarize(rows):
    valid = [r for r in rows if "features" in r]
    return {"requested": len(rows), "count": len(valid),
            "unique_inputs": len({r["input_sha256"] for r in valid}),
            "feature_counts": {f: sum(r["features"][f] for r in valid) for f in FEATURES},
            "witnesses": {f: next(r for r in valid if r["features"][f])
                          for f in FEATURES if any(r["features"][f] for r in valid)},
            "draws": [{k: v for k, v in r.items() if k != "input"} for r in rows]}


def audit(*, root, generator_file=None, samples=20, lessons=10,
          bands=("default", "easy", "medium", "hard"), seed=0, sample_index=0,
          demos=None, lesson_stride=17, lesson_target_features=()):
    if samples < 1 or lessons < 1 or lesson_stride < 1:
        raise ValueError("samples, lessons and lesson_stride must be positive")
    if not bands or any(b not in ("default", "easy", "medium", "hard") for b in bands):
        raise ValueError("bands must name default/easy/medium/hard")
    if set(lesson_target_features) - set(FEATURES):
        raise ValueError("unknown lesson target feature")
    root = find_root(root)
    source = Path(generator_file or root / "generators" / TASK_ID / "generator.py").resolve()
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    spec = importlib.util.spec_from_file_location("behavior_gate_generator_" + source_hash[:16], source)
    gen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gen
    exec(compile(source_bytes, str(source), "exec"), gen.__dict__)
    demos_source = "CLI" if demos is not None else (
        "generator.EXAMPLES_NEEDED" if hasattr(gen, "EXAMPLES_NEEDED") else "fallback_3")
    demos = demos if demos is not None else getattr(gen, "EXAMPLES_NEEDED", 3)
    if type(demos) is not int or demos < 1:
        raise ValueError("demo count must be a positive integer")
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    rule_texts = set()
    with canonical_path(root).open() as handle:
        for line in handle:
            row = json.loads(line) if line.strip() else {}
            if row.get("task_id") == TASK_ID:
                rule_texts.add(row.get("program_solution"))
    if len(rule_texts) != 1 or not all(isinstance(x, str) and x for x in rule_texts):
        raise ValueError("canonical task must have one unambiguous rule text")
    canonical_rows = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
                       "input": p["input"], "input_sha256": digest(p["input"]),
                       "features": extract_features(p["input"])} for p in pairs]
    report = {"schema": "d7f13ee34d85-canonical-behavior-support-v1", "task_id": TASK_ID,
              "status": "pending", "generator_file": str(source), "generator_sha256": source_hash,
              "canonical_program_text_sha256": hashlib.sha256(next(iter(rule_texts)).encode()).hexdigest(),
              "rule_hash_basis": "exact canonical program_solution text, before runtime lambda wrapping",
              "canonical_pairs_sha256": digest(pairs),
              "gate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "reference_executed": False, "verdict_scope": "finite_input_behavior_support_only",
              "limitation": "No output labels computed. Finite support is not a universal or identifiability claim. "
                            "A rare branch may be missed; ordered windows are raw, not runner-accepted lessons.",
              "demos": demos, "demos_source": demos_source, "lesson_target_features": list(lesson_target_features),
              "request": {"samples_per_band": samples, "lessons_per_band": lessons, "bands": list(bands),
                          "seed": seed, "ordinary_sample_index": sample_index, "lesson_stride": lesson_stride},
              "schedule": {"ordinary": "seed=base_seed+i, fixed requested sample_index",
                           "lessons": "seed=sha256(task_id:behavior:base_seed:band:i)[:8], start=sample_index+i*stride; "
                                      "demos are consecutive, query follows demos"},
              "canonical": summarize(canonical_rows), "bands": {}, "errors": [],
              "missing_ordinary_support": [], "missing_lesson_targets": []}
    required = [f for f, n in report["canonical"]["feature_counts"].items() if n]
    all_draws = []

    def draw(band, draw_seed, index, **identity):
        row = {"band": band, "seed": draw_seed, "sample_index": index, **identity}
        try:
            grid = normalize_grid(gen.generate(draw_seed, index, difficulty=None if band == "default" else band))
            row.update(input=grid, input_sha256=digest(grid), features=extract_features(grid))
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
            report["errors"].append({**row})
        all_draws.append(row)
        return row

    for band in bands:
        ordinary = summarize([draw(band, seed + i, sample_index, kind="ordinary", draw_index=i) for i in range(samples)])
        lesson_rows, lesson_draws = [], []
        for i in range(lessons):
            lesson_seed = int(hashlib.sha256(f"{TASK_ID}:behavior:{seed}:{band}:{i}".encode()).hexdigest()[:8], 16)
            start = sample_index + i * lesson_stride
            draws = [draw(band, lesson_seed, start + j, kind="lesson", lesson_index=i,
                          role="demo" if j < demos else "query", pair_index=j) for j in range(demos + 1)]
            lesson_draws.extend(draws)
            demo_features = {f: any(r.get("features", {}).get(f, False) for r in draws[:demos]) for f in FEATURES}
            query_features = draws[-1].get("features", dict.fromkeys(FEATURES, False))
            lesson_rows.append({"lesson_index": i, "seed": lesson_seed, "start_sample_index": start,
                                "complete": all("features" in r for r in draws),
                                "demo_features": demo_features, "query_features": query_features,
                                "draws": [{k: v for k, v in r.items() if k != "input"} for r in draws]})
            for f in lesson_target_features:
                if not demo_features[f]:
                    report["missing_lesson_targets"].append({"band": band, "lesson_index": i, "feature": f})
        lesson_summary = summarize(lesson_draws)
        lesson_summary.pop("draws")
        lesson_summary.update(requested_windows=lessons, complete_windows=sum(r["complete"] for r in lesson_rows),
                              zero_demo_windows={f: sum(not r["demo_features"][f] for r in lesson_rows) for f in FEATURES},
                              query_support_windows={f: sum(r["query_features"][f] for r in lesson_rows) for f in FEATURES},
                              query_only_windows={f: sum(r["query_features"][f] and not r["demo_features"][f]
                                                        for r in lesson_rows) for f in FEATURES}, windows=lesson_rows)
        report["bands"][band] = {"ordinary": ordinary, "lessons": lesson_summary}
        for feature in required:
            if not ordinary["feature_counts"][feature]:
                report["missing_ordinary_support"].append({"band": band, "feature": feature})
    report["generated_input_calls"] = len(all_draws)
    report["unique_generated_inputs"] = len({r["input_sha256"] for r in all_draws if "input_sha256" in r})
    report["generator_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    if not report["generator_unchanged"]:
        report["errors"].append({"error": "generator source changed during audit"})
    report["status"] = "error" if report["errors"] else (
        "fail" if report["missing_ordinary_support"] or report["missing_lesson_targets"] else "pass")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=find_root(__file__))
    parser.add_argument("--generator-file", type=Path)
    parser.add_argument("--samples", type=int, default=20, help="ordinary inputs per band (default 20)")
    parser.add_argument("--lessons", type=int, default=10, help="raw ordered windows per band (default 10)")
    parser.add_argument("--bands", nargs="+", choices=("default", "easy", "medium", "hard"),
                        default=["default", "easy", "medium", "hard"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--demos", type=int, help="default generator.EXAMPLES_NEEDED, or fallback 3")
    parser.add_argument("--lesson-stride", type=int, default=17)
    parser.add_argument("--lesson-target-feature", action="append", choices=FEATURES, default=[])
    parser.add_argument("--out", type=Path, help="new JSON evidence file (otherwise stdout)")
    args = parser.parse_args(argv)
    if args.out and args.out.exists():
        parser.error("--out must be a new path")
    kwargs = vars(args).copy()
    out = kwargs.pop("out")
    kwargs["lesson_target_features"] = kwargs.pop("lesson_target_feature")
    try:
        report = audit(**kwargs)
    except Exception as error:
        report = {"status": "error", "error": f"{type(error).__name__}: {error}"}
    report.update(cwd=str(Path.cwd()), command=[sys.executable, str(Path(__file__).resolve()), *(sys.argv[1:] if argv is None else argv)])
    code = {"pass": 0, "fail": 1, "error": 2}[report["status"]]
    report["exit_code"] = code
    rendered = json.dumps(report, indent=2) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
        print(json.dumps({"status": report["status"], "exit_code": code, "report": str(out)}))
    else:
        print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

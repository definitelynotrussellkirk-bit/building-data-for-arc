#!/usr/bin/env python3
"""Sample puzzle generators one at a time for hand-cleaning review.

The point of this tool is to slow me down. Each invocation prints ONE (or
a small N) generator's source plus a single sample input grid, then
prints the REVIEW CHECKLIST to stderr — re-stating the rules every time
so I don't drift back into bulk-replace mode.

Usage:
    python scripts/sample_generator.py                      # one random generator
    python scripts/sample_generator.py -n 3                 # three at a time
    python scripts/sample_generator.py --seed 42            # reproducible pick
    python scripts/sample_generator.py --tid 7bb4cfc1       # specific generator
    python scripts/sample_generator.py --grep paint_at      # filter by source content

The review checklist always prints. There is no flag to suppress it.
That's the whole point of this script — see the rules every time.
"""
from __future__ import annotations

import argparse
import ast
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PER_PUZZLE = ROOT / "puzzle_generators" / "per_puzzle"


def discover_generators() -> list[Path]:
    """All generator.py files in puzzle_generators/per_puzzle/."""
    return sorted(p for p in PER_PUZZLE.rglob("generator.py")
                  if "__pycache__" not in str(p))


def read_task_id(p: Path) -> str:
    """Read a literal task id, resolving simple top-level constant aliases."""
    tree = ast.parse(p.read_text(), filename=str(p))
    assignments: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assignments[node.target.id] = node.value

    def resolve(name: str, seen: frozenset[str] = frozenset()) -> str:
        if name in seen:
            raise ValueError(f"cyclic task-id alias in {p}: {name}")
        value = assignments.get(name)
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
        if isinstance(value, ast.Name):
            return resolve(value.id, seen | {name})
        raise ValueError(f"unresolved task-id constant in {p}: {name}")

    if "TASK_ID" not in assignments:
        return p.parent.name
    return resolve("TASK_ID")


def render_one(p: Path, *, seed: int = 0, sample_index: int = 0) -> tuple[str, str]:
    """Return (header, body). Body is generator source + a sample input grid."""
    tid = read_task_id(p)
    src = p.read_text()
    header = f"{p.parent.name}  task_id={tid}"

    # Try to render one sample input (no rule application — just generator output).
    sample = "(skipped)"
    try:
        from puzzle_generators.runner import _load_bundle
        bundle = _load_bundle(tid)
        inp = bundle.generator_module.generate(seed=seed, sample_index=sample_index)
        rows = ["".join(str(v) if v else "." for v in row) for row in inp]
        sample = "\n".join(rows)
    except Exception as e:
        sample = f"(generator raised: {type(e).__name__}: {str(e)[:120]})"

    body = f"--- source ({p.relative_to(ROOT)}) ---\n{src}\n" \
           f"--- sample input  seed={seed}  si={sample_index} ---\n{sample}\n"
    return header, body


_REVIEW_CHECKLIST = """\
╔══════════════════════════════════════════════════════════════════════════════╗
║                  GENERATOR CLEANING — READ EVERY TIME                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  GOAL: a CONSISTENT VOCABULARY across generators + their Racket rules,    ║
║  so reading one tells you what the other does. DRY for understanding.     ║
║                                                                            ║
║  ─────────  THE RULES THAT KEEP GETTING BROKEN  ─────────────────────────  ║
║                                                                            ║
║  🛑 1. NEVER batch / mass-replace across files. Open ONE generator, edit   ║
║         it by hand with my own eyes. Move on. No Python loops that mutate  ║
║         many files at once, even with smoke tests.                         ║
║                                                                            ║
║  🛑 2. NEVER invent work. If the user didn't ask for X, don't do X. Don't  ║
║         file tasks. Don't extend a small request into a sweep.             ║
║                                                                            ║
║  🛑 3. NEVER touch grounded_rules.py / arc-prelude.rkt / DSL docs in bulk. ║
║                                                                            ║
║  ─────────  WHAT GOOD CLEANING LOOKS LIKE  ──────────────────────────────  ║
║                                                                            ║
║  4. Replace inline shape literals with named constants ONLY when the       ║
║     name carries geometric meaning the literal hides:                      ║
║       PLUS_5, RING_3X3, H_LINE_3, V_LINE_3, SQUARE_2X2, T_TETROMINO,       ║
║       L_TROMINO_NE/NW/SE/SW (4 orientations), CARDINAL_DELTAS, ...         ║
║     Defined in puzzle_generators/helpers/shape.py.                          ║
║                                                                            ║
║  5. Replace ad-hoc helpers with the canonical Python ones that mirror      ║
║     the Racket vocab:                                                      ║
║       _put(g, top, left, cells, color)   →  paint_at(g, r0, c0, cells, color)
║       _draw_frame(g, r1, c1, r2, c2, ...) →  draw_frame(g, r1, c1, r2, c2, color)
║       solid-rect double-loop              →  fill_box(g, r1, c1, r2, c2, color)
║       paint_cells, random_free_cell, place_no_overlap(padding=N), ...      ║
║                                                                            ║
║  6. Replace `rng.sample([1,2,3,4,5,6,7,8,9], n)` with                      ║
║     `random_palette(rng, n)` (excludes bg=0 by default).                  ║
║                                                                            ║
║  7. After any edit: smoke this one generator (5 seeds) before moving on.   ║
║     Do not commit until smoke passes.                                      ║
║                                                                            ║
║  ─────────  HOW TO DECIDE WHEN TO SKIP A FILE  ──────────────────────────  ║
║                                                                            ║
║  8. If the helper has a fundamentally different shape (e.g., grid-patch    ║
║     paste, or _draw_frame with rh/rw instead of corners), leave it.        ║
║                                                                            ║
║  9. If a literal appears once with no clear geometric meaning, leave it.   ║
║     The named constant has to be CLEARER than the literal to be worth it.  ║
║                                                                            ║
║ 10. If cleaning would force me to change call-site arity (e.g., adding a   ║
║     color arg the helper had as default), it's a hand-edit, not a sub.    ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝"""


def main():
    parser = argparse.ArgumentParser(description="Sample one generator at a time for cleaning")
    parser.add_argument("-n", type=int, default=1,
                        help="number of generators to sample (default 1)")
    parser.add_argument("--seed", type=int, default=None,
                        help="RNG seed for reproducible sampling")
    parser.add_argument("--gen-seed", type=int, default=0,
                        help="seed passed to generate() (default 0)")
    parser.add_argument("--si", type=int, default=0,
                        help="sample_index passed to generate() (default 0)")
    parser.add_argument("--tid", type=str, default=None,
                        help="specific task_id to render (skips sampling)")
    parser.add_argument("--grep", type=str, default=None,
                        help="filter to generators whose source contains this substring")
    parser.add_argument("--smoke", type=int, default=0, metavar="N",
                        help="after rendering, smoke each generator with N seeds "
                             "through a persistent Racket bridge (one bridge per "
                             "generator). 0 = skip smoke (default).")
    parser.add_argument("--show-rule", action="store_true",
                        help="print the canonical Racket rule body next to the "
                             "generator source. Read from "
                             "data/canonical/puzzles.jsonl.")
    parser.add_argument("--full-rule", action="store_true",
                        help="like --show-rule but does not truncate long rules.")
    args = parser.parse_args()

    gens = discover_generators()

    if args.tid:
        gens = [p for p in gens if read_task_id(p) == args.tid or p.parent.name == args.tid]
        if not gens:
            print(f"no generator matching tid={args.tid!r}", file=sys.stderr)
            sys.exit(1)
    elif args.grep:
        gens = [p for p in gens if args.grep in p.read_text()]
        if not gens:
            print(f"no generators containing {args.grep!r}", file=sys.stderr)
            sys.exit(1)

    rng_seed = args.seed if args.seed is not None else random.randint(1000, 99999)
    rng = random.Random(rng_seed)
    sample = rng.sample(gens, min(args.n, len(gens)))

    print(f"# rng_seed={rng_seed}  n={len(sample)}/{len(gens)}  "
          f"gen_seed={args.gen_seed}  si={args.si}")
    print()

    for i, p in enumerate(sample, start=1):
        header, body = render_one(p, seed=args.gen_seed, sample_index=args.si)
        sep = "=" * 78
        print(sep)
        print(f"[{i}/{len(sample)}] {header}")
        print(sep)
        if args.show_rule or args.full_rule:
            tid = read_task_id(p)
            rule = _load_rule_body(tid)
            if rule is not None:
                if not args.full_rule and len(rule) > 1500:
                    rule = rule[:1500] + "\n... [truncated; --full-rule for all]"
                print(f"--- rule body ({tid}) ---\n{rule}\n")
        print(body)
        if args.smoke > 0:
            print(_smoke_one(p, n_seeds=args.smoke))

    # Always print the checklist — both stdout and stderr — so it shows up
    # whether output is piped, tee'd, or redirected. There is intentionally
    # no flag to suppress it.
    print(_REVIEW_CHECKLIST)
    print(_REVIEW_CHECKLIST, file=sys.stderr)


_RULE_INDEX: dict[str, str] | None = None


def _load_rule_body(tid: str) -> str | None:
    """Look up `task_id`'s canonical Racket rule from
    data/canonical/puzzles.jsonl. Returns the program_solution string
    or None if missing. Cached on first call."""
    global _RULE_INDEX
    if _RULE_INDEX is None:
        import json
        path = ROOT / "data" / "canonical" / "puzzles.jsonl"
        idx: dict[str, str] = {}
        if path.exists():
            with path.open() as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    rid = row.get("task_id")
                    sol = row.get("program_solution")
                    if rid and sol and rid not in idx:
                        idx[rid] = sol
        _RULE_INDEX = idx
    return _RULE_INDEX.get(tid)


def _smoke_one(p: Path, *, n_seeds: int) -> str:
    """Run N seeds through one persistent Racket bridge for this generator.

    A fresh `run_one` call costs a Racket cold-start (~1-3s); reusing
    the bridge across seeds drops per-seed cost to ~0.2-0.5s. Returns
    a one-line PASS/FAIL summary."""
    tid = read_task_id(p)
    try:
        from puzzle_generators.runner import _load_bundle, _open_bridge_with_rule, run_one
        bundle = _load_bundle(tid)
        bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    except Exception as e:
        return f"--- smoke (skipped: {type(e).__name__}: {str(e)[:120]}) ---"
    results = []
    for s in range(n_seeds):
        try:
            r = run_one(tid, seed=s, sample_index=0, n_train=2, n_test=1,
                        bundle=bundle, bridge=bridge, fn_name=fn_name)
            ok = bool(r and r.get("train"))
        except Exception as e:
            results.append(f"{s}:ERR({type(e).__name__})")
            continue
        results.append(f"{s}:{'OK' if ok else 'FAIL'}")
    summary = " ".join(results)
    n_ok = sum(1 for r in results if r.endswith(":OK"))
    return f"--- smoke {n_ok}/{n_seeds} ---\n{summary}\n"


if __name__ == "__main__":
    main()

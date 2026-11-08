#!/usr/bin/env python3
"""make_data.py — generate training data from SAFE-tagged generators ONLY.

Every row is produced by a reviewed_safe generator (drawn ∝ its recommended
mix weight) and every output is derived by executing the task's canonical
Racket rule — then validated against the qwen9b row contract. There is no
flag that lets you draw anything else.

Styles:
  grids     {"task_id", "train", "test", ...}   — ARC episode pairs
  code      {"task_id", "kind": "synth", "train", "program", ...} — demos -> Racket rule
  episodes  full raw instance rows (pairs + program + facts, contract v1)

Renders (for grids + code):
  raw       the JSONL rows above (default)
  chatml    {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}
  harmony   gpt-oss harmony text (<|start|>user<|message|>...<|channel|>final...)

Examples:
  python3 teammate/make_data.py --style grids --count 100 --seed 1
  python3 teammate/make_data.py --style grids --render chatml --count 100
  python3 teammate/make_data.py --style code --render harmony --count 50
  python3 teammate/make_data.py --style episodes --tasks 5 --instances-per-task 4
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

DEFAULT_POOL = ROOT / "qwen9b/colab/assets/safe_pool.json"
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def load_pool(path: Path) -> dict[str, float]:
    if not path.exists():
        print(f"safe pool missing at {path} — building it now "
              f"(qwen9b/build_safe_pool.py)", flush=True)
        subprocess.run([sys.executable, str(ROOT / "qwen9b/build_safe_pool.py")],
                       check=True, cwd=ROOT)
    pool = {k: float(v) for k, v in json.loads(path.read_text()).items()}
    if not pool:
        raise SystemExit("LOUD: safe pool is empty — nothing is safe to generate from")
    return pool


def load_canonical_index(path: Path) -> dict[str, dict]:
    index: dict[str, dict] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row.get("task_id")
            if task_id and (row.get("program_solution") or "").strip():
                index.setdefault(task_id, row)
    return index


def style_row(style: str, raw: dict) -> dict:
    """Project a validated raw instance row into the requested teammate style."""
    base = {
        "task_id": raw["task_id"],
        "seed": raw["seed"],
        "sample_index": raw["sample_index"],
        "split_group": raw["split_group"],
        "generator_version": raw["generator_version"],
    }
    if style == "grids":
        return {**base, "train": raw["train"], "test": raw["test"],
                "program_hash": raw["program_hash"]}
    if style == "code":
        return {**base, "kind": "synth", "train": raw["train"],
                "program": raw["program"], "program_hash": raw["program_hash"]}
    if style == "episodes":
        return raw
    raise ValueError(f"unknown style {style!r}")


# --- chat renders (torch-free local serializer; same layouts as DATA_CONTRACT) --
DEFAULT_SYSTEM_PROMPTS = {
    "grids": "You are an expert ARC-AGI reasoning agent. Predict the output grid corresponding to the query input grid.",
    "code": "You are an expert ARC-AGI reasoning agent. Synthesize a correct, verified Racket DSL program that solves the grid transformation puzzle.",
}


def _grid_text(grid) -> str:
    return "".join("".join(str(int(v)) for v in line) + "\n" for line in grid)


def prompt_target(raw: dict, style: str, fence: bool = False) -> tuple[str, str]:
    """(prompt, target) in the DATA_CONTRACT text layout for the style."""
    demos = []
    for pair_id, pair in enumerate(raw["train"]):
        demos.append(f"pair {pair_id} in\n{_grid_text(pair['input'])}"
                     f"pair {pair_id} out\n{_grid_text(pair['output'])}")
    query_in = _grid_text(raw["test"][0]["input"])
    if style == "grids":
        prompt = "mode predict\n" + "".join(demos) + f"query in\n{query_in}answer\n"
        return prompt, _grid_text(raw["test"][0]["output"])
    if style == "code":
        prompt = "mode synth\n" + "".join(demos) + "program\n"
        prog = raw["program"].strip()
        if fence:
            target = f"```racket\n{prog}\n```\n"
        else:
            target = f"{prog}\n"
        return prompt, target
    raise ValueError(f"style {style!r} has no chat render")


def chat_row(render: str, style: str, raw: dict, system_prompt: str = "",
             fence: bool = False) -> dict:
    base = {
        "task_id": raw["task_id"],
        "seed": raw["seed"],
        "sample_index": raw["sample_index"],
        "split_group": raw["split_group"],
        "objective": "predict" if style == "grids" else "synth",
    }
    prompt, target = prompt_target(raw, style, fence=fence)
    if render == "chatml":
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": target})
        return {**base, "messages": messages}
    if render == "harmony":
        system_part = f"<|start|>system<|message|>{system_prompt}<|end|>" if system_prompt else ""
        text = (f"{system_part}<|start|>user<|message|>{prompt}<|end|>"
                f"<|start|>assistant<|channel|>final<|message|>{target}<|end|>")
        return {**base, "text": text}
    raise ValueError(f"unknown render {render!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style", choices=("grids", "code", "episodes"),
                        default="grids")
    parser.add_argument("--render", choices=("raw", "chatml", "harmony"),
                        default="raw",
                        help="raw = JSONL rows; chatml = {messages:[user,assistant]}; "
                             "harmony = gpt-oss harmony text. Chat renders apply to "
                             "grids (predict) and code (synth); episodes is raw-only")
    parser.add_argument("--system-prompt", default="",
                        help="optional system prompt for chat renders (chatml/harmony)")
    parser.add_argument("--default-system-prompt", action="store_true",
                        help="use standard default system prompt for the style")
    parser.add_argument(
        "--fence",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=("wrap synthesized Racket programs in Markdown code blocks for "
              "display exports (default: false; training targets stay raw)"),
    )
    parser.add_argument("--count", type=int, default=100,
                        help="total rows to emit (0 = one batch per task)")
    parser.add_argument("--tasks", type=int, default=0,
                        help="limit to the first N pool tasks (debug; default: all)")
    parser.add_argument("--instances-per-task", type=int, default=2,
                        help="rows drawn per task visit")
    parser.add_argument("--seed", type=int, default=20260724)
    parser.add_argument("--exclude-eval-seed", type=int, default=None,
                        help="drop every task whose FAMILY falls in the "
                             "score.py make-eval holdout for this seed, so "
                             "training data stays family-disjoint from that "
                             "eval set")
    parser.add_argument("--holdout-frac", type=float, default=0.2,
                        help="must match the fraction used by score.py "
                             "make-eval when --exclude-eval-seed is given")
    parser.add_argument("--pool", default=str(DEFAULT_POOL))
    parser.add_argument("--canonical", default=str(CANONICAL))
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    from puzzle_generators.runner import run_batch
    from qwen9b.instance_rows import make_instance_row

    pool = load_pool(Path(args.pool))
    canonical = load_canonical_index(Path(args.canonical))
    tasks = sorted(t for t in pool if t in canonical)
    excluded_eval = 0
    if args.exclude_eval_seed is not None:
        from score import _family_in_holdout
        kept = []
        for t in tasks:
            fam = (canonical[t].get("parent_hash")
                   or canonical[t].get("content_hash") or t)
            if _family_in_holdout(fam, args.exclude_eval_seed,
                                  args.holdout_frac):
                excluded_eval += 1
            else:
                kept.append(t)
        tasks = kept
        print(f"excluded {excluded_eval} eval-holdout task(s) for eval seed "
              f"{args.exclude_eval_seed} (frac {args.holdout_frac})",
              flush=True)
    if args.tasks:
        tasks = tasks[: args.tasks]
    if not tasks:
        raise SystemExit("LOUD: no pool tasks have canonical rules")
    weights = [pool[t] for t in tasks]

    out_path = Path(args.out) if args.out else (
        ROOT / "teammate" / "out" / f"data_{args.style}_{args.render}_seed{args.seed}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    system_prompt = args.system_prompt
    if args.default_system_prompt and not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPTS.get(args.style, "")

    rng = random.Random(args.seed)
    target = args.count or len(tasks) * args.instances_per_task
    if args.render != "raw" and args.style == "episodes":
        raise SystemExit("LOUD: episodes style is raw-only; use --style grids or code "
                         "with --render chatml/harmony")
    produced = rejected = 0
    seen_tasks: set[str] = set()
    with out_path.open("w") as handle:
        while produced < target:
            task_id = rng.choices(tasks, weights=weights, k=1)[0]
            seed = rng.getrandbits(31)
            try:
                instances = run_batch(
                    task_id,
                    args.instances_per_task,
                    n_train=4,
                    n_test=1,
                    seed_start=seed,
                )
            except Exception as exc:  # per-task failure: loud, counted, continue
                rejected += 1
                print(f"LOUD: rejected {task_id}: {type(exc).__name__}: {exc}",
                      file=sys.stderr, flush=True)
                continue
            for instance in instances:
                if produced >= target:
                    break
                raw = make_instance_row(
                    task_id, canonical[task_id], instance,
                    where=f"teammate:{task_id}:{produced}",
                )
                if args.render == "raw":
                    row = style_row(args.style, raw)
                else:
                    row = chat_row(args.render, args.style, raw,
                                   system_prompt=system_prompt, fence=args.fence)
                handle.write(json.dumps(row, separators=(",", ":")) + "\n")
                produced += 1
                seen_tasks.add(task_id)

    summary = {
        "style": args.style,
        "render": args.render,
        "rows": produced,
        "tasks_used": len(seen_tasks),
        "task_rejections": rejected,
        "excluded_eval_tasks": excluded_eval,
        "seed": args.seed,
        "pool": str(args.pool),
        "out": str(out_path),
    }
    if args.render != "raw":
        summary["fence"] = args.fence
        if system_prompt:
            summary["system_prompt"] = system_prompt
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

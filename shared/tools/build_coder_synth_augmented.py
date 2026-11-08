"""Build a GENERATOR-AUGMENTED program-synthesis SFT dataset.

The base builder (`build_coder_synth_dataset.py`) emits ONE chat example per
canonical task: a single fixed demo set -> the verified Racket program. That
starves the coder — each program is seen exactly once. But every canonical task
that has a per-puzzle generator can produce UNLIMITED demo-set variants (the
generator draws new input grids; piping them through the canonical Racket rule
yields verified output grids). The PROGRAM target is identical across variants;
only the example grids change. So we can multiply the corpus K-fold with genuine
demo diversity, teaching the demos->program mapping far more robustly.

This script reuses the base builder's chat format, split-group key, and bucketing
verbatim (DRY) — the ONLY change is the source of the demo pairs:
`puzzle_generators.runner.run_batch` (canonical-verified) instead of the fixed
canonical `train`.

Family split is preserved: all variants of a task share `split_group_key(row)`,
so generated variants never leak across train/val.

    # small smoke
    python3 scripts/build_coder_synth_augmented.py \
        --variants-per-task 2 --limit 20 --out-dir data/coder_synth_aug

    # full
    python3 scripts/build_coder_synth_augmented.py \
        --variants-per-task 16 --out-dir data/coder_synth_aug --include-canonical
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Reuse the base builder verbatim (DRY): chat format, split key, bucketing.
from build_coder_synth_dataset import (  # noqa: E402
    CANONICAL,
    build_example,
    split_group_key,
    _demos_block,
    _bucket,
)
from build_qwen_sft_dataset import convert_grid_to_string  # noqa: E402

# NVARC-style direct grid prediction: demos + query input -> raw output grid.
NVARC_SYSTEM = (
    "You solve ARC puzzles by predicting the OUTPUT GRID directly. Given training "
    "examples (input grid -> output grid), infer the single transformation and apply "
    "it to the query input. Grids are rows of digits 0-9 (0 = background). Respond "
    "with ONLY the output grid, nothing else."
)


def _grid_example(canon_row, train_pairs, query_pair, *, split_group) -> dict | None:
    """demos + a query input -> the query OUTPUT grid (NVARC-style direct prediction)."""
    if not train_pairs or not query_pair:
        return None
    user = (
        f"{_demos_block(train_pairs)}\n\n"
        f"QUERY INPUT:\n{convert_grid_to_string(query_pair['input'])}\n\n"
        "Apply the transformation. Output ONLY the result grid."
    )
    return {
        "task_id": canon_row.get("task_id"),
        "content_hash": canon_row.get("content_hash"),
        "source": canon_row.get("source"),
        "parent_hash": canon_row.get("parent_hash"),
        "split_group": split_group,
        "stream": "nvarc_grid",
        "messages": [
            {"role": "system", "content": NVARC_SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": convert_grid_to_string(query_pair["output"])},
        ],
    }
from puzzle_generators.runner import (  # noqa: E402
    run_one,
    _load_bundle,
    _open_bridge_with_rule,
)

PER_PUZZLE = ROOT / "puzzle_generators" / "per_puzzle"


def _has_generator(task_id: str) -> bool:
    return (PER_PUZZLE / str(task_id) / "generator.py").exists()


def _synthetic_row(canon_row: dict, train_pairs: list) -> dict:
    """A canonical-shaped row carrying GENERATED demos + the canonical program,
    so `build_example` formats it identically to a real canonical row."""
    return {
        "task_id": canon_row.get("task_id"),
        "content_hash": canon_row.get("content_hash"),
        "source": canon_row.get("source"),
        "parent_hash": canon_row.get("parent_hash"),
        "program_solution": canon_row.get("program_solution"),
        "train": train_pairs,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", default=str(CANONICAL))
    ap.add_argument("--out-dir", default="data/coder_synth_aug")
    ap.add_argument("--target-mode", choices=("program", "grid"), default="program",
                    help="program: demos->Racket program; grid: demos+query->output grid (NVARC-style)")
    ap.add_argument("--variants-per-task", type=int, default=16,
                    help="generated demo-set variants per task (each shares the program target)")
    ap.add_argument("--min-demos", type=int, default=3)
    ap.add_argument("--max-demos", type=int, default=6,
                    help="demos per variant drawn uniformly in [min-demos, max-demos]")
    ap.add_argument("--split-key", default="family", choices=("family", "task", "content"))
    ap.add_argument("--val-frac", type=float, default=0.05)
    ap.add_argument("--include-canonical", action="store_true",
                    help="also emit the original fixed-demo canonical example per task")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="cap #tasks (0=all)")
    ap.add_argument("--start-idx", type=int, default=0,
                    help="first canonical-row index (for parallel sharding)")
    ap.add_argument("--end-idx", type=int, default=0,
                    help="last canonical-row index exclusive (0=to end; for sharding)")
    ap.add_argument("--progress-every", type=int, default=50)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    val_cut = int(round(a.val_frac * 1000))

    rows = []
    with open(a.canonical) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    # Shard window for parallel runs (applied before --limit).
    start = max(0, a.start_idx)
    end = a.end_idx if a.end_idx > 0 else len(rows)
    rows = rows[start:end]
    if a.limit:
        rows = rows[: a.limit]

    train_f = (out_dir / "train.jsonl").open("w")
    val_f = (out_dir / "val.jsonl").open("w")

    groups_by_split = defaultdict(set)
    n_tasks = n_with_gen = n_examples = n_train = n_val = 0
    n_underproduced = n_no_program = 0
    # FAIL LOUD: every skipped variant/task is recorded with its reason (never a
    # silent `continue`). Reasons + first example written to rejections.jsonl.
    rejections: Counter = Counter()
    reject_first: dict[str, str] = {}
    rej_f = (out_dir / "rejections.jsonl").open("w")

    def _reject(reason: str, task_id: str, detail: str = ""):
        rejections[reason] += 1
        if reason not in reject_first:
            reject_first[reason] = f"{task_id}: {detail}"
        rej_f.write(json.dumps({"reason": reason, "task_id": task_id, "detail": detail}) + "\n")

    t0 = time.time()

    for idx, row in enumerate(rows):
        program = (row.get("program_solution") or "").strip()
        task_id = row.get("task_id")
        if not program:
            n_no_program += 1
            continue
        n_tasks += 1
        split_group = split_group_key(row, a.split_key)
        split = "val" if _bucket(split_group) < val_cut else "train"
        out_f = val_f if split == "val" else train_f

        examples: list[dict] = []

        # 1) optional original canonical fixed-demo example
        if a.include_canonical:
            ex = build_example(row, split_group=split_group, min_demos=a.min_demos)
            if ex is not None:
                examples.append(ex)

        # 2) generator-augmented variants (verified against the canonical rule).
        # Open the Racket bridge + generator bundle ONCE per task and reuse it
        # across all K variants (a fresh bridge per variant would dominate cost).
        if a.variants_per_task > 0 and _has_generator(task_id):
            n_with_gen += 1
            seed_start = a.seed * 1_000_003 + (start + idx) * 101
            produced = 0
            bridge = bundle = fn_name = None
            try:
                bundle = _load_bundle(task_id)
                bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
            except Exception as e:
                bridge = None
                _reject(f"bridge_open:{type(e).__name__}", task_id, str(e)[:160])
            if bridge is not None:
                try:
                    n_test_v = 1 if a.target_mode == "grid" else 0
                    for v in range(a.variants_per_task):
                        n_train_v = rng.randint(a.min_demos, a.max_demos)
                        try:
                            inst = run_one(task_id, seed=seed_start + v, sample_index=0,
                                           n_train=n_train_v, n_test=n_test_v,
                                           bundle=bundle, bridge=bridge, fn_name=fn_name)
                        except Exception as e:
                            # generator under-produced / raised — record LOUDLY, don't swallow
                            _reject(f"run_one:{type(e).__name__}", task_id, str(e)[:160])
                            continue
                        if a.target_mode == "grid":
                            test = inst.get("test") or []
                            ex = _grid_example(row, inst.get("train") or [],
                                               test[0] if test else None, split_group=split_group)
                        else:
                            syn = _synthetic_row(row, inst.get("train") or [])
                            ex = build_example(syn, split_group=split_group, min_demos=a.min_demos)
                        if ex is not None:
                            examples.append(ex)
                            produced += 1
                finally:
                    try:
                        bridge.shutdown()
                    except Exception as e:
                        _reject(f"bridge_shutdown:{type(e).__name__}", task_id, str(e)[:160])
            if produced == 0:
                n_underproduced += 1
                _reject("task_underproduced", task_id, "0 variants produced")

        for ex in examples:
            out_f.write(json.dumps(ex) + "\n")
            n_examples += 1
            groups_by_split[split_group].add(split)
            if split == "val":
                n_val += 1
            else:
                n_train += 1

        if a.progress_every and (idx + 1) % a.progress_every == 0:
            dt = time.time() - t0
            print(f"[{idx+1}/{len(rows)}] tasks={n_tasks} with_gen={n_with_gen} "
                  f"examples={n_examples} (train={n_train} val={n_val}) "
                  f"{n_examples/max(dt,1e-9):.1f} ex/s", flush=True)

    train_f.close()
    val_f.close()
    rej_f.close()

    leaking = [g for g, s in groups_by_split.items() if len(s) > 1]
    summary = {
        "canonical_rows_read": len(rows),
        "tasks_with_program": n_tasks,
        "tasks_with_generator": n_with_gen,
        "tasks_no_program": n_no_program,
        "tasks_generator_underproduced": n_underproduced,
        "variants_per_task": a.variants_per_task,
        "demos_range": [a.min_demos, a.max_demos],
        "include_canonical": a.include_canonical,
        "examples_total": n_examples,
        "train_examples": n_train,
        "val_examples": n_val,
        "split_groups": len(groups_by_split),
        "leaking_split_groups": len(leaking),
        "rejections_total": int(sum(rejections.values())),
        "rejections_by_reason": dict(rejections),
        "rejections_first_example": reject_first,
        "elapsed_s": round(time.time() - t0, 1),
    }
    (out_dir / "augmented_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    # FAIL LOUD: surface rejections + leakage on stderr so they can't pass unnoticed.
    if rejections:
        print(f"LOUD: {sum(rejections.values())} rejections recorded -> {out_dir}/rejections.jsonl",
              file=sys.stderr)
        for reason, cnt in rejections.most_common():
            print(f"  {cnt:6d}  {reason}   (first: {reject_first.get(reason,'')})", file=sys.stderr)
    if leaking:
        print(f"LOUD: {len(leaking)} split groups leak across train/val", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

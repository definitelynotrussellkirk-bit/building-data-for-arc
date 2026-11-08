"""Build a PROGRAM-SYNTHESIS SFT dataset: ARC demos -> Racket program.

Distinct from `build_qwen_sft_dataset.py` (which teaches a model to emit raw
OUTPUT GRIDS). Here the target is the verified Racket `program_solution` — we
teach a coding model to write the DSL program that solves the task, which is
then EXECUTABLE and VERIFIABLE (run it through the Racket bridge, check pass@2).

Source of truth: `data/canonical/puzzles.jsonl` — almost every row carries a
verified `program_solution`. Grid serialization reuses NVARC's
`convert_grid_to_string` (DRY) so grids look exactly like the raw-grid corpus.

Output: chat-format JSONL ({"messages":[system,user,assistant]}). The default
split is by *family*, not by individual content hash, so generated variants from
the same parent/bank source do not leak across train and validation.

    python3 scripts/build_coder_synth_dataset.py \
        --out-dir data/coder_synth --val-frac 0.05
"""
from __future__ import annotations

import argparse
import json
import zlib
from collections import defaultdict
from pathlib import Path

# Reuse the exact grid serialization the warm base was trained on (DRY).
# Running this file puts scripts/ on sys.path, so the sibling imports bare.
from build_qwen_sft_dataset import convert_grid_to_string

CANONICAL = Path("data/canonical/puzzles.jsonl")

SYSTEM = (
    "You write programs in a Racket-style grid DSL that solve ARC puzzles. "
    "Given training examples (input grid -> output grid), infer the single "
    "transformation rule and emit ONE program of the form "
    "(rule! (lambda (g) ...)) that maps any input grid to its output. "
    "Grids are rows of digits 0-9 (0 = background). Respond with ONLY the "
    "program, no prose."
)


def _demos_block(train_pairs) -> str:
    """Serialize the demo pairs as INPUT/OUTPUT digit grids."""
    chunks = []
    for i, pair in enumerate(train_pairs, 1):
        chunks.append(
            f"Example {i}:\nINPUT:\n{convert_grid_to_string(pair['input'])}\n"
            f"OUTPUT:\n{convert_grid_to_string(pair['output'])}"
        )
    return "\n\n".join(chunks)


def split_group_key(row: dict, mode: str = "family") -> str:
    """Stable split key used to keep related tasks on one side of the split.

    `content_hash` is stable but too fine-grained for validation: the canonical
    corpus contains many bank/generated variants sharing a parent/source and the
    same solution family. Splitting those variants independently creates an
    overly rosy validation set. The default `family` key groups bank variants by
    `source`, augmented rows by `parent_hash`, and ordinary canonical rows by
    `task_id` (falling back to `content_hash`).
    """
    if mode == "content":
        return str(row.get("content_hash") or row.get("task_id") or "")
    if mode == "task":
        return str(row.get("task_id") or row.get("content_hash") or "")
    if mode != "family":
        raise ValueError(f"unknown split-key mode: {mode}")
    source = str(row.get("source") or "")
    if source.startswith("bank:"):
        return source
    return str(row.get("parent_hash") or row.get("task_id") or row.get("content_hash") or "")


def build_example(row, *, split_group: str | None = None, min_demos: int = 2) -> dict | None:
    """One canonical row -> one chat SFT example, or None if unusable."""
    program = (row.get("program_solution") or "").strip()
    train_pairs = row.get("train") or []
    if not program or len(train_pairs) < min_demos:
        return None
    user = (
        f"{_demos_block(train_pairs)}\n\n"
        "Write the Racket program that performs this transformation."
    )
    return {
        "task_id": row.get("task_id"),
        "content_hash": row.get("content_hash"),
        "source": row.get("source"),
        "parent_hash": row.get("parent_hash"),
        "split_group": split_group,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": program},
        ],
    }


def _bucket(key: str, mod: int = 1000) -> int:
    """Stable 0..mod-1 bucket from a split key (deterministic split)."""
    return zlib.crc32((key or "").encode()) % mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", default=str(CANONICAL))
    ap.add_argument("--out-dir", default="data/coder_synth")
    ap.add_argument("--val-frac", type=float, default=0.05,
                    help="fraction of split groups held out for validation")
    ap.add_argument("--split-key", choices=["family", "task", "content"], default="family",
                    help="family keeps generated/bank variants from leaking across train/val; "
                         "content reproduces the original content_hash split")
    ap.add_argument("--min-demos", type=int, default=2,
                    help="minimum number of train pairs required for an SFT example")
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    val_cut = int(a.val_frac * 1000)

    n_rows = n_train = n_val = n_skip = 0
    groups_by_split = defaultdict(set)
    group_sizes = defaultdict(int)
    ftr = (out / "train.jsonl").open("w")
    fva = (out / "val.jsonl").open("w")
    with open(a.canonical) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_rows += 1
            row = json.loads(line)
            split_group = split_group_key(row, a.split_key)
            ex = build_example(row, split_group=split_group, min_demos=a.min_demos)
            if ex is None:
                n_skip += 1
                continue
            split = "val" if _bucket(split_group) < val_cut else "train"
            sink = fva if split == "val" else ftr
            sink.write(json.dumps(ex, sort_keys=True) + "\n")
            groups_by_split[split_group].add(split)
            group_sizes[split_group] += 1
            if split == "val":
                n_val += 1
            else:
                n_train += 1
    ftr.close()
    fva.close()

    leaking = sorted(g for g, splits in groups_by_split.items() if len(splits) > 1)
    split_report = {
        "split_key": a.split_key,
        "val_frac": a.val_frac,
        "canonical_rows_read": n_rows,
        "skipped": n_skip,
        "train_examples": n_train,
        "val_examples": n_val,
        "split_groups": len(groups_by_split),
        "leaking_split_groups": len(leaking),
        "largest_groups": sorted(group_sizes.items(), key=lambda kv: kv[1], reverse=True)[:20],
        "leaking_group_examples": leaking[:20],
    }
    (out / "split_report.json").write_text(json.dumps(split_report, indent=2, sort_keys=True))

    print(f"canonical rows read : {n_rows}")
    print(f"  skipped (no program / <{a.min_demos} demos): {n_skip}")
    print(f"  split key     : {a.split_key}")
    print(f"  split groups  : {len(groups_by_split)} (leaking groups={len(leaking)})")
    print(f"  train examples: {n_train} -> {out/'train.jsonl'}")
    print(f"  val examples  : {n_val} -> {out/'val.jsonl'}")
    print(f"  split report  : {out/'split_report.json'}")
    if leaking:
        raise SystemExit("internal split error: split group appeared in both train and val")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

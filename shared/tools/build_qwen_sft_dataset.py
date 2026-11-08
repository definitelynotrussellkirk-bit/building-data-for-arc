#!/usr/bin/env python3
"""Serialize our generators into NVARC-format SFT text for continued MUON-FFT
of the NVARC warm base (sorokin/qwen3_4b_grids15_sft139).

One JSONL row = one ARC episode rendered EXACTLY in NVARC's QwenFormatter text:

    <|im_start|>user\n{input_grid}<|im_end|><|im_start|>assistant\n{output_grid}<|im_end|>   (per demo pair)
    ... then the query pair in the same shape ...

Grids use NVARC's `convert_grid_to_string`: rows of digit-chars, '\n' between
rows. The model already carries the cut (~16-token) tokenizer, so this text is
exactly what it expects. Loss masking (supervise assistant spans only) is the
training script's job — this script only emits text.

Data comes from our existing generator machinery via `puzzle_generators.runner`
(reused, not reinvented).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from puzzle_generators import runner
from scripts.difficulty_sampling import load_weights, weighted_order

IM_START, IM_END = "<|im_start|>", "<|im_end|>"
DEFAULT_GENERATOR_SKILL_MATRIX = (
    REPO_ROOT / "data/derived/official_generator_skill_matrix.jsonl"
)
LINEAGE_POLICIES = ("annotate", "verified-skill-only", "off")


def convert_grid_to_string(grid) -> str:
    """NVARC's exact serialization: digit-chars per row, '\\n' between rows."""
    return "\n".join("".join(str(int(c)) for c in row) for row in grid).strip()


def fmt_pair(inp, out) -> str:
    return (f"{IM_START}user\n{convert_grid_to_string(inp)}{IM_END}"
            f"{IM_START}assistant\n{convert_grid_to_string(out)}{IM_END}")


def fmt_episode(demo_pairs, query_pairs) -> str:
    """Demos then the query pair(s), all in NVARC chat shape (matches fmt_train)."""
    text = "".join(fmt_pair(p["input"], p["output"]) for p in demo_pairs)
    text += "".join(fmt_pair(p["input"], p["output"]) for p in query_pairs)
    return text


def episode_messages(demo_pairs, query_pairs) -> list[dict]:
    """Structured turns so the trainer can mask loss to assistant spans exactly.
    `content` is the bare grid string; the trainer re-wraps with the im_start/
    im_end markers (identical to `fmt_episode`)."""
    msgs: list[dict] = []
    for p in list(demo_pairs) + list(query_pairs):
        msgs.append({"role": "user", "content": convert_grid_to_string(p["input"])})
        msgs.append({"role": "assistant", "content": convert_grid_to_string(p["output"])})
    return msgs


def discover_task_ids(generator_root: Path) -> list[str]:
    paths = sorted(glob.glob(str(generator_root / "puzzle_generators" / "per_puzzle" / "*" / "generator.py")))
    if not paths:  # allow pointing directly at a repo-style tree
        paths = sorted(glob.glob(str(generator_root / "per_puzzle" / "*" / "generator.py")))
    return [Path(p).parent.name for p in paths]


def load_generator_skill_matrix(path: Path) -> dict[str, dict]:
    """Load the fail-closed generator-to-skill materialization by generator ID."""
    result: dict[str, dict] = {}
    ontology_ref: dict | None = None
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
        generator_id = str(row.get("generator_id") or "")
        if not generator_id:
            raise ValueError(f"{path}:{line_number}: missing generator_id")
        if generator_id in result:
            raise ValueError(f"{path}:{line_number}: duplicate generator_id {generator_id}")
        current_ref = row.get("ontology_ref")
        if not isinstance(current_ref, dict) or not current_ref.get("ontology_sha256"):
            raise ValueError(f"{path}:{line_number}: missing ontology_ref")
        if ontology_ref is None:
            ontology_ref = current_ref
        elif current_ref != ontology_ref:
            raise ValueError(f"{path}:{line_number}: mixed ontology versions")
        if row.get("candidate_claims_do_not_count") is not True:
            raise ValueError(
                f"{path}:{line_number}: candidate_claims_do_not_count must be true"
            )
        result[generator_id] = row
    return result


def lineage_is_verified_training_eligible(row: dict | None) -> bool:
    if not isinstance(row, dict):
        return False
    taught = row.get("skills_taught") or {}
    objectives = row.get("training_objective_mapping") or {}
    return bool(
        row.get("lineage_mapping_status") == "verified"
        and row.get("source_split") == "training"
        and taught.get("verified_skill_ids")
        and objectives.get("verified_objective_ids")
    )


def qwen_lineage_annotation(row: dict | None) -> dict:
    """Return only separated verified/candidate claims; never flatten them."""
    if not isinstance(row, dict):
        return {
            "mapping_status": "unmapped",
            "training_eligible": False,
            "candidate_claims_do_not_count": True,
        }
    taught = row.get("skills_taught") or {}
    exercised = row.get("skills_exercised") or {}
    tested = row.get("skills_tested") or {}
    objectives = row.get("training_objective_mapping") or {}
    return {
        "ontology_ref": row.get("ontology_ref"),
        "source_task_id": row.get("source_task_id"),
        "source_split": row.get("source_split"),
        "relationship": row.get("relationship"),
        "mapping_status": row.get("lineage_mapping_status"),
        "training_eligible": lineage_is_verified_training_eligible(row),
        "verified_taught_skill_ids": list(taught.get("verified_skill_ids") or []),
        "candidate_taught_skill_ids": list(taught.get("candidate_skill_ids") or []),
        "verified_exercised_primitive_ids": list(
            exercised.get("verified_primitive_ids") or []
        ),
        "candidate_exercised_primitive_ids": list(
            exercised.get("candidate_primitive_ids") or []
        ),
        "verified_tested_skill_ids": list(tested.get("verified_skill_ids") or []),
        "candidate_tested_skill_ids": list(tested.get("candidate_skill_ids") or []),
        "verified_training_objective_ids": list(
            objectives.get("verified_objective_ids") or []
        ),
        "candidate_training_objective_ids": list(
            objectives.get("candidate_objective_ids") or []
        ),
        "claim_rejection_reasons": list(row.get("claim_rejection_reasons") or []),
        "candidate_claims_do_not_count": True,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--generator-root", type=Path, default=REPO_ROOT,
                    help="Tree containing puzzle_generators/per_puzzle/<task>/generator.py")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--episodes-per-task", type=int, default=8)
    # Random per-episode sizes. Default 3-6 demos : 1-3 queries (the 4090 curriculum).
    # For the RTX 6000 10:4 run, pass --n-demos-min 10 --n-demos-max 10 --n-query-min 4 --n-query-max 4.
    ap.add_argument("--n-demos-min", type=int, default=3)
    ap.add_argument("--n-demos-max", type=int, default=6)
    ap.add_argument("--n-query-min", type=int, default=1)
    ap.add_argument("--n-query-max", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--shard-rows", type=int, default=2000)
    ap.add_argument("--task-id", action="append", help="restrict to this task id (repeatable)")
    ap.add_argument("--task-limit", type=int, default=None)
    ap.add_argument("--shuffle-tasks", action="store_true",
                    help="Shuffle task order (by --seed) before --task-limit, so an hourly cron "
                         "with a fresh seed hits a DIFFERENT random subset each run.")
    ap.add_argument("--difficulty-weights", default=None,
                    help="JSON {task_id: weight}. When set, the --task-limit subset is sampled "
                         "WEIGHTED by difficulty (harder generators picked more often). Unseen "
                         "task_ids get the median weight so new generators aren't starved.")
    ap.add_argument(
        "--skill-matrix", type=Path, default=DEFAULT_GENERATOR_SKILL_MATRIX,
        help="Versioned generator-to-skill JSONL emitted by audit_official_generator_lineage.py.",
    )
    ap.add_argument(
        "--lineage-policy", choices=LINEAGE_POLICIES, default="annotate",
        help=(
            "annotate every row with separated verified/candidate claims; "
            "verified-skill-only excludes unmapped, candidate, evaluation, and "
            "skill-unresolved generators; off preserves legacy output"
        ),
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    task_ids = args.task_id or discover_task_ids(args.generator_root)
    lineage_policy = getattr(args, "lineage_policy", "annotate")
    skill_matrix_path = Path(
        getattr(args, "skill_matrix", DEFAULT_GENERATOR_SKILL_MATRIX)
    )
    skill_matrix: dict[str, dict] = {}
    if lineage_policy != "off":
        if skill_matrix_path.is_file():
            skill_matrix = load_generator_skill_matrix(skill_matrix_path)
        elif lineage_policy == "verified-skill-only":
            print(f"missing required skill matrix: {skill_matrix_path}", file=sys.stderr)
            return 1
        else:
            print(
                f"warning: skill matrix missing; rows will be explicitly unmapped: {skill_matrix_path}",
                file=sys.stderr,
            )
    skipped_lineage = 0
    if lineage_policy == "verified-skill-only":
        selected = []
        for task_id in task_ids:
            if lineage_is_verified_training_eligible(skill_matrix.get(task_id)):
                selected.append(task_id)
            else:
                skipped_lineage += 1
        task_ids = selected
    weights = load_weights(args.difficulty_weights)
    if weights:
        task_ids = weighted_order(task_ids, weights, args.seed)    # harder first (in expectation)
    elif args.shuffle_tasks:
        random.Random(args.seed).shuffle(task_ids)
    if args.task_limit:
        task_ids = task_ids[: args.task_limit]
    if not task_ids:
        print("no task ids found", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    written, failed = 0, 0
    rows = []  # collect ALL episodes, then shuffle before sharding so each shard —
               # and therefore each training batch — is a diverse mix of generators
               # (NOT 40 consecutive episodes of one task, which causes the model to
               # overfit one task per step → catastrophic forgetting).

    for ti, task_id in enumerate(task_ids):
        try:
            bundle = runner._load_bundle(task_id)
            bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
        except Exception as e:
            failed += 1
            print(f"skip {task_id}: load failed {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            continue
        try:
            for ep in range(args.episodes_per_task):
                n_demos = rng.randint(args.n_demos_min, args.n_demos_max)
                n_queries = rng.randint(args.n_query_min, args.n_query_max)
                try:
                    inst = runner.run_one(
                        task_id, seed=args.seed + ep, sample_index=0,
                        n_train=n_demos, n_test=n_queries,
                        bundle=bundle, bridge=bridge, fn_name=fn_name,
                    )
                    demos = inst["train"]
                    queries = list(inst["test"])
                    text = fmt_episode(demos, queries)
                    messages = episode_messages(demos, queries)
                except Exception as e:
                    failed += 1
                    print(f"skip {task_id} ep{ep}: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
                    continue
                output_row = {
                    "text": text, "messages": messages, "task_id": task_id,
                    "demo_count": len(demos), "query_count": len(queries),
                    # Provenance is cheap and makes stale-shard/sample audits possible.
                    # Without this, a live pool can still contain rows generated by an
                    # older generator version, but the row itself gives no way to tell.
                    "source_stream": "per_puzzle",
                    "source_seed": args.seed,
                    "instance_seed": args.seed + ep,
                    "episode_index": ep,
                    "generator_version": str(getattr(bundle.generator_module, "VERSION", "")),
                    "rule_source": bundle.rule_file,
                }
                if lineage_policy != "off":
                    output_row["official_lineage"] = qwen_lineage_annotation(
                        skill_matrix.get(task_id)
                    )
                rows.append(output_row)
                written += 1
        finally:
            # one Racket subprocess per task — close it explicitly instead of
            # relying on __del__ refcounting, which is fragile over a 1000-task run.
            bridge.shutdown()
        if (ti + 1) % 50 == 0:
            print(f"... {ti+1}/{len(task_ids)} tasks, {written} rows, {failed} fails", flush=True)

    # Full mix across all generators in this run, then shard.
    rng.shuffle(rows)
    shard_idx = 0
    for i in range(0, len(rows), args.shard_rows):
        path = args.output_dir / f"qwen_sft-{shard_idx:05d}.jsonl"
        # atomic publish (temp + rename) so the live trainer never globs a half-written shard.
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w") as handle:
            for row in rows[i:i + args.shard_rows]:
                handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        tmp.replace(path)
        shard_idx += 1
    print(
        f"done: {written} rows across {shard_idx} shards (shuffled), "
        f"{failed} fails, {skipped_lineage} lineage-filtered -> {args.output_dir}"
    )
    # Signal failure if EVERY task failed: a silent "0 rows, exit 0" makes a broken
    # cron cycle look healthy. The cron's publish-guard also refuses an empty dir.
    return 0 if written > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

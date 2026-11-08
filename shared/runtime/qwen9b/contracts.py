"""Single source of truth for Qwen9B data, config, and checkpoint contracts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

RAW_SCHEMA = "qwen9b_raw_instance_v1"
DATASET_SCHEMA = "qwen9b_dataset_manifest_v2"
CHECKPOINT_SCHEMA = "qwen9b_checkpoint_v1"
OBJECTIVES = ("predict", "synth", "exec", "invert", "facts", "describe", "shape",
              "repair", "refine", "cell_probe", "verify_repair")
TRAINING_ROUTES = ("standard", "reverse_genetics")
REVERSE_GENETICS_SCHEMA_V1 = "reverse_genetics_episode_v1"
REVERSE_GENETICS_SCHEMA = "reverse_genetics_episode_v2"
REVERSE_GENETICS_SCHEMAS = {
    REVERSE_GENETICS_SCHEMA_V1, REVERSE_GENETICS_SCHEMA,
}
REVERSE_GENETICS_OBJECTIVES = {
    "exec", "synth", "trace", "delta_exec", "delta_prog",
    "which_program", "repair",
}

# TOKEN SHARE IS NOT ROW SHARE — and for a short-target objective the gap is
# enormous. The mix sampler (train.py MultimodeStream._objective) balances
# supervised TARGET TOKENS, so an objective's ROW rate is share/tokens_per_row:
# halve the target length and you double the number of presentations bought by
# the same share. The trainer explicitly computes one token-mean loss per row
# and then averages rows inside a packed microbatch, so every row contributes
# equal gradient weight regardless of target length — realized GRADIENT share
# tracks ROW share, not the token share the YAML names.
#
# Measured with the active Qwen3.5 tokenizer over 400 random rows of the live
# 18,602-row build (scripts: see MEASUREMENT below), supervised target tokens
# per row:
MEASURED_TARGET_TOKENS = {
    "predict": 141.5,
    "synth": 345.4,
    "exec": 141.5,
    "invert": 186.4,
    "facts": 95.9,
    "describe": 34.9,   # one authored rule description
    "shape": 6.1,       # "H W" + newline + EOS
    # Exactly one direct LM-head classification at each arbitrary `?` anchor;
    # no answer tokens are serialized and outputs smaller than nine cells use
    # OOB queries to keep the normal live-path count at nine.
    "cell_probe": 9.0,
    # 90% wrong: one decision token + nine independent repairs. 10% correct:
    # one decision token and no second turn. Expected targets = 9.1.
    "verify_repair": 9.1,
}
# `refine` supervises its target grid once per descent step, so its per-row
# target is steps x predict. Any objective absent from the table falls back to
# predict's length; every SHORT-target objective must be measured and listed
# here, because that is the case the fallback would get wrong.
_REFINE_STEPS_DEFAULT = 3

# Row-share ceilings keep short-target lessons from buying a silent 10-50x
# presentation multiplier. Dense objectives are intentionally allowed to mix
# freely; the local compute-aware curriculum no longer requires `predict` to
# dominate either tokens or rows.
ROW_SHARE_CAPS = {
    "describe": 0.05,
    "shape": 0.03,
    "cell_probe": 0.10,
    "verify_repair": 0.10,
}

REQUIRED_ROW_FIELDS = (
    "schema_version", "task_id", "content_hash", "source", "split_group",
    "generator_version", "seed", "sample_index", "program", "program_hash",
    "facts", "train", "test",
)


class ContractError(ValueError):
    """A persisted artifact violates an explicit training contract."""


def sha256_file(path: Path, chunk_size: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_grid(grid: Any, where: str) -> None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ContractError(f"{where}: grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ContractError(f"{where}: grid shape {height}x{width} is outside 1..30")
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            raise ContractError(f"{where}: row {r} is ragged")
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ContractError(f"{where}: cell ({r},{c})={value!r} is not an ARC color")


def validate_instance_row(row: dict[str, Any], where: str = "row") -> None:
    missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
    if missing:
        raise ContractError(f"{where}: missing fields {missing}")
    if row["schema_version"] != RAW_SCHEMA:
        raise ContractError(f"{where}: schema {row['schema_version']!r} != {RAW_SCHEMA!r}")
    for field in ("task_id", "content_hash", "source", "split_group", "generator_version"):
        if row[field] in (None, "", "?"):
            raise ContractError(f"{where}: required provenance {field} is empty")
    program = row["program"]
    if not isinstance(program, str) or not program.strip():
        raise ContractError(f"{where}: program is empty")
    if hashlib.sha256(program.encode()).hexdigest() != row["program_hash"]:
        raise ContractError(f"{where}: program_hash does not match program")
    authority_hash = row.get("program_authority_hash")
    if authority_hash is not None and (
        not isinstance(authority_hash, str)
        or len(authority_hash) != 64
        or any(char not in "0123456789abcdef" for char in authority_hash)
    ):
        raise ContractError(f"{where}: program_authority_hash is not lowercase sha256")
    presentation_variant = row.get("program_presentation_variant")
    if presentation_variant is not None and (
        not isinstance(presentation_variant, str) or not presentation_variant
    ):
        raise ContractError(f"{where}: program_presentation_variant is empty")
    comments_added = row.get("program_comments_added")
    if comments_added is not None and (
        type(comments_added) is not int or comments_added < 0
    ):
        raise ContractError(f"{where}: program_comments_added is not a nonnegative int")
    if not isinstance(row["facts"], (list, str)) or not row["facts"]:
        raise ContractError(f"{where}: facts are empty")
    if "summary" in row and row["summary"] is not None:
        # Optional autoencoder-summary channel: a K x dim bank of finite
        # numbers, demos+query-input derived only (leak rule is enforced at
        # export time; here we check shape/finiteness).
        bank = row["summary"]
        if not isinstance(bank, list) or not bank:
            raise ContractError(f"{where}: summary must be a nonempty K x dim list")
        width = None
        for slot in bank:
            if not isinstance(slot, list) or not slot:
                raise ContractError(f"{where}: summary slots must be nonempty lists")
            if width is None:
                width = len(slot)
            elif len(slot) != width:
                raise ContractError(f"{where}: summary slots have inconsistent width")
            for value in slot:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ContractError(f"{where}: summary value {value!r} is not a number")
                if value != value or value in (float("inf"), float("-inf")):
                    raise ContractError(f"{where}: summary value {value!r} is not finite")
    for split in ("train", "test"):
        pairs = row[split]
        if not isinstance(pairs, list) or not pairs:
            raise ContractError(f"{where}: {split} must contain at least one pair")
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or set(("input", "output")) - set(pair):
                raise ContractError(f"{where}: {split}[{index}] lacks input/output")
            validate_grid(pair["input"], f"{where}.{split}[{index}].input")
            validate_grid(pair["output"], f"{where}.{split}[{index}].output")

    training_route = row.get("training_route", "standard")
    if training_route not in TRAINING_ROUTES:
        raise ContractError(f"{where}: unknown training_route {training_route!r}")
    forced_objective = row.get("training_objective")
    if training_route == "standard":
        if forced_objective is not None:
            raise ContractError(
                f"{where}: standard rows may not force training_objective"
            )
        return

    # Reverse genetics is a deliberately narrow route.  These checks make a
    # generated episode self-auditing at every shard/read boundary; the
    # durable ledger enforces uniqueness across episodes.
    if row["source"] != "reverse_genetics":
        raise ContractError(f"{where}: reverse_genetics source does not match route")
    if len(row["train"]) != 5 or len(row["test"]) != 1:
        raise ContractError(
            f"{where}: reverse_genetics requires exactly five visible pairs "
            "and one hidden pair"
        )
    metadata = row.get("reverse_genetics")
    if not isinstance(metadata, dict):
        raise ContractError(f"{where}: reverse_genetics metadata is missing")
    reverse_schema = metadata.get("schema_version")
    if reverse_schema not in REVERSE_GENETICS_SCHEMAS:
        raise ContractError(
            f"{where}: reverse_genetics schema "
            f"{reverse_schema!r} is not one of {sorted(REVERSE_GENETICS_SCHEMAS)}"
        )
    program_surface = metadata.get("program_surface", "rg")
    if program_surface not in {"rg", "prelude"}:
        raise ContractError(
            f"{where}: reverse_genetics program_surface must be rg or prelude"
        )
    allowed_objectives = (
        {"exec", "synth"}
        if reverse_schema == REVERSE_GENETICS_SCHEMA_V1
        else REVERSE_GENETICS_OBJECTIVES
    )
    if forced_objective not in allowed_objectives:
        raise ContractError(
            f"{where}: reverse_genetics {reverse_schema} objective "
            f"{forced_objective!r} not in {sorted(allowed_objectives)}"
        )
    ast = metadata.get("program_ast")
    if not isinstance(ast, list) or not ast:
        raise ContractError(f"{where}: reverse_genetics program_ast is empty")
    for index, gene in enumerate(ast):
        if (not isinstance(gene, dict) or not isinstance(gene.get("name"), str)
                or not gene["name"] or not isinstance(gene.get("args"), list)
                or any(type(arg) is not int for arg in gene["args"])):
            raise ContractError(
                f"{where}: reverse_genetics program_ast[{index}] is malformed"
            )
    if metadata.get("program_ast_hash") != stable_hash(ast):
        raise ContractError(
            f"{where}: reverse_genetics program_ast_hash does not match AST"
        )
    structural_hash = stable_hash([gene["name"] for gene in ast])
    if metadata.get("program_structural_hash") != structural_hash:
        raise ContractError(
            f"{where}: reverse_genetics program_structural_hash does not match AST"
        )
    if metadata.get("visible_count") != 5 or metadata.get("hidden_count") != 1:
        raise ContractError(f"{where}: reverse_genetics pair counts are inconsistent")

    expected_input_hashes = [
        stable_hash(pair["input"])
        for pair in (*row["train"], *row["test"])
    ]
    input_hashes = metadata.get("input_hashes")
    if input_hashes != expected_input_hashes:
        raise ContractError(f"{where}: reverse_genetics input_hashes do not match grids")
    if len(set(input_hashes)) != 6:
        raise ContractError(f"{where}: reverse_genetics repeats an input grid")
    expected_output_hashes = [
        stable_hash(pair["output"])
        for pair in (*row["train"], *row["test"])
    ]
    if metadata.get("output_hashes") != expected_output_hashes:
        raise ContractError(f"{where}: reverse_genetics output_hashes do not match grids")
    if metadata.get("visible_set_hash") != stable_hash([
        [input_hash, output_hash]
        for input_hash, output_hash in zip(
            expected_input_hashes[:5], expected_output_hashes[:5]
        )
    ]):
        raise ContractError(f"{where}: reverse_genetics visible_set_hash does not match")
    if metadata.get("hidden_probe_hash") != stable_hash([
        expected_input_hashes[5], expected_output_hashes[5]
    ]):
        raise ContractError(f"{where}: reverse_genetics hidden_probe_hash does not match")
    ancestry = metadata.get("ancestry")
    if (not isinstance(ancestry, dict)
            or ancestry.get("origin") not in {"random_ast", "mutation", "crossover",
                                               "model_promotion"}
            or not isinstance(ancestry.get("parents"), list)):
        raise ContractError(f"{where}: reverse_genetics ancestry is malformed")
    activation = metadata.get("node_activation")
    if (not isinstance(activation, list) or len(activation) != len(ast)
            or any(type(active) is not bool for active in activation)
            or not all(activation)):
        raise ContractError(
            f"{where}: every reverse_genetics program node must activate visibly"
        )

    auxiliary = metadata.get("auxiliary_inputs", [])
    if reverse_schema == REVERSE_GENETICS_SCHEMA_V1:
        if auxiliary:
            raise ContractError(f"{where}: v1 reverse_genetics cannot carry auxiliaries")
        auxiliary_hashes: list[str] = []
    else:
        if not isinstance(auxiliary, list):
            raise ContractError(f"{where}: auxiliary_inputs must be a list")
        auxiliary_hashes = []
        for index, item in enumerate(auxiliary):
            if (not isinstance(item, dict) or not isinstance(item.get("role"), str)
                    or not item["role"] or "input" not in item):
                raise ContractError(
                    f"{where}: auxiliary_inputs[{index}] is malformed"
                )
            validate_grid(item["input"], f"{where}.auxiliary_inputs[{index}].input")
            fingerprint = stable_hash(item["input"])
            if item.get("input_hash") != fingerprint:
                raise ContractError(
                    f"{where}: auxiliary_inputs[{index}] hash does not match"
                )
            auxiliary_hashes.append(fingerprint)
        if len(set([*input_hashes, *auxiliary_hashes])) != 6 + len(auxiliary_hashes):
            raise ContractError(f"{where}: reverse_genetics repeats an auxiliary input")

    episode_payload = {
        "program": ast,
        "visible": expected_input_hashes[:5],
        "hidden": expected_input_hashes[5],
        "objective": forced_objective,
    }
    if reverse_schema != REVERSE_GENETICS_SCHEMA_V1:
        episode_payload["auxiliary"] = auxiliary_hashes
    expected_episode_hash = stable_hash(episode_payload)
    if metadata.get("episode_hash") != expected_episode_hash:
        raise ContractError(f"{where}: reverse_genetics episode_hash does not match")
    if row["task_id"] != expected_episode_hash[:12]:
        raise ContractError(f"{where}: reverse_genetics task_id does not match episode")

    mutant_count = metadata.get("mutant_count")
    killed = metadata.get("mutants_killed_visible")
    survivors = metadata.get("surviving_mutants")
    if (type(mutant_count) is not int or mutant_count < len(ast)
            or type(killed) is not int or not 0 <= killed <= mutant_count
            or not isinstance(survivors, list)
            or any(not isinstance(label, str) or not label for label in survivors)
            or any(label.startswith("delete:") for label in survivors)
            or killed + len(survivors) != mutant_count):
        raise ContractError(f"{where}: reverse_genetics mutant audit is inconsistent")
    if reverse_schema != REVERSE_GENETICS_SCHEMA_V1:
        killable = metadata.get("killable_mutants")
        aliases = metadata.get("empirical_aliases")
        if (type(killable) is not int or killable != killed
                or not isinstance(aliases, list) or aliases != survivors):
            raise ContractError(
                f"{where}: v2 killable/alias mutant accounting is inconsistent"
            )
        lesson = metadata.get("lesson")
        if (not isinstance(lesson, dict)
                or lesson.get("type") != forced_objective):
            raise ContractError(
                f"{where}: v2 lesson type does not match forced objective"
            )
        if forced_objective == "delta_exec" and len(auxiliary_hashes) != 1:
            raise ContractError(
                f"{where}: delta_exec requires exactly one novel paired input"
            )
        if forced_objective == "delta_exec":
            visible = lesson.get("factor_label_visible", True)
            variant = lesson.get(
                "presentation_variant",
                "factor_labeled" if visible else "factor_blind",
            )
            if type(visible) is not bool or variant not in {
                    "factor_labeled", "factor_blind"}:
                raise ContractError(
                    f"{where}: delta_exec presentation variant is malformed"
                )
            if (variant == "factor_labeled") != visible:
                raise ContractError(
                    f"{where}: delta_exec label visibility disagrees with variant"
                )
        if forced_objective != "delta_exec" and auxiliary_hashes:
            raise ContractError(
                f"{where}: only delta_exec may carry an auxiliary input"
            )
    generation = metadata.get("generation")
    required_generation = {
        "program_candidates", "scene_proposals", "valid_probes",
        "duplicate_probes", "execution_rejections", "degenerate_rejections",
        "selection_rejections", "racket_rejections", "ledger_rejections",
    }
    if reverse_schema != REVERSE_GENETICS_SCHEMA_V1:
        required_generation |= {
            "composition_rejections", "unidentifiable_rejections",
        }
    if (not isinstance(generation, dict)
            or required_generation - set(generation)
            or any(type(generation[key]) is not int or generation[key] < 0
                   for key in required_generation)
            or generation["program_candidates"] < 1
            or generation["scene_proposals"] < generation["valid_probes"]
            or generation["valid_probes"] < 6):
        raise ContractError(f"{where}: reverse_genetics generation audit is inconsistent")


def implied_row_shares(mix: dict[str, Any], refine_steps: int = _REFINE_STEPS_DEFAULT,
                       tokens: dict[str, float] | None = None) -> dict[str, float]:
    """Convert a supervised-target-TOKEN mix into the ROW share it really buys.

    The deficit sampler emits an objective until its emitted tokens catch up to
    `share * total`, so in steady state row_rate(o) = share(o)/tokens_per_row(o)
    and the realized presentation share is that rate normalized. With
    equal-example loss reduction makes this the realized gradient share at any
    supported microbatch size, since each row's loss is its own token mean.
    """
    lengths = dict(MEASURED_TARGET_TOKENS if tokens is None else tokens)
    lengths.setdefault("refine", max(1, int(refine_steps)) * lengths["predict"])
    rates = {
        name: float(share) / lengths.get(name, lengths["predict"])
        for name, share in mix.items()
        if float(share) > 0
    }
    total = sum(rates.values())
    if total <= 0:
        return {}
    return {name: rate / total for name, rate in rates.items()}


def validate_config(config: dict[str, Any]) -> None:
    required = ("model", "lora", "injector", "data", "optimizer", "full_finetune", "batching", "run")
    missing = [key for key in required if key not in config]
    if missing:
        raise ContractError(f"config missing sections {missing}")
    mix = config["data"].get("objective_mix", {})
    unknown = set(mix) - set(OBJECTIVES)
    if unknown:
        raise ContractError(f"unknown objectives in mix: {sorted(unknown)}")
    if abs(sum(float(value) for value in mix.values()) - 1.0) > 1e-9:
        raise ContractError(f"objective mix must sum to 1.0, got {sum(mix.values())}")
    cell_probe_cfg = config["data"].get("cell_probe", {})
    focus_cfg = cell_probe_cfg.get("focus_batch") or {}
    focus_enabled = bool(focus_cfg.get("enabled", False))
    predict_share = float(mix.get("predict", 0))
    if predict_share <= 0 and not focus_enabled:
        raise ContractError("objective mix must retain a positive predict lane")
    if float(mix.get("repair", 0)):
        raise ContractError("v1 contract forbids repair rows")
    cell_probe_share = float(mix.get("cell_probe", 0))
    verify_repair_share = float(mix.get("verify_repair", 0))
    if cell_probe_share or verify_repair_share:
        if not cell_probe_cfg.get("enabled"):
            raise ContractError(
                "cell_probe mix requires data.cell_probe.enabled: true"
            )
        if not str(cell_probe_cfg.get("queue_path") or "").strip():
            raise ContractError("enabled cell_probe requires a durable queue_path")
        threshold = float(cell_probe_cfg.get("nll_threshold", 0.7))
        if not (0.0 <= threshold < 10.0 if focus_enabled else 0.0 < threshold < 10.0):
            raise ContractError(
                f"data.cell_probe.nll_threshold {threshold} outside the allowed range"
            )
        oob_cells = int(cell_probe_cfg.get("oob_cells", 2))
        if not 0 <= oob_cells <= 9:
            raise ContractError(f"data.cell_probe.oob_cells {oob_cells} outside 0..9")
        max_pending = int(cell_probe_cfg.get("max_pending", 256))
        if not 9 <= max_pending <= 10_000:
            raise ContractError(
                f"data.cell_probe.max_pending {max_pending} outside 9..10000"
            )
    if focus_enabled:
        if mix != {"cell_probe": 1.0}:
            raise ContractError(
                "cell_probe.focus_batch requires objective_mix: {cell_probe: 1.0}"
            )
        if int(cell_probe_cfg.get("oob_cells", -1)) != 0:
            raise ContractError(
                "cell_probe.focus_batch reserves no OOB share; oob_cells must "
                "be 0 (tiny outputs may still be padded with nearby OOB cells)"
            )
        target_pending = int(focus_cfg.get("target_pending", 0))
        steps_per_cycle = int(focus_cfg.get("steps_per_cycle", 0))
        if not 128 <= target_pending <= max_pending:
            raise ContractError(
                "cell_probe.focus_batch.target_pending must be in 128..max_pending"
            )
        if not 1 <= steps_per_cycle <= 100:
            raise ContractError(
                "cell_probe.focus_batch.steps_per_cycle must be in 1..100"
            )
        selection_strategy = str(
            focus_cfg.get("selection_strategy", "hardest")
        )
        if selection_strategy not in {"hardest", "perplexity"}:
            raise ContractError(
                "cell_probe.focus_batch.selection_strategy must be "
                "hardest or perplexity"
            )
    if verify_repair_share:
        verify_cfg = config["data"].get("verify_repair", {})
        if not verify_cfg.get("enabled"):
            raise ContractError(
                "verify_repair mix requires data.verify_repair.enabled: true"
            )
        if float(verify_cfg.get("correct_fraction", -1)) != 0.1:
            raise ContractError("verify_repair.correct_fraction must be exactly 0.1")
        if int(verify_cfg.get("max_wrong_cells", -1)) != 3:
            raise ContractError("verify_repair.max_wrong_cells must be exactly 3")
    real_rule_cfg = config["data"].get("real_rule_adversary", {})
    if real_rule_cfg.get("enabled"):
        for key in ("lessons_path", "queue_path"):
            if not str(real_rule_cfg.get(key) or "").strip():
                raise ContractError(
                    f"enabled real_rule_adversary requires "
                    f"data.real_rule_adversary.{key}"
                )
        probability = float(
            real_rule_cfg.get("standard_row_probability", 0.0)
        )
        if not 0.0 < probability <= 0.05:
            raise ContractError(
                "real_rule_adversary.standard_row_probability must be in (0,0.05]"
            )
    # SHORT-TARGET GUARD. These objectives buy far more ROWS per unit of token
    # share than a full-grid objective. Gate on the PRESENTATION share the
    # token-balanced mix actually implies, and print the number that matters.
    row_shares = implied_row_shares(
        mix, int(config["data"].get("refine", {}).get("steps", _REFINE_STEPS_DEFAULT)))
    for name, cap in ROW_SHARE_CAPS.items():
        realized = row_shares.get(name, 0.0)
        if focus_enabled and name == "cell_probe":
            # Explicit temporary curriculum: every optimizer presentation is
            # a mined nine-cell derivative. The ordinary-route guard remains
            # unchanged when focus mode is off.
            continue
        if realized > cap:
            raise ContractError(
                f"objective_mix.{name}={mix.get(name)} is a TOKEN share; with "
                f"~{MEASURED_TARGET_TOKENS[name]:.0f} target tokens per row it "
                f"implies {realized:.1%} of all PRESENTATIONS (cap {cap:.0%}). "
                f"Token share is not row share — see contracts.MEASURED_TARGET_TOKENS. "
                f"For ~{cap / 2:.1%} of rows use about "
                f"{float(mix.get(name, 0)) * (cap / 2) / max(realized, 1e-12):.4f}."
            )
    refine_share = float(mix.get("refine", 0))
    if refine_share:
        refine_cfg = config["data"].get("refine", {})
        if not refine_cfg.get("enabled"):
            raise ContractError(
                "refine mix requires data.refine.enabled: true "
                "(deep-supervision protocol, EXPERIMENT_PLAN E2c)"
            )
        if refine_share > 0.15:
            raise ContractError(
                f"refine share {refine_share} exceeds the 0.15 cap — the cap is "
                "on supervised TARGET-TOKEN share (the mix sampler enforces "
                "token share, so gradient mass, not row count, is bounded); "
                "predict must stay dominant"
            )
        steps = int(refine_cfg.get("steps", 3))
        if not 1 <= steps <= 4:
            raise ContractError(f"data.refine.steps {steps} outside 1..4")
        drill_fraction = float(refine_cfg.get("drill_fraction", 0.5))
        if not 0.0 <= drill_fraction <= 1.0:
            raise ContractError(f"data.refine.drill_fraction {drill_fraction} outside 0..1")
    if int(config["run"].get("save_every_minutes", 0)) <= 0:
        raise ContractError("run.save_every_minutes must be positive")
    if int(config["run"].get("keep_checkpoints", 0)) < 1:
        raise ContractError("run.keep_checkpoints must be at least one")
    max_checkpoint_gb = config["run"].get("max_checkpoint_storage_gb")
    if max_checkpoint_gb is not None and float(max_checkpoint_gb) <= 0:
        raise ContractError("run.max_checkpoint_storage_gb must be positive")


def build_shard_record(path: Path, rows: int) -> dict[str, Any]:
    return {"name": path.name, "rows": rows, "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def validate_dataset(data_dir: Path, *, deep: bool = False) -> dict[str, Any]:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise ContractError(f"missing dataset manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != DATASET_SCHEMA:
        raise ContractError(f"dataset schema {manifest.get('schema_version')!r} != {DATASET_SCHEMA!r}")
    shards = manifest.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ContractError("manifest.shards must be a nonempty record list")
    total_rows = 0
    for record in shards:
        if not isinstance(record, dict) or set(("name", "rows", "bytes", "sha256")) - set(record):
            raise ContractError(f"malformed shard record: {record!r}")
        path = data_dir / record["name"]
        if not path.exists():
            raise ContractError(f"manifest shard missing: {path}")
        if path.stat().st_size != int(record["bytes"]):
            raise ContractError(f"shard byte mismatch: {path}")
        if sha256_file(path) != record["sha256"]:
            raise ContractError(f"shard checksum mismatch: {path}")
        line_count = 0
        with path.open() as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                line_count += 1
                if deep or line_number == 1:
                    validate_instance_row(json.loads(line), f"{path.name}:{line_number}")
        if line_count != int(record["rows"]):
            raise ContractError(f"shard row mismatch: {path} manifest={record['rows']} actual={line_count}")
        total_rows += line_count
    if total_rows != int(manifest.get("produced", -1)):
        raise ContractError(f"manifest produced={manifest.get('produced')} but shards contain {total_rows}")
    extras = {path.name for path in data_dir.glob("instances-*.jsonl")} - {r["name"] for r in shards}
    if extras:
        raise ContractError(f"unmanifested instance shards present: {sorted(extras)}")
    return manifest


def checkpoint_is_complete(path: Path) -> bool:
    marker = path / "COMPLETE.json"
    if not marker.exists() or not (path / "training_state.pt").exists() or not (path / "injector.pt").exists():
        return False
    try:
        record = json.loads(marker.read_text())
    except Exception:
        return False
    return record.get("schema_version") == CHECKPOINT_SCHEMA and record.get("complete") is True

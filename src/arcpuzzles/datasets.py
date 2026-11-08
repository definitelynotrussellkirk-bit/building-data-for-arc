"""Reproducible mixed sampling and explicit public/private dataset artifacts."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import shutil
import sys
import tempfile
from typing import Any

from .catalog import Catalog, jsonl, local_path, sha256
from .runtime import GenerationFailure, demonstration_policy, generate_in_runtime, prepare_runtime, run_process

STYLES = ("challenges", "episodes", "grids", "code", "dsl", "hindsight", "synthpipe", "native")
MODES = ("predict", "synth", "exec", "invert", "repair", "refine", "pred_facts")
FILTERS = {"approved", "source", "skill", "primitive", "difficulty", "kind",
           "train_safety", "search", "has_generator", "family", "split"}


def _dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def _append(path: Path, value: Any) -> None:
    with path.open("a") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def _identity(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def _draw_sequence(pool, sampling, seed):
    """One RNG order for planning and execution, including rejected draws."""
    rng = random.Random(seed)
    weights = [r['mix_weight'] if sampling == 'weighted' else 1 for r in pool]
    while True:
        row = rng.choices(pool, weights=weights, k=1)[0] if pool else None
        yield row, rng.getrandbits(63)


def _reachable_tasks(pool, sampling, seed, max_attempts):
    draws = _draw_sequence(pool, sampling, seed)
    found = set()
    for _ in range(max_attempts):
        row, _ = next(draws)
        found.add(row['id'])
        if len(found) == len(pool):
            break
    return found


def _verify_preflight(root, pool, episodes, options):
    scope = options.get('parametric_preflight')
    if scope is None:
        return  # Earlier full-pool artifacts have no bounded-preflight claim.
    expected_keys = {'schema', 'mode', 'explicit_tasks', 'checked_tasks', 'runtime_tasks'}
    if (type(scope) is not dict or set(scope) != expected_keys
            or scope['schema'] != 'arcpuzzles-parametric-preflight-v1'
            or scope['mode'] != 'bounded_draws_and_explicit_ids'):
        raise ValueError('Invalid parametric preflight scope')
    pool_ids = {row['id'] for row in pool}
    if len(pool_ids) != len(pool):
        raise ValueError('Duplicate candidate in parametric preflight pool')
    for key in ('explicit_tasks', 'checked_tasks', 'runtime_tasks'):
        values = scope[key]
        if (type(values) is not list or any(type(v) is not str for v in values)
                or values != sorted(set(values)) or not set(values) <= pool_ids):
            raise ValueError('Invalid task inventory in parametric preflight scope')
    reachable = _reachable_tasks(pool, options['sampling'], options['seed'], options['max_attempts'])
    checked = reachable | set(scope['explicit_tasks'])
    if set(scope['checked_tasks']) != checked or scope['runtime_tasks'] != scope['checked_tasks']:
        raise ValueError('Parametric preflight does not cover its bounded draws and explicit IDs')
    runtime = json.loads((root / 'runtime.private.json').read_text())
    if runtime.get('task_ids') != scope['runtime_tasks']:
        raise ValueError('Staged runtime differs from the parametric preflight scope')
    schedule = _draw_sequence(pool, options['sampling'], options['seed'])
    draws = [row for row in jsonl(root / 'draws.private.jsonl') if 'diagnostics' not in row]
    if not 1 <= len(draws) <= options['max_attempts']:
        raise ValueError('Parametric draw count differs from its bounded preflight')
    for attempt, draw in enumerate(draws, 1):
        row, seed = next(schedule)
        if (type(draw.get('attempt')) is not int or draw['attempt'] != attempt
                or type(draw.get('seed')) is not int or draw['seed'] != seed
                or draw.get('task_id') != row['id'] or row['id'] not in checked):
            raise ValueError('Parametric draw differs from its preflight schedule')
    actual = {(row['task_id'], row['seed']) for row in draws}
    if any((row['task_id'], row['seed']) not in actual for row in episodes):
        raise ValueError('Parametric episode has no corresponding preflight draw')


def public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """An opaque ID, visible demonstrations and query inputs, with no authority metadata."""
    if 'parametric' in episode:
        from .inline_parametric import public_identity
        identity = public_identity(episode)
    else:
        identity = _identity(episode)
    return {"episode_id": identity,
            "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def _lineage_row(episode: dict[str, Any], episode_id: str,
                 lineage: dict[str, Any]) -> dict[str, Any]:
    """Bind a checked official-family result to one private generated episode."""
    evidence = lineage.get("evidence")
    verified = lineage.get("verified") is True
    row = {"schema": "arcpuzzles-official-lineage-v1", "episode_id": episode_id,
           "task_id": episode["task_id"],
           "generator_sha256": episode["provenance"]["generator_sha256"],
           "demonstration_policy": episode["provenance"].get("demonstration_policy"),
           "lesson_check": episode["provenance"].get("lesson_check"),
           "verified": verified,
           "family_id": lineage.get("family_id") if verified else None,
           "source_split": lineage.get("source_split") if verified else None,
           "source_task_id": lineage.get("source_task_id") if verified else None,
           "reasons": lineage.get("reasons", []), "evidence": evidence,
           "evidence_sha256": _identity(evidence) if evidence is not None else None}
    _verify_lineage_row(row, episode_id, episode["task_id"], episode["provenance"])
    return row


def _verify_lineage_row(row: dict[str, Any], episode_id: str, task_id: str,
                        provenance: dict[str, Any]) -> None:
    if (row.get("schema") != "arcpuzzles-official-lineage-v1"
            or row.get("episode_id") != episode_id or row.get("task_id") != task_id
            or row.get("generator_sha256") != provenance.get("generator_sha256")
            or row.get("demonstration_policy") != provenance.get("demonstration_policy")
            or row.get("lesson_check") != provenance.get("lesson_check")
            or type(row.get("verified")) is not bool
            or not isinstance(row.get("reasons"), list)):
        raise ValueError("Generated episode lineage binding differs")
    evidence = row.get("evidence")
    if row.get("evidence_sha256") != (_identity(evidence) if evidence is not None else None):
        raise ValueError("Generated episode lineage evidence hash differs")
    if row["verified"]:
        if (row["reasons"] or not isinstance(evidence, dict)
                or evidence.get("mapping_status") != "verified"
                or evidence.get("generator_id") != task_id
                or evidence.get("source_hashes", {}).get("generator_sha256") != row["generator_sha256"]
                or evidence.get("source_split") not in ("training", "evaluation")
                or not isinstance(evidence.get("source_task_id"), str)
                or not re.fullmatch(r"[0-9a-f]{8}", evidence["source_task_id"])):
            raise ValueError("Verified generated episode lineage evidence differs")
        split, original = evidence["source_split"], evidence["source_task_id"]
        if (row.get("source_split") != split or row.get("source_task_id") != original
                or row.get("family_id") != f"official:{split}:{original}"):
            raise ValueError("Verified generated episode lineage family differs")
    elif (row.get("family_id") is not None or row.get("source_split") is not None
          or row.get("source_task_id") is not None or not row["reasons"]):
        raise ValueError("Unverified generated episode lineage must remain unresolved")


def verify_dataset(directory: str | Path) -> dict[str, Any]:
    """Verify a complete artifact's exact files and public/private episode binding."""
    root = Path(directory).resolve()
    if any(p.is_symlink() for p in root.rglob("*")):
        raise ValueError("Dataset artifacts cannot contain symlinks")
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("schema") != "arcpuzzles-dataset-v1" or manifest.get("status") != "complete":
        raise ValueError("Dataset is not a complete arcpuzzles-dataset-v1 export")
    if manifest.get("dataset_id") != _identity({k: v for k, v in manifest.items() if k != "dataset_id"}):
        raise ValueError("Dataset manifest identity differs")
    parametric_only = manifest['options'].get('parametric_only', False)
    if type(parametric_only) is not bool:
        raise ValueError('parametric_only must be a boolean')
    if parametric_only and manifest['options'].get('accepted_parameters') is not True:
        raise ValueError('Parametric-only exports require accepted_parameters')
    files = manifest["files"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - {"manifest.json"}
    if actual != set(files):
        raise ValueError("Dataset file inventory differs from its manifest")
    for name, expected in files.items():
        path = local_path(root, name)
        if not path.is_file() or sha256(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            raise ValueError(f"Dataset file changed: {name}")
    public = jsonl(root / "public.jsonl")
    private = jsonl(root / "labels.private.jsonl")
    if "lineage.private.jsonl" in files:
        lineage = jsonl(root / "lineage.private.jsonl")
        if len(lineage) != len(private):
            raise ValueError("Generated episode lineage count differs")
        for row, labels in zip(lineage, private):
            _verify_lineage_row(row, labels["episode_id"], labels["task_id"], labels["provenance"])
    ids = [r["episode_id"] for r in public]
    expected_count = 0 if manifest["options"]["style"] == "synthpipe" else manifest["accepted_episodes"]
    if (len(ids) != expected_count or len(set(ids)) != len(ids)
            or ids != [r["episode_id"] for r in private]):
        raise ValueError("Dataset public/private episode identities differ")
    for task, labels in zip(public, private):
        if (set(task) != {"episode_id", "train", "test"}
                or any(set(pair) != {"input", "output"} for pair in task["train"])
                or any(set(pair) != {"input"} for pair in task["test"])
                or len(task["test"]) != len(labels["test_outputs"])):
            raise ValueError("Dataset challenge projection contains unexpected fields or unmatched labels")
    if manifest["options"].get("tensors", "none") != "none":
        rows = jsonl(root / "data.private.jsonl")
        referenced = set()
        for row in rows:
            artifact = row.get("tensor_artifact", {})
            name = artifact.get("file", "")
            if (name in referenced or not name.endswith(".private.safetensors") or name not in files
                    or artifact.get("sha256") != files[name]["sha256"]
                    or artifact.get("bytes") != files[name]["bytes"]
                    or artifact.get("layout") != manifest["options"]["tensors"]):
                raise ValueError("Native row has an invalid or duplicate tensor artifact binding")
            referenced.add(name)
        if not rows or referenced != {n for n in files if n.endswith(".safetensors")}:
            raise ValueError("Native tensor inventory does not match its rows")
    if ('parametric.private.json' in files
            and manifest['options'].get('accepted_parameters') is not True):
        raise ValueError('Frozen parameter records require the explicit accepted_parameters option')
    if manifest['options'].get('accepted_parameters') is True:
        from .inline_parametric import verify
        verify(root, public, private, manifest['options'])
    if parametric_only:
        families = json.loads((root / 'parametric.private.json').read_text())['families']
        pool = json.loads((root / 'pool.private.json').read_text())['generators']
        if not pool or {row['id'] for row in pool} != set(families):
            raise ValueError('Parametric-only sampling pool contains a canonical-only family')
        episodes = jsonl(root / 'episodes.private.jsonl')
        if any('parametric' not in row for row in episodes):
            raise ValueError('Parametric-only dataset contains a canonical-only episode')
        # Valid generations can be retained after a failed render. Every
        # published episode must still resolve to validated parameter evidence.
        parameter_ids = {row['episode_id'] for row in episodes}
        if not set(ids) <= parameter_ids:
            raise ValueError('Parametric-only published episode lacks parameter evidence')
        _verify_preflight(root, pool, episodes, manifest['options'])
    return manifest


def export_dataset(catalog: Catalog, output: str | Path, *, count: int, seed: int = 0,
                   task_ids: list[str] | None = None, filters: dict[str, Any] | None = None,
                   style: str = "challenges", render: str = "raw", sampling: str = "weighted",
                   n_train: int | None = None, n_test: int | None = None, difficulty: str | None = None,
                   allow_unapproved: bool = False, max_attempts: int | None = None,
                   timeout: float = 180, modes: list[str] | None = None,
                   mutations: int = 8, stages: int = 3, system_prompt: str = "",
                   fence: bool = False, group_queries: bool = False,
                   tensors: str = "none", canvas_size: int = 30,
                   reference: str = "canonical", accepted_parameters: bool = False,
                   parametric_only: bool = False) -> dict[str, Any]:
    """Write a bounded export; return a manifest with explicit complete/incomplete status.

    Count denotes accepted generator episodes (synthetic chains for synthpipe),
    not rendered rows. An incomplete export retains evidence and is not reusable
    as a completed dataset. There are no automatic training or held-out splits.
    """
    if n_test is None:
        n_test = 4 if parametric_only is True else 1
    for name, value in (("count", count), ("n_train", n_train), ("n_test", n_test),
                        ("mutations", mutations), ("stages", stages)):
        if name == "n_train" and value is None:
            continue
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(accepted_parameters) is not bool:
        raise ValueError('accepted_parameters must be a boolean')
    if type(parametric_only) is not bool:
        raise ValueError('parametric_only must be a boolean')
    accepted_parameters = accepted_parameters or parametric_only
    if accepted_parameters and (reference != 'canonical' or style == 'synthpipe'):
        raise ValueError('Accepted parameters require a canonical generator-backed export')
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if style not in STYLES or render not in {"raw", "chatml", "harmony"}:
        raise ValueError("Unknown style or render")
    if reference not in {"canonical", "archival"}:
        raise ValueError("reference must be canonical or archival")
    if reference == "archival" and (not allow_unapproved or style == "synthpipe"):
        raise ValueError("Archival reference requires allow_unapproved and a generator-backed style")
    if render != "raw" and style not in {"grids", "code"}:
        raise ValueError("Chat renders require grids or code style")
    if type(group_queries) is not bool or tensors not in {"none", "native", "bottleneck"}:
        raise ValueError("Invalid native grouping or tensor layout")
    if type(canvas_size) is not int or not 1 <= canvas_size <= 30:
        raise ValueError("canvas_size must be an integer from 1 to 30")
    if style != "native" and (group_queries or tensors != "none" or canvas_size != 30):
        raise ValueError("Grouping and tensor options require native style")
    if tensors == "native" and (group_queries or (n_train is not None and n_train > 10)):
        raise ValueError("Native tensors require individual queries and at most 10 demonstrations")
    if tensors != "none" and any(importlib.util.find_spec(name) is None for name in ("torch", "safetensors")):
        raise ValueError("Tensor exports require the optional tensors dependencies: torch and safetensors")
    if sampling not in {"weighted", "uniform"}:
        raise ValueError("sampling must be weighted or uniform")
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")
    max_attempts = count * 2 if max_attempts is None else max_attempts
    if type(max_attempts) is not int or max_attempts < count:
        raise ValueError("max_attempts must be an integer at least count")
    modes = list(modes if modes is not None else ["predict", "synth", "exec", "invert"])
    if not modes or len(set(modes)) != len(modes) or set(modes) - set(MODES):
        raise ValueError("modes must be distinct supported DSL modes")
    filters = dict(filters or {})
    if set(filters) - FILTERS:
        raise ValueError(f"Unsupported filters: {sorted(set(filters) - FILTERS)}")
    if not allow_unapproved:
        if filters.get("approved") is False:
            raise ValueError("Unapproved sampling requires allow_unapproved")
        filters["approved"] = True
    filters["has_generator"] = True
    pool, exclusions = [], []
    if style != "synthpipe":
        selected = {catalog.resolve(tid) for tid in task_ids} if task_ids is not None else None
        if selected == set():
            raise ValueError("task_ids cannot be empty")
        for row in catalog.query(**filters):
            if selected is not None and row["id"] not in selected:
                continue
            weight = row.get("mix_weight", 0)
            if sampling == "weighted" and (type(weight) not in {int, float}
                                           or not math.isfinite(weight) or weight <= 0):
                exclusions.append({"task_id": row["id"], "reason": "nonpositive_or_invalid_mix_weight"})
                continue
            pool.append(row)
        if selected is not None and selected - {r["id"] for r in pool}:
            raise ValueError(f"Requested IDs do not meet the sampling filters: {sorted(selected - {r['id'] for r in pool})}")
        if not pool:
            raise ValueError("No generators match the sampling filters")
    elif task_ids or set(filters) - {"approved", "has_generator"}:
        raise ValueError("synthpipe creates random program chains; generator filters do not apply")

    parameter_plans = {}
    preflight = None
    if accepted_parameters:
        from . import inline_parametric
        if parametric_only:
            candidates = {row['id'] for row in pool
                          if inline_parametric.promotion._acceptance_path(catalog, row['id']).exists()
                          or inline_parametric.promotion._acceptance_path(catalog, row['id']).is_symlink()}
            if selected is not None and selected - candidates:
                raise ValueError('Requested IDs have no accepted parametric family: '
                                 + str(sorted(selected - candidates)))
            exclusions.extend({'task_id': row['id'], 'reason': 'no_accepted_parametric_family'}
                              for row in pool if row['id'] not in candidates)
            pool = [row for row in pool if row['id'] in candidates]
            if not pool:
                raise ValueError('No accepted parametric families match the sampling filters')
            checked = _reachable_tasks(pool, sampling, seed, max_attempts) | (selected or set())
            preflight = {'schema': 'arcpuzzles-parametric-preflight-v1',
                         'mode': 'bounded_draws_and_explicit_ids', 'explicit_tasks': sorted(selected or []),
                         'checked_tasks': sorted(checked), 'runtime_tasks': sorted(checked)}
        parameter_plans = inline_parametric.plan(catalog, pool, n_train, n_test, difficulty,
            parametric_only=parametric_only, check_ids=set(preflight['checked_tasks']) if preflight else None)
        if parametric_only and set(parameter_plans) != {row['id'] for row in pool}:
            raise ValueError('Accepted parameter snapshot does not cover the candidate pool')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    options = {"count": count, "seed": seed, "style": style, "render": render,
               "filters": filters, "sampling": sampling, "n_train": n_train, "n_test": n_test,
               "difficulty": difficulty, "allow_unapproved": allow_unapproved,
               "max_attempts": max_attempts, "timeout_per_worker": timeout, "modes": modes,
               "mutations": mutations, "stages": stages, "system_prompt": system_prompt, "fence": fence,
               "group_queries": group_queries, "tensors": tensors, "canvas_size": canvas_size,
               "reference": reference}
    if accepted_parameters:
        from .query_presentation import SCHEMA as presentation_schema
        options['query_presentation_schema'] = presentation_schema
        options['accepted_parameters'] = True
        options['duplicate_policy'] = 'visible_challenge'
        inline_parametric.snapshot(parameter_plans, output)
    if parametric_only:
        options['parametric_only'] = True
        options['parametric_preflight'] = preflight
    _dump(output / "plan.json", options)
    _dump(output / "pool.private.json", {"generators": pool, "exclusions": exclusions})
    for name in ("public.jsonl", "labels.private.jsonl", "lineage.private.jsonl", "episodes.private.jsonl",
                 "data.private.jsonl", "rejections.jsonl", "draws.private.jsonl"):
        (output / name).touch()
    accepted = attempts = rendered = 0
    row_counts: Counter[str] = Counter()
    seen: set[str] = set()
    manifest: dict[str, Any] = {"schema": "arcpuzzles-dataset-v1", "status": "incomplete",
                              "options": options, "split_policy": "No split assigned by export"}
    draws = _draw_sequence(pool, sampling, seed)
    lineage_cache: dict[str, dict[str, Any]] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="arcpuzzles-export-") as directory:
            stage = Path(directory)
            # Pure synthetic chains need only shared code. The existing selected
            # runtime surface requires one generator; its source is not sampled.
            ids = preflight['runtime_tasks'] if preflight else [r['id'] for r in pool]
            if not ids:
                ids = [catalog.query(has_generator=True, limit=1)[0]['id']]
            runtime = prepare_runtime(catalog, stage, task_ids=ids)
            policies, policy_errors = {}, {}
            for row in pool:
                try:
                    if row['id'] in parameter_plans:
                        item = parameter_plans[row['id']]
                        policies[row['id']] = {'automatic': n_train is None,
                            'declared_minimum': item['record']['limits']['demos'][0],
                            'resolved_n_train': item['demos'], 'basis': 'accepted_parametric_contract'}
                    else:
                        policies[row["id"]] = demonstration_policy(stage, row, n_train, default_floor=4)
                except (ValueError, SyntaxError) as exc:
                    # A malformed declaration is a source failure for this
                    # generator, not permission to weaken its lesson policy.
                    policy_errors[row["id"]] = {"error": type(exc).__name__, "reason": str(exc)}
            if tensors == "native" and any(p["resolved_n_train"] > 10 for p in policies.values()):
                raise ValueError("Native tensors require at most 10 resolved demonstrations per generator")
            runtime["demonstration_policies"] = policies
            runtime["demonstration_policy_errors"] = policy_errors
            runtime["api_files"] = {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
            _dump(output / "runtime.private.json", runtime)
            canonical_index = {}
            for line in (stage / "data/canonical/puzzles.jsonl").read_text().splitlines():
                if line.strip():
                    entry = json.loads(line)
                    canonical_index.setdefault(entry["task_id"], entry)
            while accepted < count and attempts < max_attempts:
                attempts += 1
                row, draw_seed = next(draws)
                draw = {"attempt": attempts, "seed": draw_seed, "task_id": row["id"] if row else "synthpipe"}
                _append(output / "draws.private.jsonl", draw)
                try:
                    episode, public = None, None
                    if row:
                        if row["id"] in policy_errors:
                            failure = policy_errors[row["id"]]
                            raise ValueError(f"Invalid demonstration policy ({failure['error']}): {failure['reason']}")
                        if row['id'] in parameter_plans:
                            episode = inline_parametric.generate(catalog, row, parameter_plans[row['id']],
                                seed=draw_seed, queries=n_test, timeout=timeout)
                        else:
                            episode, = generate_in_runtime(stage, row, count=1, seed=draw_seed,
                                                           difficulty=difficulty, n_train=n_train,
                                                           n_test=n_test, timeout=timeout, reference=reference,
                                                           default_n_train=4)
                        content = (inline_parametric.public_identity(episode) if accepted_parameters else
                                   _identity({"train": episode["train"], "test": episode["test"]}))
                        if content in seen:
                            raise ValueError('Duplicate visible challenge within this export' if accepted_parameters
                                             else 'Duplicate episode content within this export')
                        # Retain valid generations even if their requested render fails.
                        public = public_episode(episode)
                        _append(output / "episodes.private.jsonl", dict(episode, episode_id=public["episode_id"]))
                        if accepted_parameters:
                            seen.add(content)  # Retained generations also survive a later render failure.
                        for rejection in episode["rejections"]:
                            _append(output / "rejections.jsonl", {**draw, "stage": "pair", **rejection})
                        canonical = canonical_index.get(row.get("rule_task_id", row["id"]), {})
                        if 'parametric' in episode:
                            canonical = dict(canonical, written_solution='')
                    else:
                        canonical = {}
                    request = {**options, "n_train": (policies[row["id"]]["resolved_n_train"]
                               if row else (n_train if n_train is not None else 4)),
                               "seed": draw_seed, "episode": episode, "canonical": canonical,
                               'episode_id': public['episode_id'] if public else None}
                    _dump(stage / "export_request.json", request)
                    run = run_process([sys.executable, "-E", "-s", str(stage / "arcpuzzles_export_worker.py")],
                                      stage, timeout=timeout)
                    if run["timed_out"] or run["exit_code"] != 0:
                        raise GenerationFailure(draw["task_id"], run)
                    result = json.loads((stage / "export_result.json").read_text())
                    _append(output / "draws.private.jsonl", {**draw, "diagnostics": result["diagnostics"],
                                                             "rendered_rows": len(result["rows"])})
                    if style != "challenges" and not result["rows"]:
                        raise ValueError("Projection produced no rows; see retained diagnostics")
                    if style == "synthpipe" and result["diagnostics"]["truncated_stages"]:
                        _append(output / "rejections.jsonl", {**draw, "stage": "chain", **result["diagnostics"]})
                    artifacts = result.get("artifacts", {})
                    for name, expected in artifacts.items():
                        source, target = local_path(stage, name), local_path(output, name)
                        if (not name.endswith(".private.safetensors") or target.exists()
                                or source.is_symlink() or not source.is_file()
                                or sha256(source) != expected["sha256"] or source.stat().st_size != expected["bytes"]):
                            raise ValueError("Invalid or conflicting tensor artifact: " + name)
                    for name in artifacts:
                        shutil.copyfile(local_path(stage, name), local_path(output, name))
                    if public:
                        seen.add(content)
                        _append(output / "public.jsonl", public)
                        _append(output / "labels.private.jsonl", {"episode_id": public["episode_id"],
                                                                  "test_outputs": [p["output"] for p in episode["test"]],
                                                                  "provenance": episode["provenance"],
                                                                  "task_id": episode["task_id"], "seed": episode["seed"]})
                        if episode["task_id"] not in lineage_cache:
                            lineage_cache[episode["task_id"]] = catalog.lineage(episode["task_id"])
                        lineage = lineage_cache[episode["task_id"]]
                        _append(output / "lineage.private.jsonl",
                                _lineage_row(episode, public["episode_id"], lineage))
                    for item in result["rows"]:
                        _append(output / "data.private.jsonl", item)
                        row_counts[item.get("task_type", item.get("kind", style))] += 1
                    rendered += len(result["rows"])
                    accepted += 1
                except (ValueError, RuntimeError) as exc:
                    failure = {**draw, "stage": "episode_or_render", "error": type(exc).__name__, "reason": str(exc)}
                    if isinstance(exc, GenerationFailure):
                        failure["process"] = exc.run
                    stop = accepted_parameters and isinstance(exc, inline_parametric.AcceptedSnapshotError)
                    if stop:
                        failure['retryable'] = False
                        manifest['stop_reason'] = {'kind': 'accepted_parameter_snapshot_invalid',
                                                   'task_id': draw['task_id'], 'attempt': attempts}
                    _append(output / "rejections.jsonl", failure)
                    print(f"Rejected attempt {attempts}: {draw['task_id']}: {type(exc).__name__}", file=sys.stderr)
                    if stop:
                        break
            manifest["status"] = "complete" if accepted == count else "incomplete"
    finally:
        manifest.update({"accepted_episodes": accepted, "attempted_episodes": attempts,
                         "rendered_rows": rendered, "row_counts": dict(row_counts),
                         "files": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
                                   for p in sorted(output.iterdir()) if p.is_file() and p.name != "manifest.json"}})
        manifest["dataset_id"] = _identity(manifest)
        _dump(output / "manifest.json", manifest)
    return manifest

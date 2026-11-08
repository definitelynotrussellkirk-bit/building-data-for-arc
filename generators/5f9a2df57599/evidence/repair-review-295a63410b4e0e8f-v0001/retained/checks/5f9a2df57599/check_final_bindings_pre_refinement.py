"""Static final handoff verification; never import or execute a reference rule."""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import os
from pathlib import Path, PurePosixPath


CHECKS = Path(__file__).resolve().parent
WORK = CHECKS.parents[1]
ROOT = WORK / "repo"
TASK = "5f9a2df57599"
HOME = ROOT / f"generators/{TASK}/workspace/parametric"
AUDIT = CHECKS / "native-wall-teaching-audit-final"
EXPORT = CHECKS / "native-export-final"
FAMILY_SHA = "de0cff7b67ab090ada6a0ec7e77bc79c012451d54d35b937f0c40bd807cc08a0"
FILES, SECTIONS, FINDINGS, DATA = {}, {}, [], {}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def local(base, name):
    require(type(name) is str, "bound path is not a string")
    part = PurePosixPath(name)
    require(not part.is_absolute() and ".." not in part.parts, "bound path escapes its base")
    path = base / name
    require(path.resolve() == path.absolute() and path.is_file(), f"not a regular local file: {path}")
    require(path.resolve().is_relative_to(WORK), "bound file escapes the packet")
    return path


def sha(path):
    path = Path(path)
    require(path.resolve() == path.absolute() and path.is_file(), f"not a regular local file: {path}")
    name = path.relative_to(WORK).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    require(name not in FILES or FILES[name] == digest, f"file changed while reading: {name}")
    FILES[name] = digest
    return digest


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON field: {key}")
        result[key] = value
    return result


def read(path):
    sha(path)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def raw(value, newline=True):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + ("\n" if newline else "")).encode()


def digest(value, newline=True):
    return hashlib.sha256(raw(value, newline)).hexdigest()


def same(left, right, detail):
    require(raw(left) == raw(right), detail)


def grid(value):
    require(type(value) is list and 1 <= len(value) <= 30, "invalid grid rows")
    require(type(value[0]) is list and 1 <= len(value[0]) <= 30, "invalid grid columns")
    require(all(type(row) is list and len(row) == len(value[0]) and
                all(type(cell) is int and 0 <= cell <= 9 for cell in row) for row in value),
            "grid is not rectangular exact integer colors 0..9")


def visible(episode, query=None):
    tests = episode["test"] if query is None else [episode["test"][query]]
    return raw({"train": [{"input": pair["input"], "output": pair["output"]}
                          for pair in episode["train"]],
                "test": [{"input": pair["input"]} for pair in tests]})


def bound_rows(base, rows, count=None):
    require(type(rows) is list and rows, "empty file binding")
    require(len({row["path"] for row in rows}) == len(rows), "duplicate bound path")
    if count is not None:
        require(len(rows) == count, "unexpected bound file count")
    for row in rows:
        path = local(base, row["path"])
        require(sha(path) == row["sha256"], f"bound hash differs: {row['path']}")
        if "bytes" in row:
            require(path.stat().st_size == row["bytes"], f"bound size differs: {row['path']}")
    return len(rows)


def bound_map(base, mapping):
    return bound_rows(base, [{"path": name, "sha256": value} for name, value in mapping.items()])


def program(episode):
    value = episode.get("program", episode.get("program_solution"))
    require(type(value) is str and value.strip(), "episode has no exact program")
    return value


def jobkey(episode):
    return episode["seed"], raw(episode["settings"], False)


def episode_map(episodes):
    result = {}
    for episode in episodes:
        key = jobkey(episode)
        require(key not in result, "duplicate episode job")
        for pair in episode["train"] + episode["test"]:
            grid(pair["input"])
            grid(pair["output"])
        require(len({digest(pair["input"]) for pair in episode["train"] + episode["test"]}) ==
                len(episode["train"]) + len(episode["test"]), "duplicate episode inputs")
        result[key] = episode
    return result


def native_execution(execution, jobs, programs):
    require(len(execution["episodes"]) == len(execution["checks"]) == len(jobs), "native job count differs")
    episode_map(execution["episodes"])
    expected_calls = sum(len(programs) * job["demos"] + job["queries"] for job in jobs)
    require(execution["racket_evaluations"] == expected_calls, "native evaluation count differs")
    for episode, check, job in zip(execution["episodes"], execution["checks"], jobs, strict=True):
        require(episode["seed"] == job["seed"] and episode["task_id"] == TASK, "native job identity differs")
        same(episode["settings"], job["settings"], "native settings differ")
        require(len(episode["train"]) == job["demos"] and len(episode["test"]) == job["queries"], "native pair counts differ")
        expected_program = programs[raw(job["settings"], False).decode()]
        require(hashlib.sha256(program(episode).encode()).hexdigest() == episode["program_sha256"] == expected_program,
                "native exact program hash differs")
        same(check["settings"], job["settings"], "certificate settings differ")
        require(check["seed"] == job["seed"] and check["label_count"] == job["demos"] + job["queries"], "certificate counts differ")
        same(check["counts"], {"demos": job["demos"], "queries": job["queries"]}, "certificate request differs")
        same(check["survivors"], [job["settings"]], "native demo-only survivor differs")


def qualification():
    path = CHECKS / "qualification/qualification.json"
    qualified, execution = read(path), read(path.parent / "execution.json")
    require(qualified["status"] == "qualified" and qualified["task_id"] == TASK, "qualification is not qualified")
    require(qualified["training_admitted"] is False, "qualification claims training admission")
    binding = qualified["source_binding"]
    sources = bound_rows(ROOT, binding["files"], 152)
    executors = bound_map(ROOT / "src/arcpuzzles", binding["executor"])
    require(binding["task_id"] == binding["rule_task_id"] == TASK, "qualification task binding differs")
    require(sha(ROOT / f"generators/{TASK}/generator.py") == binding["generator_sha256"], "production source differs")
    require(sha(HOME / "native_family.py") == FAMILY_SHA, "qualified family is not final")
    require(qualified["execution"]["path"] == "execution.json" and sha(path.parent / "execution.json") == qualified["execution"]["sha256"], "qualification execution binding differs")
    same(qualified["contract"], read(HOME / "promotion.json"), "qualified contract differs")
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    sha(ledger)
    canonical = {row["program_solution"] for line in ledger.read_text().splitlines()
                 if (row := json.loads(line))["task_id"] == TASK}
    require(len(canonical) == 1, "canonical program is ambiguous")
    canonical = next(iter(canonical))
    require(hashlib.sha256(canonical.encode()).hexdigest() == binding["canonical_program_sha256"], "canonical exact source differs")
    require(hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12] == binding["rule_hash"], "canonical rule hash differs")
    native_execution(execution, qualified["jobs"], qualified["programs"])
    require(len(qualified["jobs"]) == 6 and execution["racket_evaluations"] == 60, "qualification expected six jobs and 60 calls")
    DATA.update(qualification=qualified, qualification_execution=execution)
    return {"source_files": sources, "executor_files": executors, "jobs": 6, "retained_evaluations": 60}


def inventory():
    value = read(HOME / "evidence/manifest.json")
    count = bound_rows(ROOT, value["files"], 26)
    require(value["variant_approved"] is False and value["training_admitted"] is False and
            value["builder_executed_checks"] is False, "inventory promotes execution or acceptance")
    binding = DATA["qualification"]["source_binding"]
    for field, target in (("generator_sha256", "generator_sha256"),
                          ("canonical_rule_hash", "rule_hash"),
                          ("canonical_program_sha256", "canonical_program_sha256")):
        require(value[field] == binding[target], "inventory canonical/source identity differs")
    copies = {
        "audit.json": "native-wall-teaching-audit-final/report.json",
        "examples-report.json": "native-export-final-report.json",
        "export-inspection.json": "native-export-inspection-final.json",
        "actor-conformance.json": "native-actor-conformance-final.json",
        "controller-conformance.json": "native-controller-conformance-final.json",
        "sampler.json": "sampler-final.json",
        "gate-native.json": "wall-gate-native.json",
        "gate-legacy.json": "wall-gate-legacy.json",
        "legacy-shortcut.json": "legacy-shortcut.json",
    }
    for destination, source in copies.items():
        require(sha(HOME / "evidence/current" / destination) == sha(CHECKS / source),
                f"inventory copy is not final evidence: {destination}")
    DATA["inventory"] = value
    return {"bound_files": count, "exact_evidence_copies": len(copies)}


def audit():
    report = read(AUDIT / "report.json")
    sources = bound_rows(ROOT, report["source_binding"]["files"], 14)
    artifacts = bound_rows(AUDIT, report["artifacts"], 5)
    bound_rows(AUDIT, report["programs"], 25)
    programs = {}
    for row in report["programs"]:
        require(Path(row["path"]).stem == row["sha256"], "audit program filename differs from bytes")
        programs[row["sha256"]] = (AUDIT / row["path"]).read_text()
    inputs, evaluations = read(AUDIT / "inputs.json"), read(AUDIT / "evaluations.json")
    episodes, checks = read(AUDIT / "episodes.json"), read(AUDIT / "checks.json")
    geometry = read(AUDIT / "independent-geometry.json")
    require(set(geometry) == set(inputs), "geometry/input inventories differ")
    for key, value in inputs.items():
        grid(value)
        require(digest(value) == key, "audit input content hash differs")
    matrix = {}
    for row in evaluations["evaluations"]:
        key = row["program_sha256"], row["input_sha256"]
        require(key not in matrix and key[0] in programs and key[1] in inputs, "duplicate or unknown audit evaluation")
        grid(row["output"])
        require(digest(row["output"]) == row["output_sha256"], "audit output hash differs")
        matrix[key] = row["output"]
    require(set(matrix) == set(itertools.product(programs, inputs)), "audit evaluation matrix is incomplete")
    require(len(matrix) == report["actual_evaluations"] == evaluations["actual_evaluations"] == 550, "audit call count differs")
    require(len(inputs) == report["unique_inputs"] == evaluations["unique_inputs"] == 22, "audit input count differs")
    require(len(programs) == report["unique_programs"] == evaluations["unique_programs"] == 25, "audit program count differs")
    require(report["status"] == "passed" and report["approved"] is False and
            report["query_labels_used_for_hypothesis_selection"] is False, "audit status/scope differs")
    require(len(episodes) == len(checks) == report["jobs"] == 6, "audit job count differs")
    episode_map(episodes)
    rival_rows = 0
    for episode, check in zip(episodes, checks, strict=True):
        same(check["settings"], episode["settings"], "audit job settings differ")
        require(check["seed"] == episode["seed"], "audit job seed differs")
        phash = hashlib.sha256(program(episode).encode()).hexdigest()
        require(phash == check["program_sha256"] == DATA["qualification"]["programs"][raw(episode["settings"], False).decode()], "audit intended program differs from qualification")
        pairs = episode["train"] + episode["test"]
        same(check["input_hashes"], [digest(pair["input"]) for pair in pairs], "audit input ordering differs")
        same(check["counts"], {"demos": len(episode["train"]), "queries": len(episode["test"])}, "audit counts differ")
        for pair in pairs:
            same(matrix[phash, digest(pair["input"])], pair["output"], "audit label differs from retained evaluation")
        demo_survivors, first_survivors = [], []
        for rival in check["rivals"]:
            rival_rows += 1
            rhash = rival["program_sha256"]
            for split, field in (("train", "demo_mismatch_indices"), ("test", "query_mismatch_indices")):
                mismatch = [index for index, pair in enumerate(episode[split])
                            if raw(matrix[rhash, digest(pair["input"])]) != raw(pair["output"])]
                same(mismatch, rival[field], "rival mismatch indices differ from retained evaluations")
            first = [index for index in rival["demo_mismatch_indices"] if index < 2]
            same(first, rival["first_two_demo_mismatch_indices"], "first-two rival mismatch differs")
            if not rival["demo_mismatch_indices"]:
                demo_survivors.append(rival["name"])
            if not first:
                first_survivors.append(rival["name"])
            require(first or (rival["structural_equivalence"] and
                    rival["structural_equivalence"]["equivalent_to"] == "intended" and not rival["query_mismatch_indices"]),
                    "a non-equivalent rival survives the first two demos")
        same(demo_survivors, check["demo_survivors_frozen_before_queries"], "stored demo survivor set differs")
        same(first_survivors, check["first_two_demo_survivors"], "stored first-two survivor set differs")
        require(check["version_space_used_query_labels"] is False and check["passed"] is True and
                check["two_demo_teaching_complete"] is True, "audit certificate scope differs")
    require(report["demonstrations"] == sum(len(ep["train"]) for ep in episodes) and
            report["queries"] == sum(len(ep["test"]) for ep in episodes), "audit pair totals differ")
    require(evaluations["cache_hits"] == report["cache_hits"] ==
            (report["demonstrations"] + report["queries"]) * 15 - len(matrix), "audit cache accounting differs")
    DATA.update(audit=report, audit_episodes=episodes, audit_evaluations=evaluations,
                audit_matrix=matrix, audit_geometry=geometry, audit_programs=programs)
    return {"source_files": sources, "artifact_files": artifacts, "program_files": len(programs),
            "unique_inputs": len(inputs), "retained_evaluations": len(matrix), "rival_certificates_checked": rival_rows}


def export():
    report = read(CHECKS / "native-export-final-report.json")
    manifest, context = read(EXPORT / "manifest.json"), read(EXPORT / "private/context.json")
    sources = bound_map(ROOT, report["source_sha256"])
    same(context["source_sha256"], report["source_sha256"], "private export source binding differs")
    same(context["contract"], DATA["qualification"]["contract"], "export contract differs from qualification")
    require(report["status"] == "passed" and report["training_admitted"] is False and
            report["native_acceptance"] == "owner_pending", "export status/scope differs")
    require(manifest["complete"] is True and manifest["training_admitted"] is False and
            sha(EXPORT / "manifest.json") == report["manifest_sha256"], "export completion/hash differs")
    files = bound_map(EXPORT, manifest["files"])
    require(files == 12 and {p.relative_to(EXPORT).as_posix() for p in EXPORT.rglob("*") if p.is_file()} ==
            set(manifest["files"]) | {"manifest.json"}, "export inventory is incomplete")
    execution = context["native_execution"]
    native_execution(execution, context["jobs"], DATA["qualification"]["programs"])
    require(digest(execution) == report["native_execution_sha256"] and execution["racket_evaluations"] == report["racket_evaluations"] == 20,
            "export native execution identity differs")
    metadata_path = EXPORT / "private/metadata.jsonl"
    sha(metadata_path)
    metadata = [json.loads(line, object_pairs_hook=unique) for line in metadata_path.read_text().splitlines()]
    require(len(metadata) == 2, "export must have two metadata rows")
    controllers, turns = [], []
    for row in metadata:
        episode, wrapper = row["episode"], row["episode"]["native_wrapper"]
        require(wrapper in execution["episodes"], "exact native wrapper was not retained")
        same(episode["train"], wrapper["train"], "export demo labels differ")
        same(episode["test"], wrapper["test"], "export query labels differ")
        require(episode["program_solution"] == wrapper["program"], "export program differs")
        controller = EXPORT / "private/controllers" / (row["controller_id"] + ".json")
        require(controller.read_bytes() == visible(wrapper) and sha(controller) == row["controller_id"], "controller content/identity differs")
        require(len(row["turn_ids"]) == len(wrapper["test"]) == 4, "private turn mapping count differs")
        for index, identifier in enumerate(row["turn_ids"]):
            path = EXPORT / "turns" / (identifier + ".json")
            require(path.read_bytes() == visible(wrapper, index) and sha(path) == identifier, "actor content/identity differs")
        single = {"train": wrapper["train"], "test": wrapper["test"][:1]}
        require(visible(single, 0) == visible(wrapper, 0), "first-turn bytes depend on future queries")
        controllers.append(row["controller_id"])
        turns.extend(row["turn_ids"])
    same(sorted(controllers), report["controller_ids"], "reported controller identifiers differ")
    same(sorted(turns), report["turn_ids"], "reported turn identifiers differ")
    require(len(set(turns)) == 8, "actor payloads repeat")
    for name, subdir, count, queries in (("actor", "turns", 8, 1), ("controller", "private/controllers", 2, 4)):
        check = read(CHECKS / f"native-{name}-conformance-final.json")
        require(check["status"] == "passed" and not check["findings"] and
                check["files_checked"] == count and check["queries"] == queries and check["demonstrations"] == 3,
                "final consumer conformance failed")
        for row in check["files"]:
            require(sha(EXPORT / subdir / Path(row["path"]).name) == row["sha256"], "consumer file binding differs")
    inspection = read(CHECKS / "native-export-inspection-final.json")
    require(inspection["status"] == "passed" and not inspection["findings"] and
            inspection["example_report_sha256"] == sha(CHECKS / "native-export-final-report.json") and
            inspection["manifest_sha256"] == sha(EXPORT / "manifest.json"), "final inspection binding differs")
    DATA.update(export_report=report, export_execution=execution, export_metadata=metadata)
    return {"source_files": sources, "payload_files": files, "controllers": len(controllers), "actor_files": len(turns), "retained_evaluations": 20}


def overlapping_jobs():
    collections = {"qualification": DATA["qualification_execution"]["episodes"],
                   "audit": DATA["audit_episodes"], "export": DATA["export_execution"]["episodes"]}
    result = []
    for left, right in itertools.combinations(collections, 2):
        first, second = episode_map(collections[left]), episode_map(collections[right])
        jobs, pairs, full = 0, 0, 0
        for key in first.keys() & second.keys():
            a, b = first[key], second[key]
            require(program(a) == program(b), f"program differs between {left} and {right}")
            jobs += 1
            full += all(len(a[split]) == len(b[split]) for split in ("train", "test"))
            for split in ("train", "test"):
                count = min(len(a[split]), len(b[split]))
                same(a[split][:count], b[split][:count], f"overlapping {split} labels differ between {left} and {right}")
                pairs += count
        require(jobs > 0, "expected overlapping jobs are missing")
        result.append({"left": left, "right": right, "jobs": jobs, "pair_comparisons": pairs, "equal_count_episodes": full})
    return {"comparisons": result}


def sampler():
    report = read(CHECKS / "sampler-final.json")
    sources = bound_map(ROOT, report["source_sha256"])
    require(sha(CHECKS / "probe_native_sampler.py") == report["helper_sha256"], "sampler helper differs")
    require(report["status"] == "passed" and report["failures"] == [] and report["requests"] == report["successes"] == 144,
            "sampler requests failed")
    require(len(report["seeds"]) * len(report["settings"]) * len(report["request_counts"]) == 144, "sampler request count differs")
    records = {(row["seed"], row["policy"]): row for row in report["generation_records"]}
    require(len(records) == len(report["generation_records"]) == 48, "sampler jobs repeat or are missing")
    all_inputs, query_inputs = set(), set()
    for record in records.values():
        require(len(record["fixtures"]["train"]) == 6 and len(record["fixtures"]["test"]) == 4, "sampler full bank count differs")
        for split in ("train", "test"):
            for row in record["fixtures"][split]:
                all_inputs.add(row["input_sha256"])
                if split == "test":
                    query_inputs.add(row["input_sha256"])
    require(len(all_inputs) == report["distinct_inputs"] and len(query_inputs) == report["distinct_query_inputs"], "sampler distinct input counters differ")
    overlaps = 0
    for episodes in (DATA["qualification_execution"]["episodes"], DATA["audit_episodes"], DATA["export_execution"]["episodes"]):
        for episode in episodes:
            policy = episode["settings"]["side_boundary_policy"]
            record = records.get((episode["seed"], policy))
            if record is None:
                continue
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    fixture = record["fixtures"][split][index]
                    require(digest(pair["input"], False) == fixture["input_sha256"], "sampler overlap input differs")
                    same([len(pair["input"]), len(pair["input"][0])], fixture["shape"], "sampler overlap shape differs")
                    require(sum(v == 4 for row in pair["output"] for v in row) == fixture["painted_cells"][policy], "sampler painted-cell count differs")
                    overlaps += 1
    DATA["sampler"] = report
    return {"source_files": sources, "requests_retained": 144, "metadata_jobs": len(records), "overlapping_inputs_checked": overlaps,
            "limits": "Sampler labels are Python claims; this static check validates retained hashes/counts and shared inputs, not a new sampler execution."}


def gates():
    checker = sha(HOME / "check_wall_teaching.py")
    rows = []
    for name, path, status, code in (("native", EXPORT / "private/metadata.jsonl", "passed", 0),
                                     ("legacy", CHECKS / "legacy-shortcut.json", "missing_contrast", 1)):
        report = read(CHECKS / f"wall-gate-{name}.json")
        command = read(CHECKS / f"wall-gate-{name}-command.json")
        require(report["checker_sha256"] == checker and report["input_sha256"] == sha(path), "gate checker/input binding differs")
        require(report["status"] == status and command["returncode"] == code, "gate result/exit differs")
        require((ROOT / command["payload"]["argv"][2]).resolve() == path, "gate command input differs")
        require(len(report["episodes"]) == 2 and all(row["status"] == status for row in report["episodes"]), "gate episode statuses differ")
        rows.append({"kind": name, "status": status, "expected_returncode": code, "episodes": 2})
    return {"checks": rows, "limits": "Checker/input hashes and retained outcomes only; the gate is not re-executed."}


def ast_value(path, name):
    sha(path)
    tree = ast.parse(path.read_text())
    nodes = [node.value for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    require(len(nodes) == 1, f"ambiguous static constant: {name}")
    node = nodes[0]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "frozenset":
        return frozenset(ast.literal_eval(node.args[0]))
    return ast.literal_eval(node)


def runtimes():
    expected = DATA["qualification_execution"]["racket"]
    require(expected["backend"] == "racket" and expected["protected"] is True, "reference execution was not protected Racket")
    values = {"audit": DATA["audit"]["racket"], "audit_evaluations": DATA["audit_evaluations"]["racket"],
              "export": DATA["export_report"]["racket"], "export_execution": DATA["export_execution"]["racket"],
              "causal_construction": DATA["causal"]["construction"]["racket"], "causal_replay": DATA["causal"]["replay"]["racket"]}
    for name, value in values.items():
        same(value, expected, f"runtime identity differs: {name}")
    bridge = ROOT / "shared/runtime/arc_repl/racket_bridge.py"
    security = ROOT / "shared/runtime/arc_repl/security.py"
    require(sha(bridge) == expected["bridge_sha256"], "current bridge hash differs")
    require(sha(ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt") == expected["prelude_sha256"], "current prelude hash differs")
    require(hashlib.sha256(ast_value(bridge, "_BOOT_SCRIPT").encode()).hexdigest() == expected["boot_script_sha256"], "current boot script hash differs")
    policy = {"schema": ast_value(security, "POLICY_SCHEMA"),
              "forbidden_global_symbols": sorted(ast_value(security, "FORBIDDEN_GLOBAL_SYMBOLS")),
              "forbidden_symbol_prefixes": list(ast_value(security, "FORBIDDEN_SYMBOL_PREFIXES"))}
    require(digest(policy, False) == expected["candidate_symbol_policy_sha256"], "current candidate policy hash differs")
    binary = WORK / ".review/racket-runtime/racket/bin/racket"
    if os.environ.get("RACKET_PATH"):
        require(Path(os.environ["RACKET_PATH"]).resolve() == binary, "launcher selected a different runtime binary")
    require(sha(binary) == expected["binary_sha256"], "current Racket binary hash differs")
    DATA["runtime"] = expected
    return {"matching_identities": len(values) + 1, "current_runtime_hashes_checked": 5,
            "reference_program_evaluations_performed": 0}


def causal():
    witness, replay = read(CHECKS / "causal/witness.json"), read(CHECKS / "causal/replay.json")
    recipe = read(CHECKS / "witness-recipe.json")
    binding = DATA["qualification"]["source_binding"]
    same(witness["source_binding"], binding, "witness source binding differs")
    same(replay["source_binding"], binding, "causal replay source binding differs")
    require(replay["qualification_sha256"] == sha(CHECKS / "qualification/qualification.json") and
            replay["witness_sha256"] == sha(CHECKS / "causal/witness.json"), "causal evidence hashes differ")
    require(replay["owner_acceptance"] == "not_performed" and replay["training_admitted"] is False and
            replay["status"] == replay["replay"]["status"] == "reviewer_replayed", "causal replay status differs")
    require(witness["racket"] == {"backend": "racket", "protected": True}, "witness runtime marker differs")
    require(len(witness["cases"]) == len(recipe["cases"]) == len(replay["replay"]["cases"]) == 2, "causal case count differs")
    require(replay["construction"]["evaluations"] == replay["replay"]["evaluations"] == 4, "causal evaluation counts differ")
    for field in ("step_a", "intermediate", "step_b", "why_b_depends_on_a"):
        same(witness[field], recipe[field], "causal recipe prose differs from witness")
    cases = []
    for index, (case, selected, checked) in enumerate(zip(witness["cases"], recipe["cases"], replay["replay"]["cases"], strict=True)):
        location = case["qualified_case"]
        same(location, {key: selected[key] for key in ("episode_index", "split", "pair_index")}, "causal qualified location differs")
        episode = DATA["qualification_execution"]["episodes"][location["episode_index"]]
        pair = episode[location["split"]][location["pair_index"]]
        same(case["settings"], episode["settings"], "causal setting differs")
        require(case["program"] == episode["program"] and case["counterfactual_program"] == selected["counterfactual_program"], "causal program source differs")
        same(case["intermediate_value"], selected["intermediate_value"], "authored causal intermediate differs")
        phash = hashlib.sha256(case["program"].encode()).hexdigest()
        rhash = hashlib.sha256(case["counterfactual_program"].encode()).hexdigest()
        require(phash == episode["program_sha256"] == checked["program_sha256"] and
                rhash == checked["counterfactual_program_sha256"] and checked["index"] == index, "causal program identity differs")
        require(DATA["audit_programs"][rhash] == case["counterfactual_program"], "causal rival is absent from the final audit")
        for field in ("input", "output"):
            same(case[field], pair[field], "causal input/label differs from qualification")
        for field in ("input", "output", "counterfactual_output"):
            same(case[field], checked[field], "causal replay case bytes differ")
        grid(case["counterfactual_output"])
        ihash = digest(case["input"])
        same(case["output"], DATA["audit_matrix"][phash, ihash], "causal intended label differs from audit")
        same(case["counterfactual_output"], DATA["audit_matrix"][rhash, ihash], "causal rival label differs from audit")
        policy = case["settings"]["side_boundary_policy"]
        same(case["intermediate_value"]["actual_four_connected_regions"], DATA["audit_geometry"][ihash][policy], "authored four-connected regions differ from final audit geometry")
        changed = sum(a != b for row_a, row_b in zip(case["output"], case["counterfactual_output"], strict=True)
                      for a, b in zip(row_a, row_b, strict=True))
        require(changed > 0 and changed == case["intermediate_value"]["expected_difference_cells_from_independent_python"], "causal changed-cell count differs")
        cases.append({"index": index, "qualified_case": location, "policy": policy,
                      "shape": [len(case["input"]), len(case["input"][0])], "changed_cells": changed,
                      "counterfactual_program_sha256": rhash})
    DATA["causal"] = replay
    return {"cases": cases, "retained_construction_evaluations": 4, "retained_replay_evaluations": 4,
            "limits": "Stored final labels agree across qualification, audit, witness and replay; authored intermediate interpretation is not independently proved."}


def receipts_and_scope():
    receipts = ("qualification-command.json", "native-wall-teaching-audit-final-command.json",
                "native-export-final-command.json", "native-export-inspection-final-command.json",
                "sampler-final-command.json", "causal-command.json", "manifest-final-command.json")
    for name in receipts:
        command = read(CHECKS / name)
        require(command["status"] == "completed" and command["returncode"] == 0, f"wrapper command did not complete: {name}")
    provisional = []
    family_path = f"generators/{TASK}/workspace/parametric/native_family.py"
    for relative in ("native-export-report.json", "native-wall-teaching-audit/report.json", "sampler.json"):
        report = read(CHECKS / relative)
        sources = report.get("source_sha256") or {row["path"]: row["sha256"] for row in report["source_binding"]["files"]}
        provisional.append({"path": str((CHECKS / relative).relative_to(WORK)), "sha256": sha(CHECKS / relative),
                            "family_sha256": sources[family_path], "status": "provisional_superseded",
                            "used_for_current_claims": False})
    require(not (ROOT / f"generators/{TASK}/parametric/accepted.json").exists(), "an owner acceptance artifact is present")
    DATA["provisional"] = provisional
    return {"successful_wrapper_receipts": len(receipts), "owner_acceptance": "not_performed",
            "training_admitted": False, "provisional_reports": provisional}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=CHECKS / "final-binding.json")
    args = parser.parse_args(argv)
    require(not args.out.exists() and not args.out.is_symlink(), "binding report must be fresh")
    sha(Path(__file__))
    for name, check in (("qualification", qualification), ("inventory", inventory), ("audit", audit),
                        ("export", export), ("overlapping_jobs", overlapping_jobs), ("sampler", sampler),
                        ("gates", gates), ("causal", causal), ("runtimes", runtimes),
                        ("receipts_and_scope", receipts_and_scope)):
        try:
            SECTIONS[name] = {"status": "passed", **check()}
        except Exception as error:
            finding = {"section": name, "type": type(error).__name__, "detail": str(error)}
            FINDINGS.append(finding)
            SECTIONS[name] = {"status": "failed", "finding": finding}
    drift = [name for name, expected in FILES.items()
             if not (WORK / name).is_file() or hashlib.sha256((WORK / name).read_bytes()).hexdigest() != expected]
    if drift:
        FINDINGS.append({"section": "publication", "type": "SourceDrift", "detail": drift})
    report = {
        "schema": "arcpuzzles-wall-final-static-binding-v1", "task_id": TASK,
        "status": "failed" if FINDINGS else "passed", "findings": FINDINGS,
        "family_sha256": FAMILY_SHA, "checker_sha256": sha(Path(__file__)),
        "sections": SECTIONS, "files_checked": len(FILES), "file_sha256": dict(sorted(FILES.items())),
        "runtime_identity": DATA.get("runtime"), "owner_acceptance": "not_performed",
        "training_admitted": False, "reference_program_evaluations_performed": 0,
        "material_cross_component_concerns": [],
        "limits": [
            "Static hashes and retained-output consistency only; no generator, audit, gate or Racket reference program is executed.",
            "Qualification, audit, export and causal evaluation counts are retained prior execution evidence, not new executions by this checker.",
            "Only final audit/export/sampler artifacts support current-family claims; earlier native reports remain provisional and superseded.",
            "Causal intermediate values and interpretation remain authored metadata; label parity is not a universal causal-depth proof.",
            "Finite seeds/rivals and sampler claims do not establish all-seed coverage, learned benefit, owner acceptance or training admission.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "files_checked": report["files_checked"],
                      "findings": FINDINGS, "out": str(args.out)}, sort_keys=True))
    return int(bool(FINDINGS))


if __name__ == "__main__":
    raise SystemExit(main())

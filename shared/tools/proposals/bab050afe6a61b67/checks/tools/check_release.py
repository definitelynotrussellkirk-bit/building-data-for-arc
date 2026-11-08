#!/usr/bin/env python3
"""Read-only final evidence consistency for the two targets named by RESULTS.

Uses only the standard library: no repository imports, adapter execution,
Racket evaluation, replay, acceptance or training admission. Other explicitly
listed evidence (including before/review-regression records) is hashed without
asserting that its historical source bindings describe the current source.

From the packet launcher:
  python3 ../checks/tools/check_release.py --root . --results ../RESULTS.json \
    --out ../checks/release.json
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import re
import sys


EXECUTORS = {"parametric_promotion.py", "parametric_worker.py", "catalog.py", "runtime.py", "parametric_priority.py"}
DESCRIPTIONS = ("step_a", "intermediate", "step_b", "why_b_depends_on_a")


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, low, high):
    need(type(value) is int and low <= value <= high, f"Expected exact integer in {low}..{high}: {value!r}")
    return value


def grid(value):
    need(type(value) is list and 1 <= len(value) <= 30 and type(value[0]) is list
         and 1 <= len(value[0]) <= 30, "Invalid grid dimensions")
    need(all(type(row) is list and len(row) == len(value[0]) and
             all(type(cell) is int and 0 <= cell <= 9 for cell in row) for row in value),
         "Grid must be rectangular with exact integer colors")


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("Non-finite JSON value: " + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


class Audit:
    def __init__(self, root):
        self.root = Path(os.path.abspath(root))
        self.work = self.root.parent
        self.files = {}
        self.path(self.root)

    def path(self, value, base=None):
        path = Path(value)
        if not path.is_absolute():
            path = (base or self.work) / path
        need(not any(p.is_symlink() for p in (path, *path.parents)), "Symlink in evidence path: " + str(path))
        path = Path(os.path.abspath(path))
        need(path.is_relative_to(self.work) and path.resolve() == path, "Evidence path escapes workspace: " + str(path))
        return path

    def relative(self, value, base=None):
        need(type(value) is str and value and not Path(value).is_absolute()
             and ".." not in Path(value).parts and "\\" not in value and "\0" not in value,
             "Invalid relative evidence/source path")
        return self.path(value, base)

    def read(self, path, role, expected=None):
        path = self.path(path)
        need(path.is_file(), "Missing regular evidence/source file: " + str(path))
        data = path.read_bytes()
        digest = sha(data)
        if expected is not None:
            need(type(expected) is str and re.fullmatch("[0-9a-f]{64}", expected) is not None
                 and expected == digest, "Stale or changed " + role + ": " + str(path))
        key = path.relative_to(self.work).as_posix()
        row = self.files.setdefault(key, {"path": key, "sha256": digest, "bytes": len(data), "roles": []})
        need(row["sha256"] == digest, "File changed during consistency check: " + key)
        if role not in row["roles"]:
            row["roles"].append(role)
        return data

    def json(self, path, role, expected=None):
        return decode(self.read(path, role, expected))

    def inventory(self, rows, role, *, base, home=None):
        need(type(rows) is list and rows, "Missing " + role + " inventory")
        found = {}
        for item in rows:
            need(type(item) is dict and item.get("path") not in found, "Invalid/duplicate " + role + " row")
            path = self.relative(item["path"], base)
            if home is not None:
                need(path.is_relative_to(home), "Inventory file is outside its task home")
            data = self.read(path, role, item["sha256"])
            if "bytes" in item:
                need(type(item["bytes"]) is int and item["bytes"] == len(data), "Inventory byte count differs")
            found[item["path"]] = item["sha256"]
        return found

    def selected_jsonl(self, path, key, selected):
        found = {value: [] for value in selected}
        for line in self.read(path, "current identity ledger").splitlines():
            if line.strip():
                row = decode(line)
                if row.get(key) in found:
                    found[row[key]].append(row)
        return found

    def source_binding(self, tid, q, progress, catalog, canonical, counts):
        binding, contract = q["source_binding"], q["contract"]
        home, base = self.root / "generators" / tid, self.root / "generators" / tid / "workspace/parametric"
        generator = self.relative(catalog["generator"], self.root)
        authority = catalog.get("rule_task_id", tid)
        programs = {row.get("program_solution") for row in canonical[authority]}
        need(len(programs) == 1 and all(type(p) is str and p.strip() for p in programs), "Canonical program is missing or ambiguous")
        canonical_program = next(iter(programs))
        need(binding["task_id"] == tid and binding["rule_task_id"] == authority
             and binding["generator_sha256"] == sha(self.read(generator, "current generator"))
             and binding["rule_hash"] == sha(" ".join(canonical_program.split()).encode())[:12]
             and binding["canonical_program_sha256"] == sha(canonical_program.encode()), "Current source/canonical identity differs from qualification")
        promotion = self.relative(progress["promotion_path"])
        need(promotion == base / "promotion.json" and raw(self.json(promotion, "promotion contract")) == raw(contract), "Current promotion contract differs")
        need(contract["schema"] == "arcpuzzles-parametric-adapter-v1", "Wrong adapter contract schema")
        adapter = self.relative(contract["adapter"], self.root)
        need(adapter.is_relative_to(base) and adapter.suffix == ".py", "Adapter is not task-local")
        expected = {generator, promotion, adapter}
        parser = self.root / "shared/tools/comment_solutions.py"
        if parser.is_file():
            expected.add(parser)
        for directory in (base, self.root / "shared/runtime"):
            for path in directory.rglob("*"):
                if (path.is_file() and path.suffix in {".py", ".rkt", ".json"}
                        and not {"evidence", "examples", "__pycache__"} & set(path.relative_to(directory).parts)):
                    expected.add(self.path(path))
        for name in contract.get("resources", []):
            resource = self.relative(name, self.root)
            need(resource.is_relative_to(base), "Contract resource is not task-local")
            expected.add(resource)
        sources = self.inventory(binding["files"], "qualified source", base=self.root)
        need(set(sources) == {p.relative_to(self.root).as_posix() for p in expected}, "Qualification source closure differs from current files")
        need(set(binding["executor"]) == EXECUTORS, "Incomplete native executor inventory")
        for name, digest in binding["executor"].items():
            self.read(self.root / "src/arcpuzzles" / name, "native executor", digest)
        counts.update(qualification_sources=len(sources), executor_modules=len(EXECUTORS))
        inventory = self.json(self.relative(progress["inventory_path"]), "task inventory")
        need(inventory["schema"] == "arcpuzzles-parametric-prototype-evidence-v1" and inventory["task_id"] == tid,
             "Wrong task inventory identity")
        for left, right in (("generator_sha256", "generator_sha256"), ("canonical_rule_hash", "rule_hash"),
                            ("canonical_program_sha256", "canonical_program_sha256"), ("rule_task_id", "rule_task_id")):
            need(inventory[left] == binding[right], "Task inventory source identity differs: " + left)
        for key in ("parameters", "default", "limits"):
            need(raw(inventory[key]) == raw(contract[key]), "Task inventory contract differs: " + key)
        need(inventory.get("training_admitted") is False, "Task inventory must not claim training admission")
        included = self.inventory(inventory["files"], "task inventory file", base=self.root, home=home)
        task_sources = {p.relative_to(self.root).as_posix() for p in expected if p.is_relative_to(home)}
        need(task_sources <= set(included), "Task inventory omits current task source")
        counts["inventory_files"] = len(included)

    def execution(self, tid, q, execution, counts):
        contract, binding = q["contract"], q["source_binding"]
        parameters = contract["parameters"]
        need(type(parameters) is dict and parameters, "Missing finite parameters")
        for key, values in parameters.items():
            need(type(key) is str and key.isidentifier() and type(values) is list and values
                 and all(type(v) in {str, int, bool} for v in values)
                 and len({raw(v) for v in values}) == len(values), "Invalid finite parameter options")
        names = sorted(parameters)
        settings = {raw(dict(zip(names, values))) for values in product(*(parameters[name] for name in names))}
        need(2 <= len(settings) <= 16 and raw(contract["default"]) in settings, "Invalid finite settings/default")
        jobs, episodes, checks = q["jobs"], execution["episodes"], execution["checks"]
        need(type(jobs) is list and 1 <= len(jobs) <= 128 and type(episodes) is list and type(checks) is list
             and len(jobs) == len(episodes) == len(checks), "Incomplete native qualification execution")
        coverage, evaluations = {}, 0
        for job, episode, check in zip(jobs, episodes, checks):
            seed, demos, queries = integer(job["seed"], 0, 2**63-1), integer(job["demos"], 2, 6), integer(job["queries"], 4, 32)
            for key, number in (("demos", demos), ("queries", queries)):
                low, high = contract["limits"][key]
                integer(low, 1, 32); integer(high, low, 32); integer(number, low, high)
            setting = raw(job["settings"])
            need(setting in settings and seed not in coverage.setdefault(setting, set()), "Undeclared or duplicate qualification job")
            coverage[setting].add(seed)
            need(episode["task_id"] == tid and type(episode["seed"]) is int and episode["seed"] == seed
                 and raw(episode["settings"]) == setting and type(check["seed"]) is int and check["seed"] == seed
                 and raw(check["settings"]) == setting and raw(check["counts"]) == raw({"demos": demos, "queries": queries})
                 and type(check["label_count"]) is int and check["label_count"] == demos + queries
                 and raw(check["survivors"]) == raw([job["settings"]]), "Native job/check identity differs")
            program_hash = sha(episode["program"].encode())
            need(program_hash == episode["program_sha256"] == q["programs"][setting.decode().strip()], "Qualified program bytes/hash differ")
            if setting == raw(contract["default"]):
                need(program_hash == binding["canonical_program_sha256"], "Default program differs from canonical bytes")
            inputs = []
            for split, count in (("train", demos), ("test", queries)):
                need(type(episode[split]) is list and len(episode[split]) == count, "Qualified pair count differs")
                for pair in episode[split]:
                    need(type(pair) is dict and set(pair) == {"input", "output"}, "Invalid qualified pair")
                    grid(pair["input"]); grid(pair["output"]); inputs.append(raw(pair["input"]))
            need(len(inputs) == len(set(inputs)), "Qualified inputs are not distinct")
            evaluations += len(settings) * demos + queries
        need(set(coverage) == settings and all(2 <= len(s) <= 8 for s in coverage.values())
             and set(q["programs"]) == {s.decode().strip() for s in settings}, "Incomplete qualification coverage")
        need(type(execution["racket_evaluations"]) is int and execution["racket_evaluations"] == evaluations,
             "Native evaluation-count claim differs from its job scope")
        identity = execution["racket"]
        need(identity.get("schema") == "arc-protected-racket-runtime-v1" and identity.get("backend") == "racket"
             and identity.get("protected") is True, "Missing protected Racket identity claim")
        for key in ("binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"):
            need(type(identity.get(key)) is str and re.fullmatch("[0-9a-f]{64}", identity[key]), "Invalid runtime identity hash: " + key)
        source_hashes = {row["path"]: row["sha256"] for row in binding["files"]}
        need(identity["bridge_sha256"] == source_hashes["shared/runtime/arc_repl/racket_bridge.py"]
             and identity["prelude_sha256"] == source_hashes["shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"], "Runtime source identity differs from qualification binding")
        counts["qualified_jobs"] = len(jobs)

    def causal(self, tid, progress, qpath, q, execution, counts):
        dependency = progress["sequential_dependency"]
        path = self.relative(dependency["witness_path"])
        witness = self.json(path, "causal witness")
        need(witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
             and raw(witness["source_binding"]) == raw(q["source_binding"])
             and raw(witness["racket"]) == raw({"backend": "racket", "protected": True}), "Causal witness source binding differs")
        need(all(type(witness[k]) is str and witness[k].strip() and witness[k] == dependency[k] for k in DESCRIPTIONS), "Causal descriptions differ from RESULTS")
        cases = witness["cases"]
        need(type(cases) is list and 1 <= len(cases) <= 16, "Invalid causal case count")
        for case in cases:
            for key in ("input", "output", "counterfactual_output"):
                grid(case[key])
            need(case["output"] != case["counterfactual_output"] and case.get("intermediate_value") is not None
                 and case["ablation"] in {"skip_a", "wrong_intermediate", "wrong_order"}, "Causal counterfactual must change the label")
            for key in ("program", "counterfactual_program"):
                need(type(case[key]) is str and case[key].strip(), "Empty causal program")
            setting = raw(case["settings"]).decode().strip()
            need(sha(case["program"].encode()) == q["programs"].get(setting), "Causal program is not a qualified setting program")
            selection = case["qualified_case"]
            episode = execution["episodes"][integer(selection["episode_index"], 0, len(execution["episodes"])-1)]
            need(selection["split"] in {"train", "test"}, "Invalid causal qualified split")
            pairs = episode[selection["split"]]
            pair = pairs[integer(selection["pair_index"], 0, len(pairs)-1)]
            need(raw({k: case[k] for k in ("settings", "program", "input", "output")}) ==
                 raw({"settings": episode["settings"], "program": episode["program"], **pair}), "Causal case differs from its qualified pair")
        replay = self.json(path.with_name("replay.json"), "causal replay record")
        need(replay["schema"] == "arcpuzzles-reviewer-witness-check-v1" and replay["status"] == "reviewer_replayed"
             and replay["task_id"] == tid and raw(replay["source_binding"]) == raw(q["source_binding"])
             and replay["qualification_sha256"] == sha(self.read(qpath, "qualification"))
             and replay["witness_sha256"] == sha(self.read(path, "causal witness"))
             and replay.get("training_admitted") is False and replay.get("owner_acceptance") == "not_performed", "Causal replay hash/source/provenance differs")
        record = replay["replay"]
        need(record["status"] == "reviewer_replayed" and raw(record["racket"]) == raw(execution["racket"])
             and type(record["evaluations"]) is int and record["evaluations"] == 2 * len(cases)
             and len(record["cases"]) == len(cases), "Causal replay scope/runtime differs")
        for index, (case, result) in enumerate(zip(cases, record["cases"])):
            need(type(result["index"]) is int and result["index"] == index
                 and all(raw(result[k]) == raw(case[k]) for k in ("input", "output", "counterfactual_output"))
                 and result["program_sha256"] == sha(case["program"].encode())
                 and result["counterfactual_program_sha256"] == sha(case["counterfactual_program"].encode()), "Causal replay case/program hashes differ")
        if "construction" in replay:
            construction = replay["construction"]
            need(raw(construction["racket"]) == raw(execution["racket"]) and type(construction["evaluations"]) is int
                 and construction["evaluations"] == 2 * len(cases), "Causal construction identity/scope differs")
        counts["causal_cases"] = len(cases)

    def export(self, tid, path, qpath, q, execution, counts):
        manifest = self.json(path, "qualified export manifest")
        qhash, ehash = sha(self.read(qpath, "qualification")), q["execution"]["sha256"]
        need(manifest["schema"] == "arc-qualified-single-query-export-v1" and manifest["task_id"] == tid
             and manifest["status"] == "qualified_owner_acceptance_pending" and manifest["owner_acceptance"] == "pending"
             and manifest["accepted"] is False and manifest["training_admitted"] is False
             and self.relative(manifest["qualification_path"]) == qpath
             and manifest["qualification_sha256"] == qhash and manifest["execution_sha256"] == ehash
             and manifest["source_binding_sha256"] == sha(raw(q["source_binding"]))
             and raw(manifest["racket"]) == raw(execution["racket"]), "Export source/provenance differs from final qualification")
        need(type(manifest["controller_queries"]) is int and manifest["controller_queries"] == 4, "Final export requires four private controller queries")
        self.read(self.work / "checks/tools/export_qualified.py", "exporter source", manifest["exporter_sha256"])
        files = self.inventory(manifest["files"], "qualified export payload", base=path.parent)
        actual = {p.relative_to(path.parent).as_posix() for p in path.parent.rglob("*") if p.is_file()}
        need(actual == set(files) | {path.name}, "Unlisted or missing export files")
        actors, controllers = {}, []
        for name, digest in files.items():
            need(re.fullmatch(r"(?:actor|private/controllers)/[0-9a-f]{64}\.json", name), "Unexpected export payload path")
            payload_path = self.relative(name, path.parent)
            data = self.read(payload_path, "qualified export payload", digest)
            need(payload_path.stem == sha(data), "Export content ID is not the exact payload hash")
            payload = decode(data)
            if name.startswith("actor/"):
                need(set(payload) == {"train", "test"} and type(payload["train"]) is list and 2 <= len(payload["train"]) <= 6
                     and type(payload["test"]) is list and len(payload["test"]) == 1
                     and set(payload["test"][0]) == {"input"} and data == raw(payload), "Actor payload exposes extra fields or is not canonical single-query bytes")
                grid(payload["test"][0]["input"])
                for pair in payload["train"]:
                    need(set(pair) == {"input", "output"}, "Actor demonstrations have unexpected fields")
                    grid(pair["input"]); grid(pair["output"])
                actors[name] = data
            else:
                controllers.append(payload)
        used, seeds, demos = set(), set(), set()
        for controller in controllers:
            need(controller["schema"] == "arc-qualified-single-query-controller-v1" and controller["task_id"] == tid
                 and controller["status"] == "qualified_owner_acceptance_pending" and controller["accepted"] is False
                 and controller["training_admitted"] is False and controller["qualification_sha256"] == qhash
                 and controller["execution_sha256"] == ehash, "Controller provenance differs")
            seed = integer(controller["seed"], 0, 2**63-1)
            matches = [e for e in execution["episodes"] if e["seed"] == seed and raw(e["settings"]) == raw(controller["settings"])]
            need(len(matches) == 1, "Controller does not select one qualified episode")
            episode = matches[0]
            need(all(raw(controller[k]) == raw(episode[k]) for k in ("program", "program_sha256", "train"))
                 and type(controller["queries"]) is list and len(controller["queries"]) == 4, "Controller differs from qualified episode")
            for index, turn in enumerate(controller["queries"]):
                need(type(turn["turn_index"]) is int and turn["turn_index"] == index and turn["actor_path"] in actors
                     and turn["public_id"] == sha(actors[turn["actor_path"]])
                     and raw({k: turn[k] for k in ("input", "output")}) == raw(episode["test"][index])
                     and actors[turn["actor_path"]] == raw({"train": episode["train"], "test": [{"input": turn["input"]}]}), "Actor/controller projection differs from current qualified query")
                used.add(turn["actor_path"])
            seeds.add(seed); demos.add(len(controller["train"]))
        need(used == set(actors) and controllers and type(manifest["actor_file_count"]) is int
             and manifest["actor_file_count"] == len(actors) and type(manifest["controller_count"]) is int
             and manifest["controller_count"] == len(controllers) and raw(manifest["seeds"]) == raw(sorted(seeds))
             and raw(manifest["demos"]) == raw(sorted(demos)), "Export counts or actor inventory differ")
        counts["export_controllers"] = counts.get("export_controllers", 0) + len(controllers)
        counts["actor_files"] = counts.get("actor_files", 0) + len(actors)

    def target(self, row, catalog, canonical, counts):
        tid, progress = row["task_id"], row["parametric_work"]
        need(progress.get("status") == "ready", "Target is not marked ready")
        need(type(row.get("evidence_paths")) is list and row["evidence_paths"], "No explicit target evidence")
        exports = set()
        for name in row["evidence_paths"]:
            path = self.relative(name)
            need(path.exists(), "Missing explicit RESULTS evidence: " + name)
            selected = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
            for item in selected:
                data = self.read(item, "explicit RESULTS evidence")
                if item.name == "manifest.json" and not re.search(r"before|review[-_]regression", item.as_posix()):
                    try:
                        if decode(data).get("schema") == "arc-qualified-single-query-export-v1":
                            exports.add(item)
                    except (ValueError, AttributeError):
                        pass
        qpath = self.relative(progress["qualification_path"])
        q = self.json(qpath, "qualification")
        need(q["schema"] == "arcpuzzles-parametric-qualification-v1" and q["status"] == "qualified" and q["task_id"] == tid
             and q.get("training_admitted") is False and q.get("owner_acceptance_reexecuted", False) is False,
             "Expected exact-task owner-pending native qualification")
        need(q["execution"]["path"] == "execution.json", "Qualification execution must be a sibling")
        execution = self.json(qpath.with_name("execution.json"), "qualified execution", q["execution"]["sha256"])
        self.source_binding(tid, q, progress, catalog, canonical, counts)
        self.execution(tid, q, execution, counts)
        self.causal(tid, progress, qpath, q, execution, counts)
        need(exports, "No qualified-export manifest explicitly referenced by this RESULTS target")
        for path in sorted(exports):
            self.export(tid, path, qpath, q, execution, counts)


def check_release(root, results):
    audit = Audit(root)
    report = {"schema": "arc-review-release-consistency-v1", "status": "inconsistent", "task_ids": [],
              "findings": [], "source_counts": [], "racket_replay_performed": False,
              "owner_acceptance_performed": False, "training_admitted": False,
              "scope": "Static hashes and cross-file consistency of explicit RESULTS evidence, final qualification/source closure, task inventory, causal witness/replay and single-query exports. Historical evidence is hash-only; no semantic replay or universal causal proof.",
              "checker_sha256": sha(Path(__file__).read_bytes())}
    try:
        results_path = audit.path(Path(os.path.abspath(results)))
        rows = audit.json(results_path, "RESULTS")["repair_targets"]
        need(type(rows) is list and len(rows) == 2 and all(type(row) is dict and type(row.get("task_id")) is str
             and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", row["task_id"]) for row in rows), "RESULTS must explicitly name two targets")
        ids = [row["task_id"] for row in rows]
        need(len(set(ids)) == 2, "Duplicate RESULTS task IDs")
        report["task_ids"] = ids
        catalog = audit.selected_jsonl(audit.root / "catalog/puzzles.jsonl", "id", ids)
        need(all(len(catalog[tid]) == 1 for tid in ids), "Current catalog must contain each exact RESULTS task once")
        catalog = {tid: catalog[tid][0] for tid in ids}
        authorities = {catalog[tid].get("rule_task_id", tid) for tid in ids}
        canonical = audit.selected_jsonl(audit.root / "shared/data/canonical/puzzles.jsonl", "task_id", authorities)
        for row in rows:
            counts = {"task_id": row["task_id"]}
            try:
                audit.target(row, catalog[row["task_id"]], canonical, counts)
            except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as error:
                report["findings"].append({"task_id": row["task_id"], "message": str(error)})
            report["source_counts"].append(counts)
        for row in list(audit.files.values()):
            audit.read(audit.work / row["path"], "final stability check", row["sha256"])
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as error:
        report["findings"].append({"task_id": None, "message": str(error)})
    report["hashed_files"] = [audit.files[name] for name in sorted(audit.files)]
    report["hashed_file_count"] = len(report["hashed_files"])
    report["status"] = "consistent" if not report["findings"] else "inconsistent"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "repo")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        destination = Audit(args.root).path(Path(os.path.abspath(args.out)))
        need(not destination.exists(), "Choose a fresh release-report output path")
        report = check_release(args.root, args.results)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
            handle.write(raw(report))
        print(json.dumps({"report": str(destination), "status": report["status"],
                          "findings": report["findings"], "hashed_file_count": report["hashed_file_count"],
                          "source_counts": report["source_counts"], "racket_replay_performed": False}, sort_keys=True))
        return 0 if report["status"] == "consistent" else 1
    except (OSError, ValueError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Check retained branch release bindings using only bytes and JSON.

No project helper, generator, sampler, reference program or Racket is executed.
The fixed artifact paths identify this task's release; --out must be fresh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


TASK = "d8111f3f714d"
SELF = Path(__file__).resolve()
WORK = SELF.parents[2]
REPO = WORK / "repo"
CHECKS = WORK / "checks" / TASK
HOME = REPO / "generators" / TASK / "workspace/parametric"


def raw(value, newline=True):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + ("\n" if newline else "")).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def equal(left, right):
    return raw(left) == raw(right)


def grid(value):
    require(type(value) is list and 1 <= len(value) <= 30 and type(value[0]) is list
            and 1 <= len(value[0]) <= 30, "invalid retained grid dimensions")
    require(all(type(row) is list and len(row) == len(value[0])
                and all(type(v) is int and 0 <= v <= 9 for v in row) for row in value),
            "invalid retained integer grid")
    return value


def setting_key(settings):
    return raw(settings, False).decode()


def episode_key(episode):
    return episode["seed"], setting_key(episode["settings"])


def visible(episode, query=None):
    tests = episode["test"] if query is None else [episode["test"][query]]
    return raw({"train": [{"input": grid(p["input"]), "output": grid(p["output"])}
                          for p in episode["train"]],
                "test": [{"input": grid(p["input"])} for p in tests]})


def differences(left, right):
    grid(left); grid(right)
    require((len(left), len(left[0])) == (len(right), len(right[0])), "output shapes differ")
    return [[r, c] for r, row in enumerate(left) for c, value in enumerate(row) if value != right[r][c]]


class Check:
    def __init__(self):
        self.files, self.cache, self.sections, self.findings, self.state = {}, {}, {}, [], {}

    def read(self, path):
        path = Path(path).resolve()
        require(path.is_relative_to(WORK), "artifact escapes this packet")
        if path not in self.cache:
            self.cache[path] = path.read_bytes()
            self.files[path.relative_to(WORK).as_posix()] = digest(self.cache[path])
        return self.cache[path]

    def data(self, path):
        return json.loads(self.read(path))

    def bound(self, base, name, expected, size=None):
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in name,
                "unsafe bound artifact path")
        content = self.read(Path(base) / name)
        require(digest(content) == expected, "hash differs: " + name)
        require(size is None or len(content) == size, "byte count differs: " + name)
        return content

    def bindings(self, base, mapping):
        for name, expected in mapping.items():
            self.bound(base, name, expected)
        return len(mapping)

    def section(self, name, function):
        try:
            result = function()
            self.sections[name] = {"status": "passed", **result}
        except Exception as error:
            detail = f"{name}: {type(error).__name__}: {error}"
            self.findings.append(detail)
            self.sections[name] = {"status": "failed", "detail": detail}

    def qualification(self):
        qpath = CHECKS / "qualification/qualification.json"
        q = self.data(qpath)
        require(q["status"] == "qualified" and q["training_admitted"] is False, "qualification status differs")
        binding = q["source_binding"]
        for row in binding["files"]:
            self.bound(REPO, row["path"], row["sha256"])
        self.bindings(REPO / "src/arcpuzzles", binding["executor"])
        require(q["execution"]["path"] == "execution.json", "execution location differs")
        self.bound(qpath.parent, "execution.json", q["execution"]["sha256"])
        execution = self.data(qpath.parent / "execution.json")
        require(equal(q["contract"], self.data(HOME / "promotion.json")), "qualification contract differs")
        require(len(q["jobs"]) == len(execution["episodes"]) == len(execution["checks"]) == 4,
                "qualification job/episode/check counts differ")
        pairs = 0
        for job, ep, check in zip(q["jobs"], execution["episodes"], execution["checks"], strict=True):
            require(episode_key(job) == episode_key(ep) == episode_key(check), "qualification job identity differs")
            require(check["survivors"] == [job["settings"]], "finite-setting survivor differs")
            require(digest(ep["program"].encode()) == ep["program_sha256"] == q["programs"][setting_key(ep["settings"])],
                    "qualified program differs")
            all_inputs = []
            for split, count in (("train", job["demos"]), ("test", job["queries"])):
                require(len(ep[split]) == count, "qualified pair count differs")
                for pair in ep[split]:
                    grid(pair["input"]); grid(pair["output"])
                    all_inputs.append(raw(pair["input"]))
                    pairs += 1
            require(len(set(all_inputs)) == len(all_inputs), "qualified episode has duplicate inputs")
            require(check["counts"] == {"demos": job["demos"], "queries": job["queries"]}
                    and check["label_count"] == len(all_inputs), "native check counts differ")
        expected = sum(len(q["programs"]) * j["demos"] + j["queries"] for j in q["jobs"])
        require(execution["racket_evaluations"] == expected == 64, "qualification evaluation count differs")
        require(q["programs"][setting_key(q["contract"]["default"])] == binding["canonical_program_sha256"],
                "canonical default binding differs")
        self.state.update(q=q, execution=execution, qualified=execution["episodes"])
        return {"source_files": len(binding["files"]), "executor_files": len(binding["executor"]),
                "jobs": len(q["jobs"]), "retained_labels": pairs, "retained_evaluations": expected}

    def inventory(self):
        inventory = self.data(HOME / "evidence/manifest.json")
        q = self.state["q"]
        require(inventory["builder_executed_checks"] is False and inventory["training_admitted"] is False,
                "inventory execution/admission scope differs")
        for row in inventory["files"]:
            self.bound(REPO, row["path"], row["sha256"], row["bytes"])
        for left, right in (("generator_sha256", "generator_sha256"),
                            ("canonical_program_sha256", "canonical_program_sha256"),
                            ("canonical_rule_hash", "rule_hash")):
            require(inventory[left] == q["source_binding"][right], "inventory canonical/source identity differs")
        for key in ("parameters", "default", "limits"):
            require(equal(inventory[key], q["contract"][key]), "inventory contract differs")
        copies = {"audit-tests.log": "branch-audit-tests-first.log", "boundary-review.log": "boundary-review.log",
                  "canonical-rival.json": "canonical-rival-proof/report.json", "examples.json": "native-export-report.json",
                  "export-inspection.json": "native-export-inspection.json", "export-tests.log": "export-tests.log",
                  "family-tests.log": "native-family-tests.log", "sampler.json": "sampler.json",
                  "teaching-audit.json": "native-branch-teaching-audit/report.json"}
        for target, source in copies.items():
            require(self.read(HOME / "evidence/current" / target) == self.read(CHECKS / source),
                    "inventory evidence copy differs: " + target)
        return {"bound_files": len(inventory["files"]), "exact_evidence_copies": len(copies)}

    def audit(self):
        folder = CHECKS / "native-branch-teaching-audit"
        report = self.data(folder / "report.json")
        require(report["status"] == "passed" and not report["failures"], "audit reports failures")
        self.bindings(REPO, report["source_sha256"])
        self.bindings(folder, report["artifact_sha256"])
        self.bindings(folder, report["program_sha256"])
        programs = set(report["program_sha256"].values())
        inputs, evaluations = self.data(folder / "inputs.json"), self.data(folder / "evaluations.json")
        for fingerprint, value in inputs.items():
            grid(value); require(digest(raw(value)) == fingerprint, "audit input identity differs")
        matrix = {}
        for index, item in enumerate(evaluations):
            require(item["index"] == index and item["input_sha256"] in inputs
                    and item["program_sha256"] in programs, "audit evaluation reference differs")
            grid(item["output"])
            require(digest(raw(item["output"])) == item["output_sha256"], "audit output identity differs")
            key = item["program_sha256"], item["input_sha256"]
            require(key not in matrix, "audit exact cache contains duplicate execution")
            matrix[key] = item
        require(len(evaluations) == report["racket_evaluations"] == 112
                and len(inputs) == report["distinct_inputs"] and len(programs) == report["distinct_programs"],
                "audit artifact counts differ")
        episodes = self.data(folder / "episodes.json")
        normalized, certificates = [], 0
        require(len(episodes) == len(report["jobs"]) == 4, "audit job count differs")
        for row, job in zip(episodes, report["jobs"], strict=True):
            ep = row["episode"]
            program_hash = digest(ep["program_solution"].encode())
            require(row["seed"] == job["seed"] and row["settings"] == {"branch_direction": job["setting"]}
                    and program_hash == job["program_sha256"], "audit episode identity differs")
            require(len(ep["train"]) == job["demonstrations"] and len(ep["test"]) == job["queries"],
                    "audit episode counts differ")
            cert = job["demo_certificate"]
            require(job["survivors_frozen_before_queries"] is True and cert["query_accessed"] is False
                    and not cert["survivors"] and not job["failures"], "demo-only certificate scope differs")
            require(digest(raw(cert)) == job["frozen_demo_certificate_sha256"]
                    and digest(raw(ep["train"])) == cert["demonstrations_sha256"], "frozen certificate hash differs")
            require(len(cert["demo_disagreements"]) == report["named_non_equivalent_rivals_per_setting"] == 13,
                    "declared rival count differs")
            require(set(job["first_two_refute"]) == set(cert["demo_disagreements"]), "rival certificate keys differ")
            for rival, indices in cert["demo_disagreements"].items():
                require(job["first_two_refute"][rival] is True and any(i in (0, 1) for i in indices),
                        "core demos do not refute a reported rival")
                certificates += 1
            for pair in ep["train"] + ep["test"]:
                retained = matrix[(program_hash, digest(raw(pair["input"])))]
                require(equal(retained["output"], pair["output"]), "audit intended label differs from executed matrix")
            for pair, query in zip(ep["test"], job["query_checks"], strict=True):
                require(query["input_sha256"] == digest(raw(pair["input"]))
                        and query["painted_cells"] == sum(v == 3 for r in pair["output"] for v in r),
                        "audit query summary differs")
            normalized.append({"seed": row["seed"], "settings": row["settings"], "program": ep["program_solution"],
                               "train": ep["train"], "test": ep["test"]})
        self.state.update(audit_report=report, audited=normalized, audit_matrix=matrix,
                          audit_evaluations=evaluations, audit_inputs=inputs)
        return {"source_files": len(report["source_sha256"]), "artifact_files": len(report["artifact_sha256"]),
                "program_files": len(programs), "input_grids": len(inputs), "retained_evaluations": len(evaluations),
                "hash_bound_rival_certificates": certificates}

    def exports(self):
        folder = CHECKS / "native-export"
        report = self.data(CHECKS / "native-export-report.json")
        context = self.data(folder / "private/context.json")
        manifest = self.data(folder / "manifest.json")
        require(report["status"] == "passed" and manifest["complete"] is True, "export completion differs")
        for item in (report, context, manifest):
            require(item["native_acceptance"] == "owner_pending" and item["training_admitted"] is False,
                    "export acceptance scope differs")
        self.bindings(REPO, report["source_sha256"])
        require(equal(report["source_sha256"], context["source_sha256"]), "export source inventories differ")
        for name, key in (("manifest.json", "manifest_sha256"), ("private/context.json", "private_context_sha256"),
                          ("private/metadata.jsonl", "private_metadata_sha256")):
            self.bound(folder, name, report[key])
        self.bindings(folder, manifest["files"])
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
        require(actual == set(manifest["files"]) | {"manifest.json"}, "export file inventory differs")
        native = context["native_execution"]
        require(digest(raw(native)) == report["native_execution_sha256"], "native export execution hash differs")
        require(native["racket_evaluations"] == report["racket_evaluations"] == 20, "export evaluation counts differ")
        rows = [json.loads(line) for line in self.read(folder / "private/metadata.jsonl").splitlines()]
        require(len(rows) == len(native["episodes"]) == report["settings_count"] == 2, "export episode count differs")
        require([r["controller_id"] for r in rows] == sorted(manifest["controller_ids"]) == report["controller_ids"],
                "export controller mapping differs")
        turns = []
        for row in rows:
            ep, wrapper = row["episode"], row["episode"]["native_wrapper"]
            require(any(equal(wrapper, n) for n in native["episodes"]), "native wrapper differs")
            require(ep["program_solution"] == wrapper["program"]
                    and digest(wrapper["program"].encode()) == wrapper["program_sha256"], "export program differs")
            for split in ("train", "test"):
                labels = [{"input": p["input"], "output": p["output"]} for p in ep[split]]
                require(equal(labels, wrapper[split]), "export labels differ from native execution")
            require(self.read(folder / "private/controllers" / (row["controller_id"] + ".json")) == visible(wrapper),
                    "controller visible projection differs")
            require(digest(visible(wrapper)) == row["controller_id"], "controller public ID differs")
            require(len(row["turn_ids"]) == len(wrapper["test"]) == 4, "turn mapping count differs")
            for index, identifier in enumerate(row["turn_ids"]):
                expected = visible(wrapper, index)
                require(digest(expected) == identifier
                        and self.read(folder / "turns" / (identifier + ".json")) == expected,
                        "actor visible bytes or ID differ")
            turns.extend(row["turn_ids"])
        require(sorted(turns) == report["turn_ids"] == manifest["turn_ids"] and len(set(turns)) == len(turns),
                "actor mapping contains duplicates or differs")
        inspection = self.data(CHECKS / "native-export-inspection.json")
        require(inspection["status"] == "passed" and not inspection["findings"], "saved export inspection failed")
        self.bound(CHECKS, "inspect_native_export.py", inspection["checker_sha256"])
        self.bound(WORK, "check_public_exports.py", inspection["consumer_helper_sha256"])
        self.bound(REPO, "shared/runtime/reviewer_support.py", inspection["serializer_sha256"])
        self.bound(CHECKS, "native-export-report.json", inspection["example_report_sha256"])
        self.state.update(exported=native["episodes"], export_report=report, export_native=native)
        return {"source_files": len(report["source_sha256"]), "payload_files": len(manifest["files"]),
                "actor_files": len(turns), "controllers": len(rows), "retained_evaluations": 20}

    def overlaps(self):
        groups = {name: {episode_key(e): e for e in self.state[name]}
                  for name in ("qualified", "audited", "exported")}
        comparisons = []
        for left, right in (("qualified", "audited"), ("qualified", "exported"), ("audited", "exported")):
            shared = groups[left].keys() & groups[right].keys()
            count = 0
            for key in shared:
                a, b = groups[left][key], groups[right][key]
                require(a["program"] == b["program"], "overlapping job programs differ")
                for split in ("train", "test"):
                    length = min(len(a[split]), len(b[split]))
                    require(equal(a[split][:length], b[split][:length]), "overlapping count prefixes differ")
                    count += length
            comparisons.append({"left": left, "right": right, "jobs": len(shared), "pairs": count})
        return {"comparisons": comparisons, "pair_comparisons": sum(r["pairs"] for r in comparisons)}

    def sampler(self):
        report = self.data(CHECKS / "sampler.json")
        self.bindings(WORK, report["source_sha256"])
        require(report["status"] == "passed" and not report["failures"] and report["racket_evaluations"] == 0,
                "sampler result/scope differs")
        records = report["records"]
        require(report["passed"] == report["requests"] == len(records) == 96, "sampler request counts differ")
        by_key = {(r["seed"], setting_key(r["settings"]), r["demos"], r["queries"]): r for r in records}
        require(len(by_key) == len(records), "duplicate sampler request")
        all_inputs, all_queries = set(), set()
        for row in records:
            require(row["status"] == "passed" and len(row["input_sha256"]) == row["demos"] + row["queries"],
                    "sampler record count differs")
            require(row["program_sha256"] == self.state["q"]["programs"][setting_key(row["settings"])],
                    "sampler program binding differs")
            bank = by_key[row["seed"], setting_key(row["settings"]), 6, 4]["input_sha256"]
            require(row["input_sha256"] == bank[:row["demos"]] + bank[6:6 + row["queries"]],
                    "sampler count-prefix identity differs")
            other = "away_to_edge" if row["settings"]["branch_direction"] == "toward_trunk" else "toward_trunk"
            peer = by_key[row["seed"], setting_key({"branch_direction": other}), row["demos"], row["queries"]]
            require(row["input_sha256"] == peer["input_sha256"], "settings change sampled inputs")
            all_inputs.update(row["input_sha256"]); all_queries.update(row["input_sha256"][row["demos"]:])
        require(len(all_inputs) == report["distinct_inputs"] and len(all_queries) == report["distinct_query_inputs"],
                "sampler distinct-input counts differ")
        overlap = 0
        for group in ("qualified", "audited", "exported"):
            for ep in self.state[group]:
                key = (*episode_key(ep), 6, 4)
                if key not in by_key:
                    continue
                bank = by_key[key]["input_sha256"]
                expected = bank[:len(ep["train"])] + bank[6:6 + len(ep["test"])]
                actual = [digest(raw(p["input"], False)) for p in ep["train"] + ep["test"]]
                require(actual == expected, "sampler/native retained input prefixes differ")
                overlap += len(actual)
        large = {(r["seed"], r["setting"]): r for r in report["large_queries"]}
        checked_large = set()
        for ep in self.state["qualified"]:
            key = ep["seed"], ep["settings"]["branch_direction"]
            if key in large:
                pair, row = ep["test"][3], large[key]
                require(digest(raw(pair["input"], False)) == row["input_sha256"]
                        and digest(raw(pair["output"], False)) == row["output_sha256"], "sampler large-query label differs")
                require(sum(v == 3 for r in pair["output"] for v in r) == row["painted_cells"]
                        and sum(v == 2 for r in pair["input"] for v in r) == row["red_cells"], "large-query counts differ")
                checked_large.add(key)
        return {"source_files": len(report["source_sha256"]), "requests_retained": len(records),
                "retained_input_prefix_comparisons": overlap, "retained_large_label_comparisons": len(checked_large),
                "limits": "Retained Python claims and count-prefix hashes only; sampling is not rerun."}

    def causal(self):
        witness = self.data(CHECKS / "causal/witness.json")
        replay = self.data(CHECKS / "causal/replay.json")
        q = self.state["q"]
        require(equal(witness["source_binding"], q["source_binding"])
                and equal(replay["source_binding"], q["source_binding"]), "causal source binding differs")
        self.bound(CHECKS / "causal", "witness.json", replay["witness_sha256"])
        self.bound(CHECKS / "qualification", "qualification.json", replay["qualification_sha256"])
        require(replay["status"] == replay["replay"]["status"] == "reviewer_replayed"
                and replay["owner_acceptance"] == "not_performed" and replay["training_admitted"] is False,
                "causal result/admission scope differs")
        require(len(witness["cases"]) == len(replay["replay"]["cases"]) == 2, "causal case counts differ")
        counts = []
        for case, retained in zip(witness["cases"], replay["replay"]["cases"], strict=True):
            selected = case["qualified_case"]
            ep = self.state["qualified"][selected["episode_index"]]
            pair = ep[selected["split"]][selected["pair_index"]]
            require(equal(case["settings"], ep["settings"]) and case["program"] == ep["program"]
                    and equal(case["input"], pair["input"]) and equal(case["output"], pair["output"]),
                    "causal intended case differs from qualification")
            for key in ("input", "output", "counterfactual_output"):
                require(equal(case[key], retained[key]), "causal replay output differs")
            for key in ("program", "counterfactual_program"):
                require(digest(case[key].encode()) == retained[key + "_sha256"], "causal program hash differs")
            require(case["ablation"] == "wrong_intermediate", "causal ablation differs")
            changed = len(differences(case["output"], case["counterfactual_output"]))
            require(changed > 0, "causal counterfactual does not change the output")
            counts.append(changed)
        require(replay["construction"]["evaluations"] == replay["replay"]["evaluations"] == 4,
                "causal retained evaluation counts differ")
        self.state.update(causal=replay)
        return {"cases": len(counts), "changed_cells": counts, "retained_construction_evaluations": 4,
                "retained_replay_evaluations": 4, "limits": "Authored intermediate interpretation is not independently proved."}

    def canonical_rival(self):
        folder = CHECKS / "canonical-rival-proof"
        report = self.data(folder / "report.json")
        self.bindings(WORK, report["source_sha256"])
        self.bindings(folder, report["artifact_sha256"])
        require(report["status"] == "passed" and report["selection_frozen_before_counterexample"] is True
                and report["owner_acceptance"] == "not_performed" and report["training_admitted"] is False,
                "canonical rival report status/scope differs")
        originals = []
        for line in self.read(REPO / "shared/data/canonical/puzzles.jsonl").splitlines(keepends=True):
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("content_hash") == report["canonical_content_hash"]:
                originals.append((line, row))
        require(len(originals) == 1 and digest(originals[0][0]) == report["canonical_exact_line_sha256"],
                "original canonical ledger row differs")
        original = originals[0][1]
        intended, rival = self.read(folder / "intended.rkt"), self.read(folder / "rival.rkt")
        require(intended == original["program_solution"].encode()
                and digest(intended) == self.state["q"]["source_binding"]["canonical_program_sha256"],
                "canonical intended program differs")
        fitted = self.data(folder / "canonical-fit.json")
        executed = self.data(folder / "protected-execution.json")
        matrix = {(e["program_sha256"], e["input_sha256"]): e for e in executed["evaluations"]}
        require(len(matrix) == len(executed["evaluations"]) == executed["racket_evaluations"]
                == report["fresh_protected_racket_applications"] == 8, "fresh canonical evaluation counts differ")
        require(len(fitted) == len(original["train"]) == report["canonical_demo_count"] == 4,
                "canonical training-pair counts differ")
        for pair, fit in zip(original["train"], fitted, strict=True):
            require(equal(pair["input"], fit["input"]) and equal(pair["output"], fit["output"])
                    and equal(fit["output"], fit["rival_output"]), "canonical rival does not fit retained demonstrations")
            for program, label in ((intended, fit["output"]), (rival, fit["rival_output"])):
                item = matrix[digest(program), digest(raw(pair["input"]))]
                require(equal(item["output"], label) and item["output_sha256"] == digest(raw(label)),
                        "canonical protected output differs")
        screen_survivors = [r for r, indices in report["python_screen_demo_disagreements"].items() if not indices]
        require(screen_survivors == report["survivors"] == [report["chosen_rival"]] == ["first_five_only"],
                "canonical demo-only selection differs")
        reused = self.data(folder / "reused-native-evaluations.json")
        self.bound(WORK, reused["source_report"], reused["source_report_sha256"])
        for name, key in (("evaluations.json", "source_evaluations_sha256"), ("inputs.json", "source_inputs_sha256")):
            self.bound(CHECKS / "native-branch-teaching-audit", name, reused[key])
        require(reused["fresh_reference_applications"] == 0 and report["reused_protected_native_applications"] == 2,
                "reused application accounting differs")
        case = self.data(folder / "counterexample.json")
        require(digest(raw(case["input"])) == case["input_sha256"], "counterexample input identity differs")
        for name, program in (("intended", intended), ("rival", rival)):
            retained = reused["evaluations"][name]
            require(equal(retained, self.state["audit_matrix"][digest(program), case["input_sha256"]])
                    and equal(retained["output"], case[name + "_output"]), "reused protected evaluation differs")
        changed = differences(case["intended_output"], case["rival_output"])
        require(changed == case["changed_cells"] and len(changed) == case["changed_cell_count"]
                == report["counterexample_changed_cells"] == 20, "counterexample difference count differs")
        ep = next(e for e in self.state["audited"] if episode_key(e) == episode_key(case["request"]))
        pair = ep[case["split"]][case["pair_index"]]
        require(equal(pair["input"], case["input"]) and equal(pair["output"], case["intended_output"]),
                "counterexample differs from retained native episode")
        self.state.update(canonical_execution=executed, canonical_reused=reused)
        return {"source_files": len(report["source_sha256"]), "artifact_files": len(report["artifact_sha256"]),
                "canonical_demos": len(fitted), "retained_fresh_applications": 8, "retained_reused_applications": 2,
                "changed_cells": len(changed), "limits": "Checks retained selection and labels; no fresh generation or reference application."}

    def runtimes_and_receipts(self):
        identities = [self.state["execution"]["racket"], self.state["audit_report"]["racket"],
                      self.state["export_report"]["racket"], self.state["export_native"]["racket"],
                      self.state["causal"]["construction"]["racket"], self.state["causal"]["replay"]["racket"],
                      self.state["canonical_execution"]["racket"], self.state["canonical_reused"]["racket"]]
        keys = ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256",
                "boot_script_sha256", "candidate_symbol_policy_sha256")
        expected = {key: identities[0][key] for key in keys}
        require(expected["backend"] == "racket" and expected["protected"] is True, "runtime is not protected Racket")
        require(all({key: identity[key] for key in keys} == expected for identity in identities),
                "retained execution runtime identities differ")
        runtime = self.state["audit_report"]["racket"]
        for key in ("binary", "bridge", "prelude"):
            require(digest(self.read(runtime[key + "_path"])) == runtime[key + "_sha256"], "current runtime file differs")
        receipts = ["qualification", "native-branch-teaching-audit", "native-export", "native-export-inspection",
                    "sampler", "causal", "canonical-rival-proof", "manifest", "native-family-tests",
                    "branch-audit-tests-first", "export-tests"]
        for prefix in receipts:
            receipt = self.data(CHECKS / (prefix + "-command.json"))
            require(receipt["schema"] == "arcpuzzles-run-command-v1" and receipt["returncode"] == 0,
                    "retained command did not complete successfully: " + prefix)
            require(Path(receipt["payload"]["expected_cwd"]).resolve() == REPO, "retained payload cwd differs")
        return {"matching_runtime_identities": len(identities), "current_runtime_files": 3,
                "successful_wrapper_receipts": len(receipts), "runtime_identity": expected}

    def run(self):
        self.read(SELF)
        for name in ("qualification", "inventory", "audit", "exports", "overlaps", "sampler", "causal", "canonical_rival", "runtimes_and_receipts"):
            self.section(name, getattr(self, name))
        return {"schema": "arcpuzzles-branch-release-static-check-v1", "task_id": TASK,
                "status": "failed" if self.findings else "passed", "findings": self.findings,
                "checker_sha256": digest(self.read(SELF)), "files_checked": len(self.files),
                "file_sha256": dict(sorted(self.files.items())), "sections": self.sections,
                "reference_program_evaluations_performed": 0, "owner_acceptance": "not_performed",
                "training_admitted": False,
                "limits": ["Only bytes, JSON, stored grid labels, counts and hashes are checked; no project helper, generator, audit, sampler, native worker or Racket is executed.",
                           "Retained passing receipts and hashes are not new reference execution or owner acceptance.",
                           "Finite seeds/rivals and authored causal interpretations do not establish universal identifiability, algorithmic depth or measured training benefit."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists() and not options.out.is_symlink(), "choose a fresh report path")
    result = Check().run()
    with options.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "files_checked": result["files_checked"],
                      "findings": result["findings"], "reference_program_evaluations_performed": 0}, sort_keys=True))
    raise SystemExit(bool(result["findings"]))

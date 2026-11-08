"""Generator-owned authored examples and their portable question-bank feed."""
from __future__ import annotations

from collections import Counter
import html
import json
from pathlib import Path
import zipfile

from .catalog import Catalog
from .review_full_packet import canonical_json, packet_member
from .review_solve import digest, evaluate_program, instance_hash, validate_solve_payload
from .catalog import local_path


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value) + b"\n")



def _context_files(archive, folder: str, summary: dict, out: Path, *, owner: Path,
                   receipt: dict, contract: dict, canonical_cache: dict) -> dict:
    """Retain exact solve context once by content, separate from revision logs."""
    context, content_paths = {}, {}

    def keep(key, filename, raw):
        checksum = digest(raw)
        relative = content_paths.setdefault(checksum, f"contexts/{checksum}/{filename}")
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        context[key] = {"path": relative, "sha256": checksum, "bytes": len(raw)}

    for key, member, filename in (
            ("generator_source", f"{folder}/source/generator.py", "generator.py"),
            ("solve_summary", f"{folder}/summary.json", "summary.json"),
            ("finished_work_log", f"{folder}/FINISHED_NOTES.md", "FINISHED_NOTES.md"),
            ("final_work_log", f"{folder}/SOLVE_NOTES.md", "final-SOLVE_NOTES.md")):
        if member in archive.namelist():
            keep(key, filename, archive.read(member))
    if context.get("generator_source", {}).get("sha256") != summary["generator_hash"]:
        raise ValueError("Retained solve source snapshot differs")

    # A small exact reference-rule snapshot is useful after packet retirement.
    # Only use a canonical file whose full hash matches the preparation record.
    expected = summary.get("canonical_sha256")
    if expected not in canonical_cache:
        raw = None
        canonical = owner / "shared/data/canonical/puzzles.jsonl"
        if canonical.is_file():
            candidate = canonical.read_bytes()
            if digest(candidate) == expected:
                raw = candidate
        packet_path = owner / "var/review/full-packets" / receipt["packet_id"] / "request.zip"
        if raw is None and packet_path.is_file():
            with zipfile.ZipFile(packet_path) as packet:
                candidate = packet_member(packet, "repo/shared/data/canonical/puzzles.jsonl")
                if digest(candidate) == expected:
                    raw = candidate
        canonical_cache[expected] = None if raw is None else [json.loads(line) for line in raw.splitlines() if line.strip()]
    rows = canonical_cache[expected]
    rule_task = contract["generator"].get("rule_task_id", contract["task_id"])
    if rows is not None:
        rules = sorted({row["program_solution"] for row in rows
                        if row.get("task_id") == rule_task and isinstance(row.get("program_solution"), str)})
        if rules:
            keep("reference_rule", "reference_rule.json", canonical_json({
                "task_id": rule_task, "canonical_sha256": expected, "program_solutions": rules}))
    return context

def _retained_examples(owner: Path, out: Path) -> tuple[dict, dict, list]:
    """Load useful examples without reopening their original review transports."""
    attempts, questions, curriculum = {}, {}, []
    for path in sorted((owner / "generators").glob("*/evidence/reviewer-solves/manifest.json")):
        record = json.loads(path.read_text())
        task_id = path.parents[2].name
        if record.get("schema") != "arcpuzzles-task-reviewer-solves-v1" or record.get("generator_id") != task_id:
            raise ValueError(f"Invalid task example manifest: {path}")
        for question in record["questions"]:
            if question["generator_id"] != task_id or instance_hash(question["public"]) != question["instance_hash"]:
                raise ValueError(f"Question identity differs: {path}")
            questions[question["question_id"]] = question
        for stored in record["attempts"]:
            row = {**stored, "files": {}}
            if row["generator_id"] != task_id or row["question_id"] not in questions or row["training_admitted"]:
                raise ValueError(f"Attempt identity or admission differs: {path}")
            for name, item in stored["files"].items():
                if not item["path"].startswith(f"generators/{task_id}/evidence/reviewer-solves/"):
                    raise ValueError("Authored example asset outside its generator")
                source = local_path(owner, item["path"])
                raw = source.read_bytes()
                if digest(raw) != item["sha256"] or len(raw) != item["bytes"]:
                    raise ValueError(f"Authored example asset changed: {source}")
                relative = (f"contexts/{item['sha256']}/{source.name}" if "/contexts/" in item["path"]
                            else f"records/{row['attempt_id']}/{source.name}")
                target = out / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                row["files"][name] = {**item, "path": relative}
            if row["files"]["program"]["sha256"] != row["program_hash"]:
                raise ValueError("Authored program hash differs")
            if ("generator_source" in row["files"]
                    and row["files"]["generator_source"]["sha256"] != row["generator_hash"]):
                raise ValueError("Authored generator snapshot hash differs")
            if "solve_summary" in row["files"]:
                summary = json.loads((out / row["files"]["solve_summary"]["path"]).read_text())
                if any(summary.get(k) != row.get(k) for k in ("generator_hash", "instance_hash",
                           "earlier_rule_exposure", "reference_consulted_during_solve")):
                    raise ValueError("Authored solve context or exposure differs")
                finished = row["files"].get("finished_work_log")
                if finished and summary.get("final_notes_sha256") != finished["sha256"]:
                    raise ValueError("Authored final notes binding differs")
            attempts[row["attempt_id"]] = row
        curriculum.extend(record.get("curriculum", []))
    return attempts, questions, curriculum


def retain_solve_examples(owner: Path, feed: Path) -> dict:
    from .review import _lock
    with _lock(owner.resolve() / 'REVIEW'):
        return _retain_solve_examples(owner, feed)


def _retain_solve_examples(owner: Path, feed: Path) -> dict:
    """Extract unique authored data; preserve labels/exposure, never admit training."""
    owner, feed = owner.resolve(), feed.resolve()
    manifest = json.loads((feed / "manifest.json").read_text())
    if manifest.get("schema") != "arc-reviewer-solve-feed-v1" or manifest["counts"]["errors"]:
        raise ValueError("Example extraction needs an error-free feed")
    for name, expected in manifest["files"].items():
        if digest(local_path(feed, name).read_bytes()) != expected:
            raise ValueError(f"Feed member changed: {name}")
    questions = {r["question_id"]: r for r in map(json.loads, (feed / "questions.jsonl").read_text().splitlines())}
    groups: dict[str, list] = {}
    for row in map(json.loads, (feed / "attempts.jsonl").read_text().splitlines()):
        task = row["generator_id"]
        home = local_path(owner, f"generators/{task}/evidence/reviewer-solves")
        if not (owner / "generators" / task / "generator.py").is_file():
            raise ValueError(f"Missing generator for authored example: {task}")
        copied = {**row, "files": {}, "source_returns": [
            {k: v for k, v in origin.items() if k != "archive_path"} for origin in row["source_returns"]]}
        # The verified score is already bound to these program/instance bytes.
        # A retired operational replay receipt is not a runtime dependency.
        if copied.pop("verification_receipt", None):
            copied["verification_basis"] = "independent maintainer replay of bound program and instance"
        for name, item in row["files"].items():
            raw = local_path(feed, item["path"]).read_bytes()
            target = (home / "contexts" / item["sha256"] / Path(item["path"]).name
                      if item["path"].startswith("contexts/") else
                      home / "records" / row["attempt_id"] / Path(item["path"]).name)
            if target.exists() and target.read_bytes() != raw:
                raise ValueError(f"Conflicting retained example: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            copied["files"][name] = {**item, "path": target.relative_to(owner).as_posix()}
        groups.setdefault(task, []).append(copied)
    annotations: dict[str, list] = {}
    for row in map(json.loads, (feed / "curriculum.jsonl").read_text().splitlines()):
        # Empty default forms are transport noise, not useful curriculum evidence.
        if row.get("notes") or any(a.get("status") != "unknown" or a.get("witness") or a.get("rival")
                                   for a in row.get("axes", {}).values()):
            annotations.setdefault(row["task_id"], []).append(row)
    for task in sorted(set(groups) | set(annotations)):
        rows = groups.get(task, [])
        question_ids = {r["question_id"] for r in rows}
        _write(owner / f"generators/{task}/evidence/reviewer-solves/manifest.json", {
            "schema": "arcpuzzles-task-reviewer-solves-v1", "generator_id": task,
            "questions": [questions[k] for k in sorted(question_ids)],
            "attempts": sorted(rows, key=lambda r: r["attempt_id"]),
            "curriculum": annotations.get(task, []), "training_admitted": False})
    return {"generators": len(set(groups) | set(annotations)), "questions": len(questions), "attempts": sum(map(len, groups.values()))}


def verify_return_solve(review_root: Path, assignment_id: str, version: int, *, timeout: float = 30) -> dict:
    from .review import _lock
    with _lock(review_root):
        return _verify_return_solve(review_root, assignment_id, version, timeout=timeout)


def _verify_return_solve(review_root: Path, assignment_id: str, version: int, *, timeout: float = 30) -> dict:
    """Execute inspected reviewer code against regenerated private labels in a checked candidate."""
    from .review_full_candidate import _packet, _receipt
    root = review_root.resolve()
    returned = _receipt(root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Solve replay needs a statically accepted return")
    check_path = root.parent / "var/review/full-checks" / assignment_id / f"{version:04d}/result.json"
    if not check_path.is_file():
        raise ValueError("Inspect the code and run review check before solve-check")
    checked = json.loads(check_path.read_text())
    candidate = Path(checked["candidate_path"]) / "repo"
    if checked["status"] not in {"passed", "no_changes", "failed_checks"}:
        raise ValueError("Solve replay needs an applied candidate, without patch rejection")
    destination = root.parent / "var/review/solve-checks" / assignment_id / f"{version:04d}/result.json"
    if destination.is_file():
        stored = json.loads(destination.read_text())
        if stored["return_sha256"] != returned["zip_sha256"]:
            raise ValueError("Solve replay receipt refers to another return")
        return stored
    report = {"schema": "arcpuzzles-reviewer-solve-replay-v1", "assignment_id": assignment_id,
              "version": version, "return_sha256": returned["zip_sha256"], "status": "blocked",
              "attempts": [], "training_admitted": False}
    with zipfile.ZipFile(returned["archive_path"]) as archive:
        if digest(Path(returned["archive_path"]).read_bytes()) != returned["zip_sha256"]:
            raise ValueError("Retained return bytes changed")
        contract = json.loads(archive.read("ASSIGNMENT.json"))
        summary = validate_solve_payload(archive.read, set(archive.namelist()), contract, complete=False)
        if summary is None or summary["status"] == "blocked":
            report["reason"] = "No generated solve episode to replay"
        else:
            try:
                report["attempts"] = _replay(archive, candidate, contract, summary, "solve", timeout)
                report["status"] = "verified"
            except Exception as exc:
                report["reason"] = type(exc).__name__ + ": " + str(exc)[:2000]
        if "BLIND_ASSIGNMENT.json" in archive.namelist():
            # The blind task is untouched by the return's patch; replay it independently.
            blind = json.loads(archive.read("BLIND_ASSIGNMENT.json"))
            blind_summary = validate_solve_payload(archive.read, set(archive.namelist()), blind,
                                                   complete=False, kind="blind")
            entry = {"task_id": blind["task_id"], "status": "blocked", "attempts": []}
            if blind_summary is None or blind_summary["status"] == "blocked":
                entry["reason"] = "No generated blind episode to replay"
            else:
                try:
                    with zipfile.ZipFile(_packet(root, returned["packet_id"])) as packet:
                        original_manifest = packet_member(packet, "PACKET-MANIFEST.json")
                        if digest(original_manifest) != returned["packet_id"]:
                            raise ValueError("Blind replay packet identity differs")
                        baseline_canonical = packet_member(packet, "repo/shared/data/canonical/puzzles.jsonl")
                    entry["attempts"] = _replay(archive, candidate, blind, blind_summary, "solve-blind", timeout,
                        baseline_canonical=baseline_canonical, repaired_task=contract["task_id"])
                    entry["canonical_source_policy"] = "packet_baseline_with_only_main_task_rows_repaired"
                    entry["status"] = "verified"
                except Exception as exc:
                    entry["reason"] = type(exc).__name__ + ": " + str(exc)[:2000]
            report["blind"] = entry
    _write(destination, report)
    return report


def _replay(archive, candidate: Path, contract: dict, summary: dict, folder: str, timeout: float, *,
            baseline_canonical: bytes | None = None, repaired_task: str | None = None) -> list[dict]:
    generator = candidate / contract["generator"]["generator"]
    canonical = candidate / "shared/data/canonical/puzzles.jsonl"
    if (generator.is_symlink() or digest(generator.read_bytes()) != summary["generator_hash"]
            or canonical.is_symlink()):
        raise ValueError("Replayed candidate source differs from the solve episode")
    canonical_bytes = canonical.read_bytes()
    if baseline_canonical is not None:
        from .review_full_return import _canonical_only_task
        if digest(baseline_canonical) != summary["canonical_sha256"] or repaired_task == contract["task_id"]:
            raise ValueError("Blind replay baseline differs from the solve episode")
        # Keep the original whole-file evidence and prove every blind-task row
        # unchanged; the checked main repair can legitimately alter other rows.
        _canonical_only_task(baseline_canonical, canonical_bytes, repaired_task)
    elif digest(canonical_bytes) != summary["canonical_sha256"]:
        raise ValueError("Replayed candidate source differs from the solve episode")
    episode = Catalog(candidate).generate(contract["task_id"], count=1,
        seed=summary["seed"], allow_unapproved=True, **summary["config"])[0]
    public = {"train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
              "test": [{"input": p["input"]} for p in episode["test"]]}
    labels = {"test_outputs": [p["output"] for p in episode["test"]]}
    if (instance_hash(public) != summary["instance_hash"]
            or digest(canonical_json(labels)) != summary["private_labels_sha256"]):
        raise ValueError("Regenerated episode or labels differ from the reviewer receipt")
    attempts = []
    for number in range(1, summary["attempt_count"] + 1):
        source = archive.read(f"{folder}/attempts/{number:04d}/solution.py")
        score, _ = evaluate_program(source, public, labels["test_outputs"], timeout=timeout)
        attempts.append({"revision": number, "program_hash": digest(source),
                         "generator_hash": summary["generator_hash"], "instance_hash": summary["instance_hash"],
                         "label": score["reported_label"] if score["execution_status"] == "completed" else "unknown",
                         "score": score})
    return attempts


def build_solve_tracker(review_root: Path, out: Path) -> dict:
    from .review import _lock
    with _lock(review_root):
        return _build_solve_tracker(review_root, out)


def _build_solve_tracker(review_root: Path, out: Path) -> dict:
    root, out = review_root.resolve(), out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    from .review_curriculum import retained_curriculum
    attempts, questions, curriculum = _retained_examples(root.parent, out)
    blocked, errors = [], []
    canonical_cache = {}
    for path in sorted((root / "assignments").glob("*/returns/return-*.json")):
        receipt = json.loads(path.read_text())
        if (receipt.get("schema") != "arcpuzzles-full-return-receipt-v2"
                or receipt.get("validation_status") != "accepted" or receipt.get("retention_status") == "extracted"):
            continue
        try:
            archive_path = Path(receipt["archive_path"])
            if digest(archive_path.read_bytes()) != receipt["zip_sha256"]:
                raise ValueError("Retained return SHA-256 differs")
            annotation = retained_curriculum(receipt, root.parent)
            if annotation is not None:
                curriculum.append(annotation)
            with zipfile.ZipFile(archive_path) as archive:
                for kind, folder, contract_name in (("post_repair", "solve", "ASSIGNMENT.json"),
                                                    ("blind", "solve-blind", "BLIND_ASSIGNMENT.json")):
                    if contract_name not in archive.namelist():
                        continue
                    contract = json.loads(archive.read(contract_name))
                    summary = validate_solve_payload(archive.read, set(archive.namelist()), contract, complete=False, kind=kind)
                    if summary is None:
                        continue
                    source_return = {"assignment_id": receipt["assignment_id"], "version": receipt["version"],
                        "return_sha256": receipt["zip_sha256"], "packet_id": receipt["packet_id"],
                        "archive_path": str(archive_path), "solve_kind": "blind_before_repair" if kind == "blind" else "post_repair"}
                    if summary["status"] == "blocked":
                        blocked.append({**source_return, "task_id": contract["task_id"],
                                        "reason": summary["stopping_reason"]})
                        continue
                    key = digest(canonical_json([summary["generator_hash"], summary["instance_hash"]]))
                    question = {"schema": "arc-reviewer-question-v1", "question_id": key,
                        "generator_hash": summary["generator_hash"], "instance_hash": summary["instance_hash"],
                        "generator_id": contract["task_id"], "source_split": summary["generation_provenance"].get("split"),
                        "provenance": summary["generation_provenance"],
                        "private_labels_sha256": summary["private_labels_sha256"],
                        "public": json.loads(archive.read(folder + "/challenge.json"))}
                    if key in questions and questions[key]["private_labels_sha256"] != question["private_labels_sha256"]:
                        raise ValueError("Same public question has conflicting private labels")
                    questions[key] = question
                    context = _context_files(archive, folder, summary, out, owner=root.parent,
                                             receipt=receipt, contract=contract, canonical_cache=canonical_cache)
                    replay_path = root.parent / "var/review/solve-checks" / receipt["assignment_id"] / (
                        f"{receipt['version']:04d}/result.json")
                    replay = json.loads(replay_path.read_text()) if replay_path.is_file() else {}
                    kind_replay = replay.get("blind", {}) if kind == "blind" else replay
                    verified = {r["revision"]: r for r in kind_replay.get("attempts", [])} if (
                        kind_replay.get("status") == "verified" and replay.get("return_sha256") == receipt["zip_sha256"]) else {}
                    for revision in range(1, summary["attempt_count"] + 1):
                        home = f"{folder}/attempts/{revision:04d}"
                        reported = json.loads(archive.read(home + "/report.json"))
                        attempt_id = digest(canonical_json([receipt["assignment_id"], key, revision, reported["program_hash"]]
                            + (["blind"] if kind == "blind" else [])))
                        if attempt_id in attempts:
                            origins = attempts[attempt_id]["source_returns"]
                            if not any(all(origin.get(k) == source_return[k] for k in
                                           ("assignment_id", "version", "return_sha256")) for origin in origins):
                                origins.append(source_return)
                            # A later recheck of the same retained revision can add evidence.
                            row = attempts[attempt_id]
                        else:
                            files = {}
                            for name, member in (("program", home + "/solution.py"), ("work_log", home + "/SOLVE_NOTES.md"),
                                                 ("report", home + "/report.json"), ("execution", home + "/execution.json")):
                                if member not in archive.namelist():
                                    continue
                                raw = archive.read(member)
                                relative = f"records/{attempt_id}/{Path(member).name}"
                                target = out / relative
                                target.parent.mkdir(parents=True, exist_ok=True)
                                target.write_bytes(raw)
                                files[name] = {"path": relative, "sha256": digest(raw), "bytes": len(raw)}
                            row = {"schema": "arc-reviewer-attempt-v1", "attempt_id": attempt_id,
                                "question_id": key, "generator_hash": summary["generator_hash"],
                                "instance_hash": summary["instance_hash"], "generator_id": contract["task_id"],
                                "program_hash": reported["program_hash"], "revision": revision,
                                "source_kind": "reviewer_authored", "label": "unknown",
                                "solve_kind": "blind_before_repair" if kind == "blind" else "post_repair",
                                "attempt_intent": reported.get("attempt_intent", "unknown"),
                                "reported_label": reported["reported_label"], "reported_score": reported,
                                "reference_consulted_during_solve": summary["reference_consulted_during_solve"],
                                "earlier_rule_exposure": summary["earlier_rule_exposure"],
                                "feedback_policy": summary.get("feedback_policy", "legacy_private_feedback"),
                                "note": reported["note"], "files": files, "source_returns": [source_return],
                                "training_admitted": False}
                            attempts[attempt_id] = row
                        # Also fill context for an already-retained attempt when
                        # repairing an earlier incomplete extraction.
                        row["files"].update(context)
                        scored = verified.get(revision)
                        if scored and all(scored.get(k) == row[k] for k in ("program_hash", "generator_hash", "instance_hash")):
                            row.update({"label": scored["label"], "verified_score": scored["score"],
                                        "verification_receipt": str(replay_path)})
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
            errors.append({"receipt": str(path), "reason": str(exc)})
    curriculum = list({digest(canonical_json(row)): row for row in curriculum}.values())
    rows = sorted(attempts.values(), key=lambda r: (r["source_returns"][0]["assignment_id"], r.get("solve_kind", "post_repair"), r["revision"]))
    question_rows = sorted(questions.values(), key=lambda q: q["question_id"])
    (out / "attempts.jsonl").write_bytes(b"".join(canonical_json(row) + b"\n" for row in rows))
    (out / "questions.jsonl").write_bytes(b"".join(canonical_json(row) + b"\n" for row in question_rows))
    (out / "curriculum.jsonl").write_bytes(b"".join(canonical_json(row) + b"\n" for row in curriculum))
    labels = Counter(row["label"] for row in rows)
    counts = {"questions": len(questions), "attempts": len(rows), "verified_good": labels["good"],
              "verified_bad": labels["bad"], "unverified": labels["unknown"], "blocked": len(blocked), "errors": len(errors)}
    _write(out / "summary.json", {"schema": "arcpuzzles-reviewer-solve-tracker-v1", "counts": counts,
                                  "blocked": blocked, "errors": errors})
    files = {name: digest((out / name).read_bytes()) for name in ("attempts.jsonl", "questions.jsonl", "summary.json", "curriculum.jsonl")}
    for row in rows:
        files.update({item["path"]: item["sha256"] for item in row["files"].values()})
    manifest = {"schema": "arc-reviewer-solve-feed-v1", "files": files, "counts": counts,
                "training_admitted": False, "origin": "ARCpuzzles review returns"}
    _write(out / "manifest.json", manifest)
    export = out / "export/reviewer-solves.zip"
    export.parent.mkdir(exist_ok=True)
    temporary = export.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted({*files, "manifest.json"}):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / name).read_bytes())
    temporary.replace(export)
    cards = []
    for row in rows:
        program = (out / row["files"]["program"]["path"]).read_text()
        notes = (out / row["files"]["work_log"]["path"]).read_text()
        label = row["label"]
        identity = f"{row['generator_id']} · {row.get('solve_kind', 'post_repair')} · revision {row['revision']} · {label} (reviewer reported {row['reported_label']})"
        cards.append("<article data-label='" + html.escape(label) + "'><h2>" + html.escape(identity) + "</h2>"
            "<p>Intent: " + html.escape(row["attempt_intent"]) + "</p><p>" + html.escape(row["note"]) + "</p><p>Generator hash: <code>" + row["generator_hash"] + "</code><br>"
            "Instance hash: <code>" + row["instance_hash"] + "</code></p><p>Reference consulted during solve: "
            + html.escape(str(row["reference_consulted_during_solve"])) + "; earlier exposure: "
            + html.escape(row["earlier_rule_exposure"]) + "</p><details><summary>Public episode</summary><pre>"
            + html.escape(json.dumps(questions[row["question_id"]]["public"], indent=2))
            + "</pre></details><details><summary>Python program</summary><pre>" + html.escape(program)
            + "</pre></details><details><summary>Work log</summary><pre>" + html.escape(notes) + "</pre></details></article>")
    page = """<!doctype html><html lang='en'><meta charset='utf-8'><title>Reviewer solves</title>
<style>body{font:16px system-ui;max-width:1100px;margin:auto;padding:2rem}article{border:1px solid #ccc;padding:1rem;margin:1rem 0}pre{white-space:pre-wrap}code{overflow-wrap:anywhere}input,select{padding:.5rem}</style>
<h1>Reviewer solves</h1><p>Reviewer claims are retained immediately. Good/bad labels require independent maintainer replay. All records remain outside training admission.</p>
<input id='search' placeholder='Filter generator, hash, notes'><select id='label'><option value=''>All</option><option>good</option><option>bad</option><option>unknown</option></select>
""" + "<p>" + html.escape(json.dumps(counts)) + "</p>" + "".join(cards)
    if blocked or errors:
        page += "<h2>Blocked or unresolved</h2><pre>" + html.escape(json.dumps(blocked + errors, indent=2)) + "</pre>"
    page += """<script>function filter(){for(const el of document.querySelectorAll('article'))el.hidden=(label.value&&el.dataset.label!==label.value)||!el.textContent.toLowerCase().includes(search.value.toLowerCase());}document.querySelector('#search').oninput=filter;document.querySelector('#label').onchange=filter;</script></html>"""
    (out / "index.html").write_text(page)
    return {"html": str(out / "index.html"), "attempts": str(out / "attempts.jsonl"),
            "questions": str(out / "questions.jsonl"), "export": str(export), "counts": counts}

"""Replay a task delta against newly extracted, hash-verified packet sources.

By default this replay extracts every original non-generator file and the
selected generator. --runtime-closure instead selects the official runtime
mapping dependencies, public API, catalog and launchers, omitting unrelated sources. It never edits or
deletes the working review, source ZIP, or an existing destination. Run the
fresh checkout's focused tests afterward using its own Python environment.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or ".." in path.parts
            or "\\" in name or "\x00" in name or str(path) != name.rstrip("/")):
        raise ValueError(f"Unsafe archive path: {name!r}")
    return path


def no_symlink_ancestors(path):
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError(f"Symlink destination ancestor: {parent}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--delta-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compare-work", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--runtime-closure", action="store_true", help="Extract official selected runtime mappings, public API, catalog, launchers and target; omit unrelated sources.")
    parser.add_argument("--receipt-dir", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.task_id):
        parser.error("Unsafe task ID")
    for path in (args.out, args.receipt_dir):
        no_symlink_ancestors(path.absolute())
        if path.exists():
            parser.error(f"Destination must be new: {path}")
    source, delta = args.source_zip.resolve(), args.delta_zip.resolve()
    owner = args.compare_work.resolve()
    out, receipts = args.out.absolute(), args.receipt_dir.absolute()
    if owner == out or owner in out.parents or out in owner.parents:
        parser.error("Fresh destination must be separate from working review")

    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        seen = set()
        for info in infos:
            safe_name(info.filename)
            if info.filename in seen:
                raise ValueError(f"Duplicate archive member: {info.filename}")
            seen.add(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"Archive symlink: {info.filename}")
        manifest = json.loads(archive.read("WORK/PACKET-MANIFEST.json"))
        expected = {"WORK/" + key: value for key, value in manifest["files"].items()}
        expected.update(manifest["layout"]["entry_files"])
        if args.runtime_closure:
            mapping = json.loads(archive.read("WORK/repo/catalog/runtime_files.json"))
            authorities = json.loads(archive.read("WORK/repo/catalog/authority_files.json"))
            identity = manifest["generators"][args.task_id].get("rule_task_id", args.task_id)
            wanted = {args.task_id, identity}
            required = set()
            for item in mapping:
                relative, target = item["path"], item["target"]
                if relative.startswith("generators/") and PurePosixPath(relative).parts[1] not in wanted:
                    continue
                if target.startswith("data/base/solutions/") and authorities.get(target) not in wanted:
                    continue
                required.add("WORK/repo/" + relative)
            missing = required - seen
            if missing:
                raise ValueError(f"Missing original declared runtime sources: {sorted(missing)}")
            selected = [info for info in infos if not info.is_dir() and (
                info.filename in required
                or info.filename in ("review.py", "START-HERE.md", "WORK/repo/AGENTS.md", "WORK/repo/README.md", "WORK/repo/pyproject.toml")
                or PurePosixPath(info.filename).parent == PurePosixPath("WORK")
                or info.filename.startswith(("WORK/repo/src/arcpuzzles/", "WORK/repo/catalog/", "WORK/vendor/"))
                or info.filename.startswith("WORK/repo/generators/" + args.task_id + "/"))]
        else:
            selected = [info for info in infos if not info.is_dir() and (
                not info.filename.startswith("WORK/repo/generators/")
                or info.filename.startswith("WORK/repo/generators/" + args.task_id + "/"))]
        if not any(info.filename == f"WORK/repo/generators/{args.task_id}/generator.py"
                   for info in selected):
            raise ValueError("Selected generator absent from original ZIP")
        with zipfile.ZipFile(delta) as returned:
            patch = returned.read("patches/source.patch")
        changed = re.findall(rb"^diff --git a/(repo/[^\s]+) b/\1$", patch, re.M)
        paths = [raw.decode("utf-8") for raw in changed]
        if not paths or len(paths) != len(set(paths)):
            raise ValueError("Missing or repeated patch paths")
        for path in paths:
            safe_name(path)
            if not path.startswith("repo/generators/" + args.task_id + "/"):
                raise ValueError("This bounded task replay requires a task-local patch")
            if not (owner / path).is_file() or (owner / path).is_symlink():
                raise ValueError(f"Missing working-review comparison file: {path}")

        receipts.mkdir(parents=True)
        out.mkdir(parents=True)
        records = []
        receipt = {
            "schema": "arcpuzzles-fresh-task-replay-v1", "status": "running",
            "source_zip_sha256": file_sha(source), "delta_zip_sha256": file_sha(delta),
            "patch_sha256": sha(patch), "task_id": args.task_id,
            "source_zip": str(source), "delta_zip": str(delta), "fresh_root": str(out),
            "scope": ("Original selected-task runtime mappings, public API, catalog, launchers and task sources; unrelated sources omitted. Working-review bytes are read only for hash comparison." if args.runtime_closure else "All original non-generator files and selected generator; unrelated generator homes omitted."),
            "extraction_mode": "declared_runtime_dependency_closure" if args.runtime_closure else "all_shared_and_selected_task",
            "original_files": sum(not info.is_dir() for info in infos),
            "extracted_files": len(selected), "commands": [], "changed_files": []}
        def save():
            (receipts / "replay.json").write_text(json.dumps(receipt, indent=2) + "\n")
        save()
        try:
            for info in selected:
                raw = archive.read(info)
                digest = sha(raw)
                wanted = expected.get(info.filename)
                if wanted is not None and wanted != digest:
                    raise ValueError(f"Original manifest mismatch: {info.filename}")
                target = out / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                records.append({"path": info.filename, "bytes": len(raw), "sha256": digest,
                                "packet_manifest_bound": wanted is not None})
            raw_inventory = (json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with (receipts / "extraction-manifest.json.gz").open("xb") as stream:
                with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as compressed:
                    compressed.write(raw_inventory)
            receipt["extraction_manifest_raw_sha256"] = sha(raw_inventory)
            receipt["extraction_manifest_gzip_sha256"] = file_sha(receipts / "extraction-manifest.json.gz")
            patch_path = receipts / "source.patch"
            patch_path.write_bytes(patch)
            work = out / "WORK"
            def run(argv):
                completed = subprocess.run(argv, cwd=work, text=True, capture_output=True, timeout=120)
                receipt["commands"].append({"argv": argv, "cwd": str(work),
                                            "exit_code": completed.returncode,
                                            "stdout": completed.stdout, "stderr": completed.stderr})
                save()
                if completed.returncode:
                    raise RuntimeError(f"Command failed: {argv}")
                return completed.stdout.strip()
            run(["git", "init", "-q"])
            top = run(["git", "rev-parse", "--show-toplevel"])
            if Path(top).resolve() != work.resolve():
                raise ValueError("Git top-level differs from exact fresh WORK directory")
            # Git parses the whole patch, including sections our simple header
            # reader might not recognize. Require that its complete inventory
            # is exactly the reviewed task-local add/edit inventory before any
            # patch application. Rename records use a different NUL layout and
            # are rejected by this deliberately narrow replay tool.
            inventory = run(["git", "apply", "--numstat", "-z", str(patch_path)])
            git_paths = []
            for record in inventory.split("\0"):
                if not record:
                    continue
                fields = record.split("\t", 2)
                if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
                    raise ValueError("Unsupported non-text or renamed patch entry")
                path = fields[2]
                safe_name(path)
                if not path.startswith("repo/generators/" + args.task_id + "/"):
                    raise ValueError(f"Git reports an out-of-scope patch path: {path}")
                git_paths.append(path)
            if sorted(git_paths) != sorted(paths):
                raise ValueError("Complete Git patch inventory differs from checked headers")
            receipt["git_parsed_patch_paths"] = git_paths
            run(["git", "apply", "--check", str(patch_path)])
            run(["git", "apply", str(patch_path)])
            for path in paths:
                applied = work / path
                digest = file_sha(applied)
                wanted = file_sha(owner / path)
                if digest != wanted:
                    raise ValueError(f"Applied path differs from reviewed final source: {path}")
                receipt["changed_files"].append({"path": path, "sha256": digest,
                                                  "bytes": applied.stat().st_size, "matches_review": True})
            receipt["generator_sha256"] = file_sha(work / f"repo/generators/{args.task_id}/generator.py")
            receipt["status"] = "patch_replay_passed_tests_pending"
            save()
            print(json.dumps({key: receipt[key] for key in
                              ("status", "extracted_files", "generator_sha256", "patch_sha256")}))
        except BaseException as exc:
            receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            save()
            raise


if __name__ == "__main__":
    main()

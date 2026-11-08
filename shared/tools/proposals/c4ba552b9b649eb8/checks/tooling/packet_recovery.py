#!/usr/bin/env python3
"""Explicit, ZIP-backed recovery for source-bound ARCpuzzles WORK packets.

No command is run on import. hydrate-main commits one seed before extracting any
selected source; --plan-only commits that same seed but does not draw. The package
adapter changes one checked expression in a private copy of the issued packager;
it never changes the issued module, entry files, manifest, or task sources.
The optional replay adapter changes only source-path resolve to absolute for an
explicit /proc/self/fd/N source transport; every stock replay check is retained.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import zipfile

DEFAULT_ZIP = Path("/workspace/scratch/4bbe6d6743f0/upload/SEND-THIS-ARCpuzzles-review(20261023-054016).zip")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
BLOCK = 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or "\0" in name
            or name.startswith("/") or any(x in {"", ".", ".."} for x in name.split("/"))
            or ":" in name.split("/")[0]):
        raise ValueError(f"Unsafe relative path: {name!r}")
    return name


def no_symlinks(path):
    path = Path(path).absolute()
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink():
            raise ValueError(f"Symlink path refused: {parent}")
    return path


def safe_target(root, name):
    return no_symlinks(Path(root).absolute() / safe_name(name))


def regular_bytes(path):
    path = no_symlinks(path)
    if not path.is_file():
        raise ValueError(f"Expected regular file: {path}")
    return path.read_bytes()


def sync_dir(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path, raw):
    path = no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".portable-stage-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        no_symlinks(path)
        os.replace(temporary, path)
        sync_dir(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def seed_lock(work):
    review = safe_target(work, ".review")
    review.mkdir(parents=True, exist_ok=True)
    lock = safe_target(review, "portable-seed.lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        os.close(descriptor)


def commit_seed(work, packet_id):
    """Return one durable seed; adopt completed/pending draws, never redraw."""
    if not HEX64.fullmatch(packet_id):
        raise ValueError("Invalid packet ID")
    work = no_symlinks(work)
    with seed_lock(work):
        seed_path = safe_target(work, ".review/portable-seed.json")
        records = []
        for name, expected_schema in (
                (".review/portable-seed.json", "arcpuzzles-portable-seed-v1"),
                (".review/main-draw-seed.json", "arcpuzzles-main-draw-seed-v1"),
                ("ASSIGNMENT.json", None),
                (".review/pending-main-draw.json", "arcpuzzles-pending-main-draw-v1")):
            path = safe_target(work, name)
            if path.exists():
                record = json.loads(regular_bytes(path))
                if not isinstance(record, dict):
                    raise ValueError(f"Invalid saved draw object: {name}")
                if expected_schema is not None and record.get("schema") != expected_schema:
                    raise ValueError(f"Invalid saved draw schema: {name}")
                if name.endswith("pending-main-draw.json"):
                    record = record.get("contract", {})
                if (not isinstance(record, dict) or record.get("packet_id") != packet_id
                        or not isinstance(record.get("seed"), str)
                        or not HEX64.fullmatch(record["seed"])):
                    raise ValueError(f"Invalid or foreign saved draw: {name}")
                records.append(record["seed"])
        if len(set(records)) > 1:
            raise ValueError("Saved assignment and recovery seeds conflict")
        seed = bytes.fromhex(records[0]) if records else os.urandom(32)
        if not seed_path.exists():
            atomic_write(seed_path, canonical({"schema": "arcpuzzles-portable-seed-v1",
                "packet_id": packet_id, "seed": seed.hex()}))
        return seed


class Packet:
    """Read the original ZIP, rejecting ambiguous paths before any extraction."""

    def __init__(self, path):
        self.path = Path(path).absolute()
        self.zip = zipfile.ZipFile(self.path)
        try:
            self.infos = {}
            for info in self.zip.infolist():
                safe_name(info.filename[:-1] if info.is_dir() else info.filename)
                if info.filename in self.infos:
                    raise ValueError(f"Duplicate ZIP member: {info.filename}")
                if stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1:
                    raise ValueError(f"Symlink/encrypted ZIP member refused: {info.filename}")
                self.infos[info.filename] = info
            self.raw_manifest = self.zip.read("WORK/PACKET-MANIFEST.json")
            self.manifest = json.loads(self.raw_manifest)
            if (self.manifest.get("schema") != "arcpuzzles-full-packet-v2"
                    or canonical(self.manifest) != self.raw_manifest
                    or self.manifest.get("layout", {}).get("workspace") != "WORK"):
                raise ValueError("Not a canonical supported WORK packet manifest")
            self.files = self.manifest["files"]
            self.entries = self.manifest["layout"]["entry_files"]
            if set(self.entries) != {"review.py", "START-HERE.md"}:
                raise ValueError("Unexpected outer entry inventory")
            for inventory, prefix in ((self.files, "WORK/"), (self.entries, "")):
                for name, digest in inventory.items():
                    safe_name(name)
                    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
                        raise ValueError(f"Invalid SHA-256: {name}")
                    info = self.infos.get(prefix + name)
                    if info is None or info.is_dir():
                        raise ValueError(f"Missing regular ZIP member: {prefix + name}")
            self.packet_id = sha(self.raw_manifest)
        except BaseException:
            self.zip.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.zip.close()

    def _stream_verified(self, archive_name, expected, output=None):
        digest = hashlib.sha256()
        size = 0
        with self.zip.open(archive_name) as stream:
            for block in iter(lambda: stream.read(BLOCK), b""):
                digest.update(block)
                size += len(block)
                if output is not None:
                    output.write(block)
        if digest.hexdigest() != expected:
            raise ValueError(f"ZIP SHA-256 mismatch: {archive_name}")
        return size

    def verify_member(self, name):
        safe_name(name)
        if name not in self.files:
            raise ValueError(f"Not in issued manifest: {name}")
        return self._stream_verified("WORK/" + name, self.files[name])

    def verify(self):
        """Stream every source member; never extracts or loads task data as text."""
        total = 0
        for name in self.files:
            total += self.verify_member(name)
        for name, digest in self.entries.items():
            total += self._stream_verified(name, digest)
        return {"packet_id": self.packet_id, "files_verified": len(self.files),
                "outer_entries_verified": len(self.entries), "uncompressed_bytes_verified": total,
                "scope": "original ZIP only; this is not stock review.py verify"}

    def _hydrate_one(self, root, name, archive_name, expected):
        target = safe_target(root, name)
        if target.exists():
            if not target.is_file() or sha(regular_bytes(target)) != expected:
                raise ValueError(f"Refusing to overwrite changed/unsafe local file: {target}")
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".portable-stage-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as output:
                size = self._stream_verified(archive_name, expected, output)
                output.flush()
                os.fsync(output.fileno())
            # Publish only verified complete bytes, and never overwrite a late edit.
            no_symlinks(target)
            os.link(temporary, target)
            sync_dir(target.parent)
            return size
        finally:
            Path(temporary).unlink(missing_ok=True)

    def hydrate(self, work, names):
        total = 0
        for name in names:
            safe_name(name)
            if name not in self.files:
                raise ValueError(f"Not in issued manifest: {name}")
            total += self._hydrate_one(work, name, "WORK/" + name, self.files[name])
        return {"packet_id": self.packet_id, "new_bytes": total}

    def bootstrap(self, outer):
        """Only workflow code/scripts and issued manifest/entries, no task data."""
        outer = no_symlinks(outer)
        work = outer / "WORK"
        work.mkdir(parents=True, exist_ok=True)
        target = safe_target(work, "PACKET-MANIFEST.json")
        if target.exists():
            if regular_bytes(target) != self.raw_manifest:
                raise ValueError("Existing local manifest differs from original ZIP")
        else:
            atomic_write(target, self.raw_manifest)
        for name, digest in self.entries.items():
            self._hydrate_one(outer, name, name, digest)
        names = [name for name in self.files if
                 (name.startswith("repo/src/arcpuzzles/") and name.endswith(".py"))
                 or ("/" not in name and name.endswith(".py"))]
        return self.hydrate(work, names)

    def unchanged_source(self, work, name, expected):
        """Package guard for noncandidate paths only; never hydrates a deletion."""
        if self.files.get(name) != expected:
            raise ValueError(f"Packager digest differs from original manifest: {name}")
        target = safe_target(work, name)
        if target.exists():
            return target.is_file() and sha(regular_bytes(target)) == expected
        self.verify_member(name)
        return True


def compile_package_adapter(source, namespace, packet, work):
    """Clone just the stock function, replacing exactly its global source guard.

    The issued module namespace is copied, not modified. Candidate/deletion,
    frozen-baseline, scope, exposure, evidence, and static ZIP checks are intact.
    CLI verifies this source file against the original ZIP before calling here.
    """
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "build_full_return"]
    if len(functions) != 1:
        raise ValueError("Unrecognized stock build_full_return function")
    function = copy.deepcopy(functions[0])
    expected = ast.dump(ast.parse("not target.is_file() or target.is_symlink() or _sha(target.read_bytes()) != digest", mode="eval").body)
    matches = [node for node in ast.walk(function) if isinstance(node, ast.If)
               and ast.dump(node.test) == expected]
    if len(matches) != 1:
        raise ValueError("Unrecognized or ambiguous stock unchanged-source guard")
    # Ensure it really is inside the global manifest loop excluding candidates.
    containers = [node for node in ast.walk(function) if isinstance(node, ast.For)
                  and ast.unparse(node.iter) == "manifest['files'].items()"
                  and any(child is matches[0] for child in ast.walk(node))]
    candidate_guards = [node for node in ast.walk(function) if isinstance(node, ast.If)
                        and ast.unparse(node.test) == "path.startswith('repo/') and path not in candidates"
                        and any(child is matches[0] for child in ast.walk(node))]
    if len(containers) != 1 or len(candidate_guards) != 1:
        raise ValueError("Stock guard is not the noncandidate manifest guard")
    matches[0].test = ast.parse("not _portable_unchanged_source(packet_root, path, digest)", mode="eval").body
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    scope = dict(namespace)
    work = no_symlinks(work)

    def guard(packet_root, name, digest):
        if Path(packet_root).absolute() != work:
            raise ValueError("Package adapter called for another workspace")
        return packet.unchanged_source(work, name, digest)

    scope["_portable_unchanged_source"] = guard
    exec(compile(module, "<explicit ZIP-backed package adapter>", "exec"), scope)
    return scope["build_full_return"]


def import_workflow(work):
    package = Path(work).absolute() / "repo/src/arcpuzzles"
    existing = sys.modules.get("arcpuzzles")
    if existing and Path(existing.__file__).absolute().parent != package:
        raise ValueError("Another arcpuzzles package is already imported")
    sys.path.insert(0, str(package.parent))
    return importlib.import_module("arcpuzzles.review_full_draw")


def hydrate_main(packet, outer, *, plan_only=False):
    """Commit one seed, hydrate the original draw's exact sources, then draw."""
    packet.bootstrap(outer)
    work = Path(outer).absolute() / "WORK"
    seed = commit_seed(work, packet.packet_id)
    # Every operation after commitment may fail safely; retry uses the same seed.
    draw = import_workflow(work)
    if ((work / "ASSIGNMENT.json").is_file()
            and not (work / ".review/pending-main-draw.json").exists()):
        contract = draw.draw_main(work, seed=seed)
        return {"packet_id": packet.packet_id, "assignment_id": contract["assignment_id"],
                "task_id": contract["task_id"], "status": "existing completed draw; sources retained"}
    packet.hydrate(work, ["repo/catalog/runtime_files.json", "repo/catalog/authority_files.json"])
    task_id, _ = draw.main_selection_for_seed(packet.manifest, seed)
    names = draw._base_paths(work, packet.manifest, task_id)
    questions = sorted(packet.manifest["questions"], key=lambda item: item["id"])
    question = questions[int.from_bytes(hashlib.sha256(seed + b":question").digest(), "big") % len(questions)]
    names.append(f"repo/REVIEW/questions/{question['id']}.json")
    missing_bytes = sum(packet.infos["WORK/" + name].file_size for name in names
                        if not safe_target(work, name).exists())
    baseline_bytes = sum(packet.infos["WORK/" + name].file_size for name in names[:-1])
    result = {"packet_id": packet.packet_id, "task_id": task_id, "selected_members": len(names),
              "additional_source_bytes": missing_bytes, "baseline_bytes_upper_bound": baseline_bytes,
              "seed_record": ".review/portable-seed.json",
              "scope": "exact main baseline only; runtime, blind solve, audits and full verification excluded"}
    if plan_only:
        return result
    packet.hydrate(work, names)
    contract = draw.draw_main(work, seed=seed)
    result["assignment_id"] = contract["assignment_id"]
    atomic_write(work / ".review/PORTABLE-RECOVERY.json", canonical(result))
    return result


def package_return(packet, outer, out=None, *, bundle_evidence=False):
    """Explicit optional adapter; absent candidates are still stock deletions."""
    work = Path(outer).absolute() / "WORK"
    packet.bootstrap(outer)
    import_workflow(work)
    module = importlib.import_module("arcpuzzles.review_full_return")
    source_path = Path(module.__file__).absolute()
    name = source_path.relative_to(work).as_posix()
    if sha(regular_bytes(source_path)) != packet.files.get(name):
        raise ValueError("Packager source differs from original issued manifest")
    packet.verify_member(name)
    adapted = compile_package_adapter(source_path.read_text(), vars(module), packet, work)
    return adapted(work, out, bundle_evidence=bundle_evidence)


def compile_replay_adapter(source, namespace):
    """Private stock replay copy with one source-transport-only AST change.

    This low-level compiler never executes replay. The public replay_return
    entry verifies issued source bytes and limits use to /proc/self/fd/N.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ValueError("Malformed stock replay source") from error
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "replay_return"]
    if len(functions) != 1:
        raise ValueError("Unrecognized stock replay_return function")
    function = copy.deepcopy(functions[0])
    expected = ast.parse("source_zip, return_zip = Path(source_zip).resolve(), Path(return_zip).resolve()").body[0]
    matches = [node for node in ast.walk(function) if isinstance(node, ast.Assign)
               and ast.dump(node) == ast.dump(expected)]
    if len(matches) != 1 or matches[0] not in function.body:
        raise ValueError("Unrecognized or ambiguous stock replay path assignment")
    # The matched shape pins both tuple slots. Leave return_zip.resolve() and
    # every other body node untouched; change exactly the first method name.
    matches[0].value.elts[0].func.attr = "absolute"
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    scope = dict(namespace)
    exec(compile(module, "<explicit proc-fd source transport replay adapter>", "exec"), scope)
    return scope["replay_return"]


def replay_return(packet, outer, return_zip, compare_work, out, *, runtime_closure=False):
    """Replay using verified issued logic and an explicit Linux proc-fd source.

    Source transport is the only adaptation. Original archive inventory, return
    validation, extracted hashes, Git patch/root checks, and every changed-byte
    comparison execute unchanged. No original module/source is monkeypatched.
    """
    if not re.fullmatch(r"/proc/self/fd/[0-9]+", str(packet.path)):
        raise ValueError("Replay transport adapter requires explicit /proc/self/fd/N source; use stock replay for ordinary paths")
    packet.bootstrap(outer)
    work = Path(outer).absolute() / "WORK"
    import_workflow(work)
    module = importlib.import_module("arcpuzzles.review_replay")
    source_path = Path(module.__file__).absolute()
    name = source_path.relative_to(work).as_posix()
    raw_source = regular_bytes(source_path)
    if sha(raw_source) != packet.files.get(name):
        raise ValueError("Replay source differs from original issued manifest")
    packet.verify_member(name)
    adapted = compile_replay_adapter(raw_source.decode("utf-8"), vars(module))
    return adapted(packet.path, return_zip, compare_work, out, runtime_closure=runtime_closure)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--outer", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-zip")
    sub.add_parser("bootstrap")
    sub.add_parser("commit-seed")
    hydrate = sub.add_parser("hydrate")
    hydrate.add_argument("members", nargs="+", help="Exact logical WORK-relative manifest paths")
    draw = sub.add_parser("hydrate-main")
    draw.add_argument("--plan-only", action="store_true", help="Commits one stable seed but does not draw")
    package = sub.add_parser("package", help="Explicit private ZIP-backed stock packager adapter")
    package.add_argument("--out", type=Path)
    package.add_argument("--bundle-evidence", action="store_true")
    replay = sub.add_parser("replay", help="Explicit proc-fd source transport adapter retaining all stock replay checks")
    replay.add_argument("--return-zip", type=Path, required=True)
    replay.add_argument("--compare-work", type=Path)
    replay.add_argument("--out", type=Path, required=True)
    replay.add_argument("--runtime-closure", action="store_true")
    args = parser.parse_args(argv)
    with Packet(args.zip) as packet:
        work = args.outer / "WORK"
        if args.command == "verify-zip":
            result = packet.verify()
        elif args.command == "bootstrap":
            result = packet.bootstrap(args.outer)
        elif args.command == "hydrate":
            result = packet.hydrate(work, args.members)
        elif args.command == "commit-seed":
            commit_seed(work, packet.packet_id)
            result = {"packet_id": packet.packet_id, "seed_record": str(work / ".review/portable-seed.json")}
        elif args.command == "hydrate-main":
            result = hydrate_main(packet, args.outer, plan_only=args.plan_only)
        elif args.command == "package":
            result = package_return(packet, args.outer, args.out, bundle_evidence=args.bundle_evidence)
        else:
            result = replay_return(packet, args.outer, args.return_zip,
                                   args.compare_work or work, args.out,
                                   runtime_closure=args.runtime_closure)
        print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print(f"RECOVERY BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(2)

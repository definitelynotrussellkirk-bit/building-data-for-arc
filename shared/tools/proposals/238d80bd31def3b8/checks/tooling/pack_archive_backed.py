#!/usr/bin/env python3
"""Optional, version-bound ARCpuzzles return builder for a sparse packet.

Requires the adjacent packet_zip.py. Issued files remain unchanged. The only
controller transformation extends immutable-source verification to the original
archive when a source is absent locally. All local edits, stock return gates,
patch generation, budgets and INTAKE generation retain their issued behavior.
"""

import argparse
import ast
from contextlib import ExitStack, contextmanager
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import types
import zipfile

import packet_zip


BUILDER_PATH = "repo/src/arcpuzzles/review_full_return.py"
ISSUED_BUILDER_SHA256 = "a021d00ec056acbdf0958955f5d08f110bff934375a6dac397fc3f86089a2f74"
ORIGINAL_LOOP = '''\
for path, digest in manifest["files"].items():
    if path.startswith("repo/") and path not in candidates:
        target = packet_root / path
        if not target.is_file() or target.is_symlink() or _sha(target.read_bytes()) != digest:
            raise ValueError(f"Changed or missing shared packet source: {path}")
'''
REPLACEMENT_LOOP = '''\
for path, digest in manifest["files"].items():
    if path.startswith("repo/") and path not in candidates:
        _archive_backed_verify_immutable(packet_root, path, digest)
'''


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


@contextmanager
def _local_source(root, relative, *, absent_ok=False):
    """Open a regular file through directory descriptors; reject every symlink."""
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(p in (".", "..") for p in parts):
        raise ValueError("Invalid source binding path")
    with ExitStack() as handles:
        stream = None
        try:
            # These POSIX primitives are shared with the adjacent extraction tool.
            directory = packet_zip._root_fd(root)
            handles.callback(os.close, directory)
            parent = packet_zip._walk_dir(directory, parts[:-1])
            handles.callback(os.close, parent)
            descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 dir_fd=parent)
            handles.callback(os.close, descriptor)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError("Source is not a regular file: " + relative)
            stream = handles.enter_context(os.fdopen(descriptor, "rb", closefd=False))
        except FileNotFoundError:
            if not absent_ok:
                raise ValueError("Required local source is missing: " + relative) from None
        except OSError as error:
            raise ValueError("Local source has a symlink or unsafe path: " + relative) from error
        yield stream


def _required_bytes(root, relative):
    with _local_source(root, relative) as source:
        return source.read()


class ArchiveSourceVerifier:
    """Bind a complete original archive to one unchanged packet manifest."""

    def __init__(self, packet, packet_root):
        self.packet = packet
        self.root = Path(os.path.abspath(packet_root))
        self.manifest = packet.manifest
        self.archive_fallback_count = 0
        self.local_verified_count = 0
        self.archive_fully_verified = False
        raw = _required_bytes(self.root, "PACKET-MANIFEST.json")
        if raw != packet.manifest_raw:
            raise ValueError("Local packet manifest does not match original archive manifest")
        if raw != _canonical(self.manifest):
            raise ValueError("Original packet manifest is not canonical")
        layout = self.manifest["layout"]
        if layout.get("workspace") != "WORK" or set(layout["entry_files"]) != {"START-HERE.md", "review.py"}:
            raise ValueError("Unsupported original packet entry layout")
        for name, expected in layout["entry_files"].items():
            if _sha(_required_bytes(self.root.parent, name)) != expected:
                raise ValueError("Original outer entry file changed: " + name)

    def verify_all_archive_sources(self):
        """Verify every inventoried original byte without materializing payloads."""
        self.packet.verify(sorted(self.packet.hashes))
        self.archive_fully_verified = True

    def verify(self, packet_root, relative, expected):
        """Stock local checks, or exact archive verification for an absent file."""
        if (Path(os.path.abspath(packet_root)) != self.root
                or not relative.startswith("repo/")
                or self.manifest["files"].get(relative) != expected
                or self.packet.hashes.get("WORK/" + relative) != expected):
            raise ValueError("Immutable source binding mismatch: " + relative)
        with _local_source(self.root, relative, absent_ok=True) as source:
            if source is not None:
                actual, _ = packet_zip._digest(source)
                if actual != expected:
                    raise ValueError("Changed or missing shared packet source: " + relative)
                self.local_verified_count += 1
                return
        # No local file, symlink, unsafe ancestor or changed local data is hidden.
        # copy_verified checks exact membership, streamed SHA-256, CRC and size.
        self.packet.copy_verified("WORK/" + relative)
        self.archive_fallback_count += 1

    def controller_sources(self):
        """Freeze manifest-verified local Python sources, excluding bytecode."""
        sources = {}
        prefix = "repo/src/"
        for relative, expected in self.manifest["files"].items():
            if not relative.startswith(prefix + "arcpuzzles/") or not relative.endswith(".py"):
                continue
            raw = _required_bytes(self.root, relative)
            if _sha(raw) != expected:
                raise ValueError("Local controller source changed: " + relative)
            sources[relative[len(prefix):]] = raw
        if "arcpuzzles/__init__.py" not in sources or BUILDER_PATH[len(prefix):] not in sources:
            raise ValueError("Required controller source binding is missing")
        return sources

    def receipt(self):
        return {
            "schema": "arcpuzzles-archive-backed-builder-v1",
            "proposal": True,
            "archive_sha256": self.packet.archive_sha256,
            "manifest_sha256": _sha(self.packet.manifest_raw),
            "controller_sha256": ISSUED_BUILDER_SHA256,
            "complete_archive_verified": self.archive_fully_verified,
            "archive_files_verified": len(self.packet.hashes) if self.archive_fully_verified else 0,
            "immutable_sources_verified_locally": self.local_verified_count,
            "immutable_sources_verified_from_archive": self.archive_fallback_count,
            "transformed_ast_loops": 1,
            "intake_generation": "unchanged issued controller",
        }


def transform_builder(source, expected_sha256):
    """Compile an exact-one loop extension, bound to a reviewed source hash."""
    if _sha(source) != expected_sha256:
        raise ValueError("Unsupported controller source SHA-256; version binding failed")
    text = source.decode("utf-8")
    tree = ast.parse(text, filename=BUILDER_PATH)
    expected_loop = ast.dump(ast.parse(ORIGINAL_LOOP).body[0])
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.For)
               and ast.dump(node) == expected_loop]
    builders = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "build_full_return"]
    if len(matches) != 1 or len(builders) != 1 or matches[0] not in builders[0].body:
        raise ValueError("Controller AST must contain exactly one known immutable-source loop")
    original = matches[0]
    indent = " " * original.col_offset
    replacement = "".join(indent + line + "\n" for line in REPLACEMENT_LOOP.splitlines())
    lines = text.splitlines(keepends=True)
    changed = "".join(lines[:original.lineno - 1]) + replacement + "".join(lines[original.end_lineno:])
    revised = ast.parse(changed, filename=BUILDER_PATH)
    # Restore only the changed node in a comparison tree: every other AST node
    # must be identical, including stock validation and INTAKE construction.
    revised_builder = next(node for node in revised.body if isinstance(node, ast.FunctionDef)
                           and node.name == "build_full_return")
    position = builders[0].body.index(original)
    revised_builder.body[position] = original
    if ast.dump(revised) != ast.dump(tree):
        raise ValueError("Controller AST transformation changed unrelated logic")
    return compile(changed, BUILDER_PATH, "exec", dont_inherit=True), changed


class _FrozenLoader(importlib.abc.Loader):
    def __init__(self, raw, filename, is_package):
        self.raw, self.filename, self.is_package = raw, str(filename), is_package

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.__file__ = self.filename
        if self.is_package:
            module.__path__ = [str(Path(self.filename).parent)]
        exec(compile(self.raw, self.filename, "exec", dont_inherit=True), module.__dict__)


class _FrozenFinder(importlib.abc.MetaPathFinder):
    def __init__(self, sources, source_root):
        self.sources, self.source_root = sources, source_root

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "arcpuzzles" and not fullname.startswith("arcpuzzles."):
            return None
        relative = fullname.replace(".", "/")
        for name, package in ((relative + "/__init__.py", True), (relative + ".py", False)):
            if name in self.sources:
                loader = _FrozenLoader(self.sources[name], self.source_root / name, package)
                return importlib.util.spec_from_loader(fullname, loader, is_package=package)
        raise ModuleNotFoundError("Controller module is outside verified source binding: " + fullname)


@contextmanager
def frozen_controllers(sources, source_root):
    """Load only verified controller bytes, with no preloaded modules or pyc."""
    def owned(name):
        return name == "arcpuzzles" or name.startswith("arcpuzzles.")
    if any(owned(name) for name in sys.modules):
        raise ValueError("Preloaded arcpuzzles controllers are not allowed; run this tool in a fresh process")
    finder = _FrozenFinder(sources, Path(source_root))
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        for name in list(sys.modules):
            if owned(name):
                del sys.modules[name]


def build_archive_backed(archive, packet_root, *, out=None, bundle_evidence=False,
                         expected_archive_sha256=None):
    """Run the isolated stock builder and publish only its validated output."""
    root = Path(os.path.abspath(packet_root))
    with ExitStack() as resources:
        with packet_zip.open_packet(archive, expected_archive_sha256) as packet:
            verifier = ArchiveSourceVerifier(packet, root)
            verifier.verify_all_archive_sources()
            sources = verifier.controller_sources()
            code, _ = transform_builder(sources[BUILDER_PATH[len("repo/src/"):]], ISSUED_BUILDER_SHA256)
            with frozen_controllers(sources, root / "repo/src"):
                module = types.ModuleType("arcpuzzles._archive_backed_return")
                module.__package__ = "arcpuzzles"
                module.__file__ = str(root / BUILDER_PATH)
                module.__dict__["_archive_backed_verify_immutable"] = verifier.verify
                exec(code, module.__dict__)
                # Stock builder chooses the usual default filename. Staging is
                # outside repo/ and retained until the archive identity check.
                contract = json.loads(_required_bytes(root, "ASSIGNMENT.json"))
                identifier = contract.get("assignment_id")
                if not isinstance(identifier, str) or not identifier.startswith("review-") or any(
                        c not in "review-0123456789abcdef" for c in identifier):
                    raise ValueError("Invalid assignment ID for output filename")
                destination = Path(os.path.abspath(out or root / f"review_response_{identifier}.zip"))
                if destination.exists() or destination.is_symlink():
                    raise FileExistsError(destination)
                staging = resources.enter_context(tempfile.TemporaryDirectory(prefix=".archive-backed-", dir=root))
                staged = Path(staging) / "return.zip"
                result = module.build_full_return(root, staged, bundle_evidence=bundle_evidence)
                result["archive_backed_verification"] = verifier.receipt()
        destination.parent.mkdir(parents=True, exist_ok=True)
        # No overwrite. Linking publishes already validated bytes without a second
        # copy. An explicitly requested destination must be on the same filesystem.
        os.link(staged, destination, follow_symlinks=False)
        result["zip"] = str(destination)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--packet-root", required=True, help="issued WORK directory")
    parser.add_argument("--out", help="new return ZIP on the same filesystem as WORK")
    parser.add_argument("--bundle-evidence", action="store_true")
    parser.add_argument("--expected-archive-sha256")
    args = parser.parse_args(argv)
    try:
        result = build_archive_backed(args.archive, args.packet_root, out=args.out,
                                      bundle_evidence=args.bundle_evidence,
                                      expected_archive_sha256=args.expected_archive_sha256)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (ValueError, OSError, packet_zip.PacketError, zipfile.BadZipFile) as error:
        print(json.dumps({"status": "error", "error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

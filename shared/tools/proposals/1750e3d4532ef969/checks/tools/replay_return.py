"""Safely replay patches/source.patch from a return ZIP onto a fresh packet.

Usage: python3 replay_return.py ORIGINAL_ZIP RETURN_ZIP FRESH_DIRECTORY
                              --receipt RECEIPT_JSON

The receipt must be new and outside FRESH_DIRECTORY. This tool checks and
applies standard text patches with unquoted, unchanged repo/ paths, including
file additions and deletions. Cross-path, rename/copy, and binary patches are
rejected. It does not run regression tests or archive-supplied commands.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile


PATCH_MEMBER = "patches/source.patch"


class ReplayError(Exception):
    pass


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_parts(name):
    if (not name or name.startswith("/") or "\\" in name or ":" in name
            or any(ord(character) < 32 for character in name)):
        raise ReplayError("Unsafe path: " + repr(name))
    parts = name.split("/")
    if any(part in ("", ".", "..") or part.casefold() == ".git"
           for part in parts):
        raise ReplayError("Unsafe path or Git metadata: " + repr(name))
    return parts


def validate_patch_headers(patch):
    """Check both sides of each file header, without reading hunk text as headers.

    The source-return format uses ordinary Git text diffs. Conservatively refuse
    quoted/whitespace paths and cross-path changes instead of approximating Git's
    pathname quoting or rename/copy semantics.
    """
    def repo_path(value, prefix=b""):
        if not value.startswith(prefix):
            raise ReplayError("Unexpected patch path prefix")
        value = value[len(prefix):]
        if not value or any(character in b' \t\r\n"' for character in value):
            raise ReplayError("Quoted or whitespace patch paths are unsupported")
        name = os.fsdecode(value)
        parts = safe_parts(name)
        if len(parts) < 2 or parts[0] != "repo":
            raise ReplayError("Both old and new source patch paths must be inside repo/")
        return name

    current_path = None
    old_remaining = new_remaining = 0
    sections = 0
    for line in patch.splitlines():
        if line == b"\\ No newline at end of file":
            continue
        if old_remaining or new_remaining:
            marker = line[:1]
            if marker == b" ":
                old_remaining -= 1
                new_remaining -= 1
            elif marker == b"-":
                old_remaining -= 1
            elif marker == b"+":
                new_remaining -= 1
            else:
                raise ReplayError("Malformed text patch hunk")
            if old_remaining < 0 or new_remaining < 0:
                raise ReplayError("Text patch hunk exceeds its declared line counts")
            continue
        if line.startswith(b"diff --git "):
            fields = line.split(b" ")
            if len(fields) != 4:
                raise ReplayError("Only unquoted Git patch paths are supported")
            old_path = repo_path(fields[2], b"a/")
            new_path = repo_path(fields[3], b"b/")
            if old_path != new_path:
                raise ReplayError("Cross-path patches are unsupported")
            current_path = old_path
            sections += 1
        elif line.startswith((b"--- ", b"+++ ")):
            if current_path is None:
                raise ReplayError("File header appeared before its Git diff header")
            value = line[4:]
            if value != b"/dev/null":
                prefix = b"a/" if line.startswith(b"--- ") else b"b/"
                if repo_path(value, prefix) != current_path:
                    raise ReplayError("File header differs from its Git diff path")
        elif line.startswith((b"rename from ", b"rename to ",
                              b"copy from ", b"copy to ")):
            # Reject every such operation, including headers inconsistent with
            # an otherwise safe diff --git line.
            raise ReplayError("Rename and copy patches are unsupported")
        elif line.startswith(b"@@"):
            match = re.fullmatch(
                rb"@@ -[0-9]+(?:,([0-9]+))? \+[0-9]+(?:,([0-9]+))? @@(?:.*)",
                line,
            )
            if current_path is None or match is None:
                raise ReplayError("Unsupported or malformed patch hunk header")
            old_remaining = int(match.group(1) or b"1")
            new_remaining = int(match.group(2) or b"1")
        elif line.startswith((b"GIT binary patch", b"Binary files ",
                              b"diff --cc ", b"diff --combined ")):
            raise ReplayError("Only ordinary Git text patches are supported")
    if not sections or old_remaining or new_remaining:
        raise ReplayError("Missing Git diff header or incomplete text patch hunk")


def validate_zip(archive):
    entries = []
    kinds = {}
    total_size = 0
    for info in archive.infolist():
        is_directory = info.is_dir()
        name = info.filename[:-1] if is_directory else info.filename
        parts = safe_parts(name)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ReplayError("ZIP contains a symlink or special file: " + name)
        if kind == stat.S_IFDIR and not is_directory:
            raise ReplayError("ZIP directory metadata conflicts with its name: " + name)
        if name in kinds:
            raise ReplayError("ZIP contains a duplicate path: " + name)
        kinds[name] = is_directory
        entries.append((info, parts, is_directory))
        total_size += info.file_size
    if len(entries) > 100000 or total_size > 1024 * 1024 * 1024:
        raise ReplayError("ZIP exceeds the 100000-member or 1 GiB expanded limit")
    for _, parts, _ in entries:
        for length in range(1, len(parts)):
            if kinds.get("/".join(parts[:length])) is False:
                raise ReplayError("ZIP has a file/directory path conflict")
    return entries


def extract_original(archive, entries, destination):
    # mkdir is exclusive, including when an existing destination is a symlink.
    destination.mkdir(parents=True, exist_ok=False)
    for info, parts, is_directory in entries:
        target = destination.joinpath(*parts)
        if is_directory:
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, target.open("xb") as output:
            shutil.copyfileobj(source, output)
        executable = (info.external_attr >> 16) & 0o111
        target.chmod(0o755 if executable else 0o644)


def snapshot(root):
    result = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if name != ".git"]
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise ReplayError("Unexpected symlink directory after replay")
        for name in files:
            path = Path(directory) / name
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                raise ReplayError("Unexpected non-regular file after replay: " + str(path))
            relative = path.relative_to(root).as_posix()
            result[relative] = (sha256(path), stat.S_IMODE(metadata.st_mode))
    return result


def run_git(argv, root, environment, receipt):
    entry = {"argv": argv, "cwd": str(root), "exit_code": None}
    receipt["commands"].append(entry)
    try:
        process = subprocess.run(argv, cwd=root, env=environment,
                                 capture_output=True, check=False)
    except OSError as error:
        entry["error"] = str(error)
        raise ReplayError("Could not start Git: " + str(error)) from error
    entry["exit_code"] = process.returncode
    for key, value in (("stdout", process.stdout), ("stderr", process.stderr)):
        if value:
            entry[key] = value[:4096].decode("utf-8", errors="replace")
            if len(value) > 4096:
                entry[key + "_truncated"] = True
    if process.returncode:
        raise ReplayError("Git command failed with exit " + str(process.returncode))
    return process.stdout


def replay(original, returned, destination, receipt):
    root = None
    before = None
    try:
        receipt["stage"] = "hash_inputs"
        receipt["original_zip"]["sha256"] = sha256(original)
        receipt["return_zip"]["sha256"] = sha256(returned)
        receipt["stage"] = "validate_archives"
        with zipfile.ZipFile(original) as original_archive, \
                zipfile.ZipFile(returned) as return_archive:
            original_entries = validate_zip(original_archive)
            return_entries = validate_zip(return_archive)
            patch_members = [info for info, _, is_directory in return_entries
                             if info.filename == PATCH_MEMBER and not is_directory]
            if len(patch_members) != 1:
                raise ReplayError("Return must contain exactly " + PATCH_MEMBER)
            if patch_members[0].file_size > 64 * 1024 * 1024:
                raise ReplayError("Patch exceeds 64 MiB")
            patch = return_archive.read(patch_members[0])
            receipt["patch"]["sha256"] = hashlib.sha256(patch).hexdigest()
            validate_patch_headers(patch)
            # A source return must not introduce symlinks or Git submodules.
            for mode in re.findall(
                    rb"(?m)^(?:new file mode|deleted file mode|old mode|new mode) ([0-9]+)$",
                    patch):
                if mode not in (b"100644", b"100755"):
                    raise ReplayError("Patch contains an unsupported file mode")
            if os.path.lexists(destination):
                raise ReplayError("Destination already exists; it was left untouched")
            receipt["stage"] = "extract_original"
            extract_original(original_archive, original_entries, destination)

        receipt["stage"] = "detect_root"
        layouts = [("envelope", destination / "WORK"), ("legacy", destination)]
        matches = [(name, path.resolve()) for name, path in layouts
                   if (path / "repo").is_dir()]
        if len(matches) != 1:
            raise ReplayError("Expected exactly one layout: WORK/repo or repo")
        receipt["layout"], root = matches[0]
        receipt["git_root"] = str(root)
        before = snapshot(root)
        git = shutil.which("git")
        if git is None:
            raise ReplayError("Git executable was not found")
        git = str(Path(git).resolve())
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("GIT_")}
        environment.update({"GIT_CONFIG_NOSYSTEM": "1",
                            "GIT_CONFIG_GLOBAL": os.devnull,
                            "GIT_ATTR_NOSYSTEM": "1",
                            "GIT_TERMINAL_PROMPT": "0"})

        with tempfile.TemporaryDirectory(prefix="patch-replay-") as temporary:
            temporary = Path(temporary)
            empty = temporary / "empty"
            empty.mkdir()
            patch_path = temporary / "source.patch"
            patch_path.write_bytes(patch)
            patch_path.chmod(0o644)
            base = [git, "-c", "core.hooksPath=" + str(empty),
                    "-c", "core.fsmonitor=false"]
            receipt["stage"] = "initialize_git"
            run_git(base + ["init", "-q", "--template=" + str(empty)],
                    root, environment, receipt)
            receipt["stage"] = "confirm_git_root"
            observed = run_git(base + ["rev-parse", "--show-toplevel"],
                               root, environment, receipt)
            if Path(os.fsdecode(observed).rstrip("\n")).resolve() != root:
                raise ReplayError("Git worktree root differs from the detected root")
            observed = run_git(base + ["rev-parse", "--absolute-git-dir"],
                               root, environment, receipt)
            if Path(os.fsdecode(observed).rstrip("\n")).resolve() != root / ".git":
                raise ReplayError("Git metadata is not isolated inside the detected root")
            receipt["stage"] = "validate_patch_paths"
            numstat = run_git(base + ["apply", "--numstat", "-z", "--", str(patch_path)],
                              root, environment, receipt)
            for entry in numstat.split(b"\0"):
                if entry:
                    fields = entry.split(b"\t", 2)
                    if len(fields) != 3:
                        raise ReplayError("Unexpected Git patch-path output")
                    parts = safe_parts(os.fsdecode(fields[2]))
                    if parts[0] != "repo":
                        raise ReplayError("Source patch must target repo/ paths")
            receipt["stage"] = "check_patch"
            run_git(base + ["apply", "--check", "--", str(patch_path)],
                    root, environment, receipt)
            receipt["stage"] = "apply_patch"
            run_git(base + ["apply", "--", str(patch_path)],
                    root, environment, receipt)
        receipt["stage"] = "complete"
        receipt["status"] = "success"
    except (ReplayError, OSError, ValueError, zipfile.BadZipFile,
            RuntimeError, EOFError) as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
    finally:
        # Capture observed changes even if a later Git command failed.
        if root is not None and before is not None:
            try:
                after = snapshot(root)
                changed = sorted(path for path in before.keys() | after.keys()
                                 if before.get(path) != after.get(path))
                receipt["patched_files"] = {
                    path: after[path][0] if path in after else None for path in changed
                }
                receipt["patched_file_modes"] = {
                    path: oct(after[path][1]) for path in changed if path in after
                }
            except (ReplayError, OSError) as error:
                receipt["status"] = "failed"
                receipt["snapshot_error"] = str(error)


def write_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".replay-receipt-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.chmod(0o644)
        # Linking a fully written temporary file creates the destination
        # exclusively. Unlike replace(), this cannot clobber a late collision
        # or follow an existing destination symlink.
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_zip", type=Path)
    parser.add_argument("return_zip", type=Path)
    parser.add_argument("fresh_directory", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    arguments = parser.parse_args()
    original = arguments.original_zip.resolve()
    returned = arguments.return_zip.resolve()
    destination = Path(os.path.abspath(arguments.fresh_directory))
    # Keep the literal leaf for lexists and exclusive creation. Resolving it
    # first would follow an existing (including dangling) receipt symlink.
    receipt_path = Path(os.path.abspath(arguments.receipt))
    receipt = {"schema": "patch-replay-receipt-v1", "status": "failed",
               "verification": "patch_application_only", "stage": "preflight",
               "original_zip": {"path": str(original), "sha256": None},
               "return_zip": {"path": str(returned), "sha256": None},
               "patch": {"member": PATCH_MEMBER, "sha256": None},
               "destination": str(destination), "git_root": None,
               "commands": [], "patched_files": {}}
    if os.path.lexists(receipt_path):
        receipt["error"] = "Receipt already exists; it was left untouched"
        print(json.dumps(receipt), file=sys.stderr)
        return 1
    resolved_receipt = receipt_path.resolve()
    if (resolved_receipt in (original, returned)
            or resolved_receipt.is_relative_to(destination.resolve())):
        receipt["error"] = "Receipt must be outside the destination and distinct from inputs"
        print(json.dumps(receipt), file=sys.stderr)
        return 1
    replay(original, returned, destination, receipt)
    try:
        write_receipt(receipt_path, receipt)
    except OSError as error:
        receipt["status"] = "failed"
        receipt["receipt_error"] = str(error)
        print(json.dumps(receipt), file=sys.stderr)
        return 1
    if receipt["status"] != "success":
        print("Replay failed: " + receipt.get("error", receipt.get("snapshot_error", "unknown")),
              file=sys.stderr)
        return 1
    print("Patch applied; receipt: " + str(receipt_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

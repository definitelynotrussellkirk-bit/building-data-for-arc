#!/usr/bin/env python3
"""Opt-in Linux recovery launcher for an explicitly new, empty task directory.
Pre-create TASK and OUT outside each other, then run:
  python3 recovery_helper.py --enable-private-tmpfs --task-dir TASK --output-dir OUT -- bash
TMPFS CONTENTS DISAPPEAR at session exit. Only WORK/**/review_response_*.zip
is copied to OUT; existing files are never overwritten. No extraction or cleanup
is automatic. --memory-mib limits tmpfs capacity, not process RAM. This is not a
security sandbox; commands retain access to files available to the invoking user.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def directory(value, empty=False):
    p = Path(os.path.abspath(os.path.expanduser(value)))
    if any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError(f"symlink paths are forbidden: {p}")
    if not p.is_dir():
        raise ValueError(f"directory must already exist: {p}")
    if empty and (os.path.ismount(p) or next(p.iterdir(), None) is not None):
        raise ValueError(f"task directory must be new, empty, and not a mount point: {p}")
    return p


def validate(a):
    if sys.platform != "linux":
        raise ValueError("unsupported: Linux is required")
    if not a.enable_private_tmpfs:
        raise ValueError("explicit --enable-private-tmpfs opt-in is required")
    if not 256 <= a.memory_mib <= 4096:
        raise ValueError("--memory-mib must be between 256 and 4096")
    if not a.command or not a.task_dir or not a.output_dir:
        raise ValueError("--task-dir, --output-dir, and an explicit command are required")
    task, output = directory(a.task_dir, True), directory(a.output_dir)
    if output == task or task in output.parents:
        raise ValueError("output directory must be outside the task directory")
    executables = [shutil.which(name) for name in ("unshare", "mount")]
    if not all(executables):
        raise ValueError("unsupported: both unshare and mount must be installed")
    return task, output, executables


def inside(config):
    a = argparse.Namespace(**json.loads(config))
    task, output, (_, mount) = validate(a)
    if set(a.namespaces) != {"user", "mnt"} or any(os.readlink(f"/proc/self/ns/{name}") == old for name, old in a.namespaces.items()):
        raise ValueError("refusing mount: both user and mount namespaces must change")
    subprocess.run([mount, "--make-rprivate", "/"], check=True)
    subprocess.run([mount, "-t", "tmpfs", "-o", f"size={a.memory_mib}m,mode=700,nodev,nosuid", "tmpfs", str(task)], check=True)
    code = 127
    try:
        try:
            code = subprocess.call(a.command, cwd=task)
        except (OSError, KeyboardInterrupt) as exc:
            print(f"command failed: {exc}", file=sys.stderr)
            code = 130 if isinstance(exc, KeyboardInterrupt) else 127
    finally:
        work = task / "WORK"
        if work.is_dir() and not work.is_symlink():
            for src in sorted(work.rglob("review_response_*.zip")):
                if not src.is_file() or any(p.is_symlink() for p in (src, *src.parents)):
                    continue
                try:
                    dest = output / src.name
                    try:
                        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    except FileExistsError:
                        fd, name = tempfile.mkstemp(prefix=src.stem + "-", suffix=".zip", dir=output)
                        dest = Path(name)
                    with os.fdopen(fd, "wb") as dst, src.open("rb") as source:
                        shutil.copyfileobj(source, dst)
                    print(f"Preserved: {dest}", flush=True)
                except OSError as exc:
                    print(f"preservation failed: {src}: {exc}", file=sys.stderr)
                    code = 74
    return code


def self_test():
    import unittest
    from unittest.mock import patch
    class Guards(unittest.TestCase):
        def test_guards(self):
            with tempfile.TemporaryDirectory() as raw:
                base = Path(raw); task = base / "task"; task.mkdir(); out = base / "out"; out.mkdir()
                a = argparse.Namespace(enable_private_tmpfs=True, task_dir=str(task), output_dir=str(out), memory_mib=256, command=["true"])
                with patch("shutil.which", return_value="/usr/bin/tool"):
                    self.assertEqual(validate(a)[:2], (task, out))
                    for key, value in (("memory_mib", 255), ("memory_mib", 4097), ("enable_private_tmpfs", False), ("command", []), ("output_dir", str(task)), ("task_dir", str(base / "missing"))):
                        bad = argparse.Namespace(**vars(a)); setattr(bad, key, value)
                        with self.subTest(key=key, value=value), self.assertRaises(ValueError): validate(bad)
                    (task / "keep").write_text("untouched")
                    with self.assertRaises(ValueError): validate(a)
                    self.assertEqual((task / "keep").read_text(), "untouched")
                    link = base / "link"; link.symlink_to(out, target_is_directory=True)
                    with self.assertRaises(ValueError): directory(str(link))
                    with self.assertRaises(ValueError): directory(str(link / "child"))
                with patch("sys.platform", "darwin"), self.assertRaises(ValueError): validate(a)
                a.task_dir, a.output_dir = str(out), str(base)
                with patch("shutil.which", return_value=None), self.assertRaisesRegex(ValueError, "unsupported"): validate(a)
                a.namespaces = {name: os.readlink(f"/proc/self/ns/{name}") for name in ("user", "mnt")}
                with patch("shutil.which", return_value="/usr/bin/tool"), patch("subprocess.run") as mount_call:
                    with self.assertRaisesRegex(ValueError, "refusing mount"): inside(json.dumps(vars(a)))
                    mount_call.assert_not_called()
    return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards)).wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--enable-private-tmpfs", action="store_true")
    parser.add_argument("--task-dir"); parser.add_argument("--output-dir")
    parser.add_argument("--memory-mib", type=int, default=512)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    a = parser.parse_args()
    if a.self_test: return self_test()
    if a.command[:1] == ["--"]: a.command.pop(0)
    task, output, (unshare, _) = validate(a)
    a.task_dir, a.output_dir = str(task), str(output)
    a.namespaces = {name: os.readlink(f"/proc/self/ns/{name}") for name in ("user", "mnt")}
    print("WARNING: tmpfs disappears at exit; only WORK/**/review_response_*.zip will be preserved.", file=sys.stderr, flush=True)
    child = "import runpy,sys; sys.exit(runpy.run_path(sys.argv[1])['inside'](sys.argv[2]))"
    return subprocess.call([unshare, "--user", "--map-root-user", "--mount", "--fork", "--", sys.executable, "-c", child, str(Path(__file__).resolve()), json.dumps(vars(a))])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"recovery_helper: {exc}", file=sys.stderr)
        sys.exit(2)

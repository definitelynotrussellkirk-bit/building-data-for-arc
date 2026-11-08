"""Portable Racket activation: immutable generations, explicit identity, no fallback.

The cache is private to the current user. Activation is POSIX-only (Kaggle/Linux).
This is a deployment helper, not a sandbox for untrusted executable bundles.
"""
from __future__ import annotations

import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile


class RuntimeActivationError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

    def to_dict(self) -> dict:
        return {"phase": "activation", "code": self.code, "message": str(self)}


def tree_sha256(root: Path) -> str:
    """Hash relative names, entry types, link targets and bytes (not mount modes)."""
    root = Path(root).resolve(strict=True)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix().encode()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(path)
            if os.path.isabs(target) or not path.resolve().is_relative_to(root):
                raise RuntimeActivationError("bundle_link", f"Nonportable link: {relative!r}")
            payload = b"L\0" + relative + b"\0" + target.encode()
        elif stat.S_ISDIR(mode):
            payload = b"D\0" + relative
        elif stat.S_ISREG(mode):
            content = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    content.update(block)
            payload = b"F\0" + relative + b"\0" + content.digest()
        else:
            raise RuntimeActivationError("bundle_entry", f"Not a regular file/directory/link: {path}")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def find_bundle(roots: list[Path]) -> Path | None:
    """Deterministic search; supplied root order is priority order."""
    for root in map(Path, roots):
        if not root.is_dir():
            continue
        for candidate in (root, root / "racket-bundle"):
            if (candidate / "bin/racket").is_file():
                return candidate.resolve()
        for binary in sorted(root.rglob("racket-bundle/bin/racket")):
            if binary.is_file():
                return binary.resolve().parents[1]
    return None


def bundle_environment(destination: Path) -> dict[str, str]:
    """Preserve relocation paths for bundles that need explicit collections."""
    env = dict(os.environ)
    layouts = {
        "LD_LIBRARY_PATH": (destination / "lib",),
        "PLTCOLLECTS": (destination / "share/racket/collects",
                        destination / "share/collects", destination / "collects"),
        "PLTCONFIGDIR": (destination / "lib/racket", destination / "etc"),
    }
    additions = {name: next((p for p in choices if p.is_dir()), None)
                 for name, choices in layouts.items()}
    for name, path in additions.items():
        if path is None:
            if name.startswith("PLT"):
                env.pop(name, None)  # Let this runtime resolve its own absent layout.
            continue
        if name == "PLTCONFIGDIR":
            env[name] = str(path)
            continue
        # Collections must belong to this runtime, not a previous activation.
        if name == "PLTCOLLECTS":
            env[name] = str(path)
            continue
        parts = [str(path), *filter(None, env.get(name, "").split(os.pathsep))]
        env[name] = os.pathsep.join(dict.fromkeys(parts))
    return env


def probe_binary(binary: Path, timeout: float = 20.0) -> dict:
    binary = Path(binary).resolve()
    runtime_env = bundle_environment(binary.parents[1])
    try:
        probe = subprocess.run([str(binary), "-e", "(displayln (+ 20 22))"],
                               capture_output=True, text=True, timeout=timeout, env=runtime_env)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeActivationError("probe_timeout", f"Racket arithmetic probe exceeded {timeout}s") from exc
    except OSError as exc:
        raise RuntimeActivationError("probe_start", str(exc)) from exc
    if probe.returncode != 0 or probe.stdout.strip() != "42":
        raise RuntimeActivationError("probe_failed", f"rc={probe.returncode}; stderr={probe.stderr[-500:]!r}")
    return {"binary": str(binary), "arithmetic": 42, "status": "pass"}


def activate_bundle(source: Path, destination: Path, *, expected_sha256: str | None = None) -> Path:
    """Copy once to ``destination/<content-sha>/``; never replace an active tree.

    ``destination`` is a cache root, not the final runtime path. Set RACKET_PATH
    only after a successful probe. Workers should receive the returned absolute
    path in an explicit environment snapshot, before they are spawned.
    """
    source, destination = Path(source).resolve(), Path(destination).absolute()
    if not (source / "bin/racket").is_file():
        raise RuntimeActivationError("bundle_missing", f"No bin/racket under {source}")
    if destination.resolve().is_relative_to(source) or source.is_relative_to(destination.resolve()):
        raise RuntimeActivationError("path_overlap", "Source and cache must be disjoint")
    if destination.is_symlink():
        raise RuntimeActivationError("cache_symlink", "Cache root must not be a symlink")
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = destination.stat()
    if metadata.st_uid != os.getuid() or metadata.st_mode & 0o022:
        raise RuntimeActivationError("cache_permissions", "Cache must be owned by this user and not group/world writable")
    fingerprint = tree_sha256(source)
    if expected_sha256 and fingerprint != expected_sha256:
        raise RuntimeActivationError("identity_mismatch", f"Expected {expected_sha256}; observed {fingerprint}")
    target = destination / fingerprint
    lock_fd = os.open(destination / ".activation.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, "a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if target.exists():
            if target.is_symlink() or tree_sha256(target) != fingerprint:
                raise RuntimeActivationError("cache_integrity", "Existing runtime differs from source; refusing to reuse or delete it")
        else:
            with tempfile.TemporaryDirectory(prefix=".stage-", dir=destination) as stage:
                staged = Path(stage) / "runtime"
                shutil.copytree(source, staged, symlinks=True)
                # Copying a read-only dataset preserves read-only directory modes.
                staged.chmod(0o700)
                for entry in staged.rglob("*"):
                    if entry.is_dir() and not entry.is_symlink():
                        entry.chmod(0o700)
                for folder in (staged / "bin", staged / "lib"):
                    if folder.is_dir():
                        for entry in folder.rglob("*"):
                            if entry.is_file() and not entry.is_symlink():
                                entry.chmod(entry.stat().st_mode | 0o500)
                if tree_sha256(staged) != fingerprint:
                    raise RuntimeActivationError("copy_integrity", "Source changed during activation")
                probe_binary(staged / "bin/racket")
                os.replace(staged, target)
        probe_binary(target / "bin/racket")
    binary = (target / "bin/racket").resolve()
    os.environ.update(bundle_environment(target))
    os.environ["RACKET_PATH"] = str(binary)
    return binary

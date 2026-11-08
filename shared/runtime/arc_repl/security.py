"""Fail-closed policy for model-generated ARC-Racket expressions.

The protected bridge also installs a Racket ``security-guard`` that denies
filesystem, network, link, and executable access.  This Python-side guard is a
second, earlier boundary: it rejects reflection, environment access,
concurrency, non-determinism, and known host-I/O entry points before the model
expression is serialized into the Racket namespace.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterator

from .parser import Symbol


POLICY_SCHEMA = "arc-racket-candidate-symbol-policy-v1"

# Keep this list exact instead of banning broad English-looking prefixes such
# as ``process`` or ``path``: the grounded ARC corpus legitimately uses those
# names for local geometry helpers.  The Racket security guard remains the
# authoritative capability boundary even when an unsafe primitive is reached
# indirectly.
FORBIDDEN_GLOBAL_SYMBOLS = frozenset(
    {
        # Reflection, code loading, namespace escape, and macro construction.
        "eval",
        "compile",
        "compile-syntax",
        # `expand` is intentionally not blocked by spelling: grounded ARC
        # solutions use it as a local BFS frontier binding. `eval`, code
        # loaders, namespace mutation, and host capabilities remain blocked,
        # so expanding syntax alone cannot cross the host boundary.
        "expand-once",
        "dynamic-require",
        "require",
        "local-require",
        "load",
        "load/use-compiled",
        "include",
        "include-at/relative-to",
        "namespace-variable-value",
        "namespace-set-variable-value!",
        "namespace-undefine-variable!",
        "namespace-mapped-symbols",
        "namespace-require",
        "namespace-require/copy",
        "namespace-require/constant",
        "namespace-require/expansion-time",
        "namespace-attach-module",
        "namespace-anchor->namespace",
        "module->namespace",
        "make-base-namespace",
        "make-empty-namespace",
        "current-namespace",
        "current-code-inspector",
        "current-inspector",
        "current-module-name-resolver",
        "datum->syntax",
        "syntax->datum",
        "quote-syntax",
        "quasisyntax",
        "unsyntax",
        "unsyntax-splicing",
        # Filesystem and host-path access. The child security guard denies these
        # too, including aliases and dynamically obtained procedures.
        "open-input-file",
        "open-output-file",
        "open-input-output-file",
        "call-with-input-file",
        "call-with-output-file",
        "with-input-from-file",
        "with-output-to-file",
        "file->string",
        "file->bytes",
        "file->lines",
        "directory-list",
        "filesystem-root-list",
        "find-system-path",
        "find-executable-path",
        "delete-file",
        "delete-directory",
        "delete-directory/files",
        "rename-file-or-directory",
        "copy-file",
        "make-file-or-directory-link",
        "make-directory",
        "make-directory*",
        "make-temporary-file",
        "file-exists?",
        "directory-exists?",
        "link-exists?",
        "file-or-directory-stat",
        "file-or-directory-permissions",
        "file-or-directory-modify-seconds",
        "current-directory",
        "current-directory-for-user",
        "current-load-relative-directory",
        "current-write-relative-directory",
        # Process, environment, FFI, and network escape.
        "system",
        "system*",
        "system/exit-code",
        "system*/exit-code",
        "shell-execute",
        "subprocess",
        "subprocess-wait",
        "subprocess-kill",
        "subprocess-status",
        "getenv",
        "putenv",
        "environment-variables-ref",
        "environment-variables-set!",
        "environment-variables-names",
        "current-environment-variables",
        "current-command-line-arguments",
        "tcp-connect",
        "tcp-connect/enable-break",
        "tcp-listen",
        "tcp-accept",
        "tcp-accept/enable-break",
        "udp-open-socket",
        "udp-bind!",
        "udp-connect!",
        "udp-send",
        "udp-send-to",
        # Persistent concurrency/resource escape. Each evaluation also runs
        # under a short-lived child custodian that is shut down before reply.
        "thread",
        "thread/suspend-to-kill",
        "thread-resume",
        "thread-suspend",
        "kill-thread",
        "break-thread",
        "future",
        # `touch` is intentionally not blocked by spelling because several
        # canonical programs use it as a local boolean. `future` creation is
        # blocked, and short-lived custodians tear down concurrent resources.
        "make-custodian",
        "custodian-shutdown-all",
        "custodian-limit-memory",
        "custodian-memory-accounting-available?",
        "current-custodian",
        "current-subprocess-custodian-mode",
        "current-security-guard",
        "make-security-guard",
        # Continuation escape can outlive the guarded dynamic extent.
        "call/cc",
        "call-with-current-continuation",
        "call-with-composable-continuation",
        "call-with-continuation-prompt",
        "abort-current-continuation",
        # Non-determinism and host-state probes.
        "random",
        "random-seed",
        "crypto-random-bytes",
        "current-pseudo-random-generator",
        "current-seconds",
        "current-inexact-milliseconds",
        "current-inexact-monotonic-milliseconds",
        "current-process-milliseconds",
        "current-gc-milliseconds",
        "current-memory-use",
        "current-thread",
        "current-input-port",
        "current-output-port",
        "current-error-port",
        "exit-handler",
        "call-in-nested-thread",
        "read",
        "read-syntax",
        "read-line",
        "read-byte",
        "read-bytes",
        "read-bytes!",
        "read-string",
        "read-char",
        "peek-byte",
        "peek-bytes",
        "peek-char",
        "port->bytes",
        "port->string",
        "copy-port",
        "current-milliseconds",
        "current-date",
        "system-type",
        "system-language+country",
        "processor-count",
        "gethostname",
        "getpid",
        "gensym",
    }
)

FORBIDDEN_SYMBOL_PREFIXES = (
    "#%",
    "ffi/",
    "unsafe-",
    "tcp-",
    "udp-",
    "ssl-",
    "namespace-",
)


def _symbols(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, Symbol):
        yield value.name, path
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _symbols(child, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for index, (key, child) in enumerate(value.items()):
            yield from _symbols(key, f"{path}.key[{index}]")
            yield from _symbols(child, f"{path}.value[{index}]")


def _canonical_symbol_name(spelling: str) -> str:
    """Normalize reader quoting that does not change a Racket identifier.

    The project parser deliberately preserves vertical-bar spelling. In
    Racket, ``|system|`` still names the ``system`` binding, so checking only
    the raw token would turn reader quoting into a trivial deny-list bypass.
    Keep case intact because Racket identifiers are case-sensitive.
    """

    if len(spelling) >= 2 and spelling[0] == "|" and spelling[-1] == "|":
        body = spelling[1:-1]
        out: list[str] = []
        escaped = False
        for character in body:
            if escaped:
                out.append(character)
                escaped = False
            elif character == "\\":
                escaped = True
            else:
                out.append(character)
        if escaped:
            out.append("\\")
        return "".join(out)
    return spelling


def forbidden_symbols(value: Any) -> list[dict[str, str]]:
    """Return unique forbidden symbol/path pairs in one parsed expression."""

    rows: dict[tuple[str, str], dict[str, str]] = {}
    for spelling, path in _symbols(value):
        symbol = _canonical_symbol_name(spelling)
        if symbol in FORBIDDEN_GLOBAL_SYMBOLS or symbol.startswith(
            FORBIDDEN_SYMBOL_PREFIXES
        ):
            row = {"symbol": symbol, "path": path}
            if spelling != symbol:
                row["spelling"] = spelling
            rows[(symbol, path)] = row
    return [rows[key] for key in sorted(rows)]


def validate_candidate_expression(value: Any) -> None:
    """Reject host-capability, reflective, and nondeterministic expressions."""

    blocked = forbidden_symbols(value)
    if blocked:
        preview = ", ".join(
            f"{row['symbol']}@{row['path']}" for row in blocked[:8]
        )
        suffix = f" (+{len(blocked) - 8} more)" if len(blocked) > 8 else ""
        raise ValueError(f"forbidden ARC-Racket symbol(s): {preview}{suffix}")


def policy_sha256() -> str:
    payload = {
        "schema": POLICY_SCHEMA,
        "forbidden_global_symbols": sorted(FORBIDDEN_GLOBAL_SYMBOLS),
        "forbidden_symbol_prefixes": list(FORBIDDEN_SYMBOL_PREFIXES),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

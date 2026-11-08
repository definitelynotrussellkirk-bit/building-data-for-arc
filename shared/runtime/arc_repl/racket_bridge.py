"""
RacketBridge — persistent Racket subprocess for evaluating S-expressions.

Replaces the Python-based evaluator with real Racket (Chez Scheme backend).
Communicates via stdin/stdout with JSON-encoded results.
"""

import subprocess
import json
import hashlib
import os
import shutil
import sys
import tarfile
import threading
import time
from collections import deque

_HERE = os.path.dirname(os.path.abspath(__file__))
_PRELUDE_PATH = os.path.join(_HERE, "racket_prelude", "arc-prelude.rkt")
_RACKET_BINARY_CACHE: str | None = None


def _file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


_RACKET_ENV_ALLOWLIST = frozenset(
    {
        "PATH",
        "HOME",
        "TMPDIR",
        "TMP",
        "TEMP",
        "TERM",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LD_LIBRARY_PATH",
        "PLTCOLLECTS",
        "PLTCONFIGDIR",
        "PLTUSERHOME",
        "PLTCOMPILEDROOTS",
        "PLT_COMPILED_FILE_CHECK",
        "ARC_REPL_SKIP_BANK_HELPERS",
    }
)


def _racket_subprocess_env(source=None):
    """Return a minimal child environment for noninteractive Racket runs.

    Copying the whole parent environment exposed Kaggle, model-host, and CI
    credentials to arbitrary model-generated ``getenv`` calls.  Racket needs a
    handful of relocation/locale variables; everything else is deliberately
    absent.  The in-process symbol policy blocks environment primitives too,
    but capability removal should not depend on one spelling deny-list.
    """

    source = os.environ if source is None else source
    env = {
        name: str(source[name])
        for name in _RACKET_ENV_ALLOWLIST
        if source.get(name) is not None
    }
    env.setdefault("PATH", os.defpath)
    if not env.get("TERM"):
        # A set-but-empty TERM is not a real terminal; the child gets the
        # explicit noninteractive one. A genuine TERM passes through above.
        env["TERM"] = "dumb"
    env.setdefault("LANG", "C.UTF-8")
    return env


def _chmod_runtime_tree(path: str) -> None:
    """Best-effort executable-bit restore for copied/extracted runtimes."""
    for root, _, files in os.walk(path):
        if os.path.basename(root) in {"bin", "lib"}:
            for name in files:
                try:
                    os.chmod(os.path.join(root, name), 0o755)
                except OSError:
                    pass


def _resolve_racket_binary() -> str:
    """Find a Racket binary without requiring callers to preconfigure PATH.

    Resolution order:
      1. Explicit RACKET_PATH.
      2. System/PATH `racket`.
      3. Pre-extracted repo-local vendor/racket/bin/racket.
      4. Repo-local vendor/racket-minimal-*.tgz, extracted once under /tmp.

    The archive used for offline/Kaggle runs already contains the tarball, so
    local parity tests should not fail merely because the host has no system
    Racket installed.
    """
    global _RACKET_BINARY_CACHE

    explicit = os.environ.get("RACKET_PATH")
    if explicit:
        return explicit
    if _RACKET_BINARY_CACHE:
        return _RACKET_BINARY_CACHE

    on_path = shutil.which("racket")
    if on_path:
        _RACKET_BINARY_CACHE = on_path
        return on_path

    repo_root = os.path.dirname(_HERE)
    extracted_binary = os.path.join(repo_root, "vendor", "racket", "bin", "racket")
    if os.path.exists(extracted_binary):
        _chmod_runtime_tree(os.path.dirname(os.path.dirname(extracted_binary)))
        _RACKET_BINARY_CACHE = extracted_binary
        return extracted_binary

    vendor_dir = os.path.join(repo_root, "vendor")
    if not os.path.isdir(vendor_dir):
        return "racket"

    tarballs = sorted(
        name for name in os.listdir(vendor_dir)
        if name.startswith("racket-minimal-") and name.endswith(".tgz")
    )
    if not tarballs:
        return "racket"

    tarball = os.path.join(vendor_dir, tarballs[-1])
    # Stable, repo-specific extraction location to avoid doing this on every
    # subprocess spawn. Include mtime/size so stale extractions are naturally
    # invalidated when the vendor tarball changes.
    stat = os.stat(tarball)
    target = os.path.join(
        "/tmp",
        f"arc_racket_{int(stat.st_mtime)}_{stat.st_size}",
    )
    binary = os.path.join(target, "racket", "bin", "racket")
    marker = os.path.join(target, ".chmod-ok")
    if not os.path.exists(binary):
        os.makedirs(target, exist_ok=True)
        with tarfile.open(tarball, "r:gz") as tf:
            tf.extractall(target)
    if os.path.exists(binary) and not os.path.exists(marker):
        _chmod_runtime_tree(os.path.join(target, "racket"))
        try:
            with open(marker, "w") as f:
                f.write("ok\n")
        except OSError:
            pass
    _RACKET_BINARY_CACHE = binary if os.path.exists(binary) else "racket"
    return _RACKET_BINARY_CACHE


def racket_runtime_status() -> dict:
    """Return a structured, side-effect-minimal protected-runtime preflight.

    Missing Racket is an unavailable optional system dependency for source-only
    review environments, not evidence that compiler or Python controller tests
    failed. A present but broken executable is *not* hidden here: callers will
    run the live handshake and surface that failure normally.
    """

    requested = _resolve_racket_binary()
    resolved = (
        requested
        if os.path.isabs(requested) or os.path.sep in requested
        else shutil.which(requested)
    )
    available = bool(
        resolved
        and os.path.isfile(resolved)
        and os.access(resolved, os.X_OK)
    )
    return {
        "schema": "arc-protected-racket-preflight-v1",
        "available": available,
        "requested_binary": requested,
        "resolved_binary": os.path.realpath(resolved) if available else None,
        "prelude_path": os.path.realpath(_PRELUDE_PATH),
        "prelude_present": os.path.isfile(_PRELUDE_PATH),
        "reason": None if available else (
            "protected Racket runtime is unavailable; install `racket`, set "
            "RACKET_PATH to an executable, or include vendor/racket-minimal-*.tgz"
        ),
    }


def racket_runtime_available() -> bool:
    """Whether a candidate Racket executable is locally available."""

    return bool(racket_runtime_status()["available"])


# Boot script: load prelude, then enter a read-eval-write-json loop.
# Protocol: one S-expression per line in, one JSON line out.
_BOOT_SCRIPT = r"""
(require json racket/list racket/string racket/match racket/dict
         racket/set racket/vector racket/format racket/port)

;; Load the ARC prelude with all grid primitives
;; Prelude path is passed as first line of stdin
(define prelude-path (read-line))

;; Set up a namespace with full Racket + prelude bindings
(define ns (make-base-namespace))
(eval '(require racket) ns)
(eval '(require json) ns)
(eval `(require (file ,prelude-path)) ns)
;; Also load heightmap into the namespace
;; Load additional prelude modules into the namespace
(define prelude-dir (path->string (simplify-path
  (build-path (string->path prelude-path) 'up))))
(for-each (lambda (mod)
  (define mod-path (string-append prelude-dir "/" mod))
  (when (file-exists? mod-path)
    (eval `(require (file ,mod-path)) ns)))
  '("heightmap.rkt" "layers.rkt"))
(current-namespace ns)

;; Override operators for ARC compatibility
;; All overrides defined as Racket code eval'd in the namespace
;; Override operators — each eval'd sequentially so earlier defs are visible
(eval '(begin
  (define = arc=)
  (define != arc!=)
  (define / arc/)
  (define range safe-range)

  ;; Safe arithmetic: treat #f as 0
  (define (safe-num x) (if (eq? x #f) 0 x))
  (define orig-+ +) (define orig-- -) (define orig-* *)
  (define orig-< <) (define orig-> >) (define orig-<= <=) (define orig->= >=)
  (define (+ . args) (apply orig-+ (map safe-num args)))
  (define (- . args) (apply orig-- (map safe-num args)))
  (define (* . args) (apply orig-* (map safe-num args)))
  (define (< . args) (apply orig-< (map safe-num args)))
  (define (> . args) (apply orig-> (map safe-num args)))
  (define (<= . args) (apply orig-<= (map safe-num args)))
  (define (>= . args) (apply orig->= (map safe-num args)))

  ;; Safe list accessors: handle #f and short lists
  (define orig-list-ref list-ref)
  (define (safe-idx? idx) (and (integer? idx) (orig->= idx 0)))
  (define (list-ref lst idx)
    (cond [(not (safe-idx? idx)) #f]
          [(orig->= idx (length lst)) #f]
          [else (orig-list-ref lst idx)]))
  (define (nth lst idx) (list-ref lst idx))
  (define (first x) (if (and (list? x) (not (empty? x))) (car x) #f))
  (define (second x) (if (and (list? x) (orig->= (length x) 2)) (list-ref x 1) #f))
  (define (third x) (if (and (list? x) (orig->= (length x) 3)) (list-ref x 2) #f))
  (define (fourth x) (if (and (list? x) (orig->= (length x) 4)) (list-ref x 3) #f))
  (define (last x) (if (and (list? x) (not (empty? x)))
    (orig-list-ref x (sub1 (length x))) #f))
) ns)

;; Load generated puzzle-bank helpers after the ARC compatibility overrides.
;; These are plain top-level forms, not a module, so helper references bind to
;; the same namespace as compacted bank rule bodies.
(define bank-helpers-path (string-append prelude-dir "/bank-helpers.rkt"))
(define skip-bank-helpers?
  (let ([v (getenv "ARC_REPL_SKIP_BANK_HELPERS")])
    (and v (not (member (string-downcase v) '("" "0" "false" "no"))))))
(when (and (not skip-bank-helpers?) (file-exists? bank-helpers-path))
  ;; Load helper definitions directly in the active ARC namespace. Reading + evaling the enlarged
  ;; helper file form-by-form is fragile: module-local reader state, begin-for-syntax, or a large
  ;; generated body can terminate the bridge during startup with no JSON handshake (reviewer round19).
  ;; `load` preserves the same namespace binding semantics without reimplementing the reader loop.
  (parameterize ([current-namespace ns])
    (load bank-helpers-path)))

;; Candidate code runs only after all trusted modules are loaded.  Deny every
;; later filesystem, network, executable, and link operation.  A child guard
;; cannot weaken its parent, and each evaluation receives a fresh custodian so
;; spawned threads/ports are torn down before the JSON reply is published.
(define (arc-deny-file who path modes)
  (error 'arc-sandbox
         "filesystem access denied: primitive=~a path=~a modes=~a"
         who path modes))
(define (arc-deny-network who host port mode)
  (error 'arc-sandbox
         "network access denied: primitive=~a host=~a port=~a mode=~a"
         who host port mode))
(define (arc-deny-link who path target)
  (error 'arc-sandbox
         "link access denied: primitive=~a path=~a target=~a"
         who path target))
(define arc-candidate-security-guard
  (make-security-guard
   (current-security-guard)
   arc-deny-file
   arc-deny-network
   arc-deny-link))

;; Serialize a Racket value to a JSON-friendly structure
(define (serialize v)
  (cond
    [(void? v) 'null]
    [(boolean? v) v]
    [(exact-integer? v) v]
    [(number? v) (inexact->exact (round (* v 1000000.0)))]  ;; float as scaled int
    [(string? v) v]
    [(null? v) '()]
    [(pair? v)
     (if (list? v)
         (map serialize v)
         (list (serialize (car v)) (serialize (cdr v))))]
    [(hash? v)
     (for/hasheq ([(k val) (in-hash v)])
       (values (if (number? k) (~a k) k)
               (serialize val)))]
    [(procedure? v) (hasheq 'type "procedure" 'name (~a v))]
    [(vector? v) (map serialize (vector->list v))]
    [else (~a v)]))

;; Main REPL loop: read line, eval, write JSON, repeat
(let loop ()
  (define line (read-line))
  (unless (eof-object? line)
    (define trimmed (string-trim line))
    (cond
      [(string=? trimmed "") (write-json 'null) (newline) (flush-output)]
      [else
       (with-handlers ([exn:fail? (lambda (e)
                          (write-json (hasheq 'error (exn-message e)))
                          (newline) (flush-output))])
         (define expr (read (open-input-string trimmed)))
         ;; Evaluate with stdout redirected to a throwaway string port so any
         ;; incidental output a rule prints (display/displayln/print) does NOT
         ;; land on the real stdout. Otherwise that stray line is read by the
         ;; bridge as THIS call's JSON response, desyncing every later call by
         ;; one (intermittent wrong/"expected a )" results). Results are RETURN
         ;; values serialized below — never printed — so discarding stdout here
         ;; is semantics-preserving for grid ops.
         (define eval-custodian (make-custodian))
         (when (custodian-memory-accounting-available?)
           (custodian-limit-memory
            eval-custodian
            (* 512 1024 1024)
            eval-custodian))
         (define result
           (dynamic-wind
             void
             (lambda ()
               (parameterize ([current-output-port (open-output-string)]
                              [current-error-port (open-output-string)]
                              [current-input-port (open-input-string "")]
                              [current-environment-variables
                               (make-environment-variables)]
                              [current-command-line-arguments #()]
                              [exit-handler
                               (lambda args
                                 (error 'arc-sandbox
                                        "process exit denied: args=~a"
                                        args))]
                              [current-security-guard arc-candidate-security-guard]
                              [current-custodian eval-custodian])
                 ;; Allocations are charged to a thread's managing custodian,
                 ;; not merely the current-custodian parameter. Running the
                 ;; evaluator in a nested thread makes the 512 MiB cap real.
                 (call-in-nested-thread
                  (lambda () (eval expr))
                  eval-custodian)))
             (lambda () (custodian-shutdown-all eval-custodian))))
         (write-json (serialize result))
         (newline)
         (flush-output))])
    (loop)))
"""


def _flatten_for_transport(sexpr: str) -> str:
    r"""Collapse a (possibly multi-line) s-expression to one transport line.

    The Racket boot loop reads ONE line per eval, so the program must be a
    single line. A naive ``sexpr.replace("\\n", " ")`` corrupts any program
    that contains a ``;`` line comment: once newlines become spaces, the
    comment runs to the end of the (now single) line and eats every closing
    paren after it, yielding ``read: expected a )``. Strip ``;`` line comments
    BEFORE flattening (Racket ignores them anyway, so this is
    semantics-preserving), while leaving ``;`` inside string literals intact.

    Two ``;``-bearing forms are NOT line comments and are passed through
    verbatim: ``#;`` datum comments and ``#\`` char literals (e.g. a literal
    semicolon character). Block
    comments (``#| |#``) are also left untouched — all of these are explicitly
    delimited and survive flattening without swallowing code.
    """
    out = []
    in_string = False
    escape = False
    in_line_comment = False
    n = len(sexpr)
    i = 0
    while i < n:
        ch = sexpr[i]
        if in_line_comment:
            # A line comment ends at the newline; drop the comment body and the
            # newline, emitting a single separating space so adjacent tokens on
            # the next line don't fuse.
            if ch == "\n":
                in_line_comment = False
                out.append(" ")
            i += 1
            continue
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "#" and i + 1 < n:
            nxt = sexpr[i + 1]
            if nxt == "\\" and i + 2 < n:
                # Character literal #\<c> (e.g. #\; or #\newline-name) — emit the
                # `#\` and the literal char verbatim so its `;`/space isn't read
                # as a comment/separator.
                out.append(sexpr[i:i + 3])
                i += 3
                continue
            if nxt == ";":
                # Datum comment prefix — the `;` here is part of `#;`, not a line
                # comment. Emit `#;` and resume normal scanning.
                out.append("#;")
                i += 2
                continue
        if ch == ";":
            in_line_comment = True
            i += 1
            continue
        if ch == "\n":
            out.append(" ")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


class RacketBridgeError(Exception):
    pass


class RacketUnavailableError(RacketBridgeError):
    """Raised when no executable protected Racket runtime can be resolved."""


class RacketBridge:
    """Manages a persistent Racket subprocess for S-expression evaluation."""

    def __init__(self, prelude_path=None, timeout=10.0, *,
                 max_calls_before_restart=None, startup_timeout=30.0):
        self.prelude_path = prelude_path or _PRELUDE_PATH
        self.timeout = timeout
        # Optional defense-in-depth: transparently respawn the child after this
        # many evals to bound any slow accumulation of subprocess state. None
        # (default) disables it — the stderr drain below removes the known
        # accumulation source, so this is belt-and-suspenders, not required.
        self.max_calls_before_restart = max_calls_before_restart
        self.startup_timeout = startup_timeout
        self._proc = None
        self._call_count = 0
        # Restart accounting, readable by callers that report latency: total
        # child restarts (scheduled + respawn) and whether the most recent
        # eval_text paid startup cost.
        self._restarts = 0
        self.restarted_last_call = False
        self._stderr_tail = deque(maxlen=400)  # bounded ring of recent stderr lines
        self._stderr_thread = None
        self._stdout_buffer = ""   # over-read bytes from os.read kept for the next _read_line
        self._start()

    def _start(self):
        """Spawn the Racket subprocess."""
        # Write boot script to temp file (can't use #lang with -e)
        import tempfile
        self._boot_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.rkt', delete=False,
            prefix=f'arc_bridge_boot_{os.getpid()}_')
        self._boot_file.write('#lang racket\n')
        self._boot_file.write(_BOOT_SCRIPT)
        self._boot_file.flush()
        self._boot_file.close()

        runtime_status = racket_runtime_status()
        if not runtime_status["available"]:
            try:
                os.unlink(self._boot_file.name)
            except OSError:
                pass
            raise RacketUnavailableError(runtime_status["reason"])
        self.racket_binary = runtime_status["resolved_binary"]
        self._proc = subprocess.Popen(
            [self.racket_binary, self._boot_file.name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
            env=_racket_subprocess_env(),
        )
        self._call_count = 0
        # Continuously drain stderr in the background. The boot loop never reads
        # stderr; left undrained, the OS pipe buffer (~64KB) fills and Racket
        # BLOCKS on its next stderr write, wedging the whole bridge. Because
        # stderr is cumulative over the process lifetime, a long-lived bridge
        # that emits even a little stderr per call deadlocks after ~64KB total
        # (observed at ~call 64) while a fresh bridge "works" — exactly the
        # reported degrade-over-time symptom. Draining into a bounded ring keeps
        # the pipe empty AND preserves a recent tail for crash diagnostics.
        self._stderr_tail.clear()
        proc = self._proc
        stderr = proc.stderr

        def _drain():
            try:
                for raw in iter(stderr.readline, ""):
                    self._stderr_tail.append(raw)
            except Exception:
                pass

        self._stderr_thread = threading.Thread(target=_drain, daemon=True)
        self._stderr_thread.start()

        # Send prelude path as first line
        self._proc.stdin.write(self.prelude_path + "\n")
        self._proc.stdin.flush()
        # Readiness handshake: replace a blind sleep with a confirmed round-trip.
        # We eval a known prelude call and block (bounded) until its exact answer
        # comes back. This proves the prelude finished loading AND the read/eval
        # loop is consuming stdin before any real eval is sent — closing the
        # startup-race window where a too-short fixed sleep could desync the
        # first response on a busy host.
        self._in_startup = True
        try:
            self._handshake()
            self._security_canary = self._security_handshake()
        finally:
            self._in_startup = False

    @property
    def runtime_identity(self):
        """Content-bind the executable and prelude used by this live bridge."""

        from .security import POLICY_SCHEMA, policy_sha256

        canary = dict(getattr(self, "_security_canary", {}))
        protected = bool(
            canary.get("filesystem") == "pass"
            and canary.get("network") == "pass"
            and canary.get("subprocess") == "pass"
            and canary.get("environment") == "pass"
            and canary.get("input") == "pass"
            and canary.get("exit") == "pass"
            and canary.get("memory") == "pass"
        )
        bridge_path = os.path.realpath(__file__)
        return {
            "schema": "arc-protected-racket-runtime-v1",
            "backend": "racket",
            "protected": protected,
            "deterministic": True,
            "startup_handshake": "pass",
            "security_canary": canary,
            "security_guard": "deny-filesystem-network-link-v1",
            "evaluation_custodian": "fresh-per-eval-shutdown-before-reply-v1",
            "subprocess_environment": "explicit-allowlist-v1",
            "candidate_environment": "empty-environment-variables-v1",
            "candidate_input": "empty-string-port-v1",
            "candidate_output": "discard-string-ports-v1",
            "candidate_exit_handler": "deny-process-exit-v1",
            "evaluation_resource_limit": "nested-thread-512MiB-v1",
            "candidate_symbol_policy_schema": POLICY_SCHEMA,
            "candidate_symbol_policy_sha256": policy_sha256(),
            "binary_path": self.racket_binary,
            "binary_sha256": _file_sha256(self.racket_binary),
            "prelude_path": os.path.realpath(self.prelude_path),
            "prelude_sha256": _file_sha256(self.prelude_path),
            "bridge_path": bridge_path,
            "bridge_sha256": _file_sha256(bridge_path),
            "boot_script_sha256": hashlib.sha256(_BOOT_SCRIPT.encode()).hexdigest(),
        }


    def _stderr_text(self, limit=4000):
        """Most recent drained stderr, newest-last, capped for messages."""
        text = "".join(self._stderr_tail)
        return text[-limit:]

    def _handshake(self):
        """Confirm the child is up and the prelude is loaded before first eval."""
        sentinel = "(rows '((7 7 7 7 7 7 7 7 7)))"  # prelude fn; unambiguous -> 1
        deadline = time.time() + self.startup_timeout
        try:
            self._proc.stdin.write(sentinel + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise RacketBridgeError(
                f"Racket failed to start (stdin write): {e}\n"
                f"stderr: {self._stderr_text()}")
        # Read response lines until we see the sentinel answer or time out. Any
        # earlier lines (e.g. stray prelude-load output on stdout) are skipped so
        # they cannot desync the first real eval.
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                self.shutdown()
                raise RacketBridgeError(
                    f"Racket startup handshake timed out ({self.startup_timeout}s).\n"
                    f"stderr: {self._stderr_text()}")
            line = self._read_line_timeout(timeout=remaining)
            if line is None:
                continue
            if line.strip() == "1":
                return

    def _security_handshake(self):
        """Prove host-I/O and process-control guards before accepting code."""

        escaped_prelude = json.dumps(os.path.realpath(self.prelude_path))
        escaped_binary = json.dumps(os.path.realpath(self.racket_binary))
        probes = {
            "filesystem": (
                f"(file-exists? {escaped_prelude})",
                "filesystem access denied",
            ),
            "network": (
                '(tcp-connect "127.0.0.1" 9)',
                "network access denied",
            ),
            "subprocess": (
                f'(system* {escaped_binary} "-e" "(void)")',
                "filesystem access denied",
            ),
        }
        receipt = {}
        for name, (expression, marker) in probes.items():
            try:
                self.eval_text(expression)
            except RacketBridgeError as exc:
                if marker not in str(exc):
                    self.shutdown()
                    raise RacketBridgeError(
                        f"Racket {name} security canary failed ambiguously: {exc}"
                    ) from exc
                receipt[name] = "pass"
                continue
            self.shutdown()
            raise RacketBridgeError(
                f"Racket {name} security canary unexpectedly succeeded"
            )

        value_probes = {
            "environment": ('(not (getenv "PATH"))', True),
            "input": ("(eof-object? (read-line))", True),
            "memory": ("(custodian-memory-accounting-available?)", True),
        }
        for name, (expression, expected) in value_probes.items():
            try:
                observed = self.eval_text(expression)
            except RacketBridgeError as exc:
                self.shutdown()
                raise RacketBridgeError(
                    f"Racket {name} security canary errored: {exc}"
                ) from exc
            if observed is not expected:
                self.shutdown()
                raise RacketBridgeError(
                    f"Racket {name} security canary returned {observed!r}; "
                    f"expected {expected!r}"
                )
            receipt[name] = "pass"

        try:
            self.eval_text("(exit 0)")
        except RacketBridgeError as exc:
            if "process exit denied" not in str(exc):
                self.shutdown()
                raise RacketBridgeError(
                    f"Racket exit security canary failed ambiguously: {exc}"
                ) from exc
            receipt["exit"] = "pass"
        else:
            self.shutdown()
            raise RacketBridgeError(
                "Racket exit security canary unexpectedly succeeded"
            )
        return receipt

    def alive(self):
        return self._proc is not None and self._proc.poll() is None

    def __enter__(self):
        """Return the live bridge for use in a ``with`` block."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Always reap the child when leaving a ``with`` block."""
        self.shutdown()
        return False

    def eval_text(self, sexpr: str) -> any:
        """Send an S-expression string to Racket, return the parsed result.

        Raises RacketBridgeError on timeout, subprocess crash, or Racket error.
        """
        # Startup handshake/canary evals are part of _start itself: they must
        # not consult the restart policy (a small max_calls_before_restart
        # would recurse _start -> canary eval -> _start forever), must not
        # clobber the outer call's restarted_last_call telemetry, and a child
        # death here is a startup failure, not a respawnable client call.
        in_startup = getattr(self, "_in_startup", False)
        # Optional belt-and-suspenders restart to bound any slow state drift.
        # Counted like a respawn: callers that time evals must be able to see
        # which calls paid process-startup cost, or a scheduled restart lands
        # in their latency percentiles as a phantom outlier. Workers were
        # excluding these by hand (v13-z WFB-702, 30d3af94d21e WFB-001).
        if not in_startup:
            self.restarted_last_call = False
            if (self.max_calls_before_restart
                    and self._call_count >= self.max_calls_before_restart):
                self.shutdown()
                self._start()
                self._restarts = getattr(self, "_restarts", 0) + 1
                self.restarted_last_call = True

        if in_startup and not self.alive():
            raise RacketBridgeError(
                "Racket child died during the startup handshake/canary probes")
        if not self.alive():
            # RESPAWN instead of bricking. A single timeout used to kill the
            # child and null `_proc`, after which EVERY later eval_text raised
            # "Racket process is not running" — one slow rule permanently
            # bricked a bridge and silently zeroed every candidate behind it.
            # ProgramVerifier.apply already restarts for exactly this reason
            # ("silently zeroed 17/48 candidates"); the two consumers had two
            # policies. An independent audit reproduced the cascade by
            # accident: 8/60 gold tasks "failed" and passed on re-run.
            # Recovery is LOUD and bounded — a respawn that itself fails
            # raises, and we never retry more than once per call.
            print("LOUD: racket bridge was dead at eval_text; respawning "
                  "(a prior call timed out or the child crashed)",
                  file=sys.stderr)
            self._restarts = getattr(self, "_restarts", 0) + 1
            self.restarted_last_call = True
            self._start()
            if not self.alive():
                raise RacketBridgeError(
                    "Racket process is not running and respawn failed")

        # Flatten to a single transport line (Racket reads one line per eval),
        # stripping `;` line comments so they don't swallow the closing parens.
        line = _flatten_for_transport(sexpr).strip()
        if not line:
            return None

        if not in_startup:  # canary probes are not client calls
            self._call_count += 1
        try:
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise RacketBridgeError(
                f"Failed to send to Racket: {e}\nstderr: {self._stderr_text()}")

        # Read response with timeout
        result_line = self._read_line_timeout()
        if result_line is None:
            raise RacketBridgeError(f"Racket timed out ({self.timeout}s) evaluating: {line[:200]}")

        # Parse JSON response
        try:
            result = json.loads(result_line)
        except json.JSONDecodeError:
            raise RacketBridgeError(f"Invalid JSON from Racket: {result_line[:500]}")

        # Check for error
        if isinstance(result, dict) and "error" in result:
            raise RacketBridgeError(f"Racket error: {result['error']}")

        return result

    def _read_line_timeout(self, timeout=None):
        """Read one line from stdout with timeout.

        stderr is drained by the background thread, so on death/timeout we read
        the captured tail via `_stderr_text()` rather than touching the pipe
        directly (which would race the drainer thread).
        """
        if timeout is None:
            timeout = self.timeout
        # POSIX path: avoid a helper thread blocked in TextIO.readline().  Also
        # avoid TextIO.readline() itself after select(): a pipe can become
        # readable with only a partial line, and TextIO.readline() would then
        # block past the requested timeout.  Read bytes until a newline is
        # actually present, preserving any over-read bytes for the next call
        # (reviewer next352). The timeout path still kills AND reaps the wedged
        # evaluator (reviewer nedxt259 select_timeout_fail_closed) — bulk audits
        # must fail closed, not hang or zombie.
        if os.name == "posix":
            import select

            deadline = time.time() + timeout
            while True:
                buf = getattr(self, "_stdout_buffer", "")
                if "\n" in buf:
                    line, rest = buf.split("\n", 1)
                    self._stdout_buffer = rest
                    return line.strip()
                remaining = deadline - time.time()
                if remaining <= 0:
                    proc = self._proc
                    self._proc = None
                    try:
                        proc.kill()
                        proc.wait(timeout=1)
                    except Exception:
                        pass
                    return None
                ready, _, _ = select.select([self._proc.stdout], [], [], remaining)
                if not ready:
                    proc = self._proc
                    self._proc = None
                    try:
                        proc.kill()
                        proc.wait(timeout=1)
                    except Exception:
                        pass
                    return None
                try:
                    chunk = os.read(self._proc.stdout.fileno(), 4096)
                except OSError:
                    chunk = b""
                if not chunk:
                    stderr = self._stderr_text()
                    self._proc = None
                    raise RacketBridgeError(f"Racket process died. stderr: {stderr[:1000]}")
                self._stdout_buffer = buf + chunk.decode(errors="replace")

        result = [None]

        def reader():
            try:
                result[0] = self._proc.stdout.readline()
            except Exception:
                pass

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            # Timeout — kill and reap before returning.  Leaving a killed but
            # unreaped Racket child can make CLI smoke tests appear to die by
            # signal under harness cleanup.
            proc = self._proc
            if proc is not None:
                try:
                    proc.kill()
                    proc.wait(timeout=1)
                except Exception:
                    pass
            self._proc = None
            return None

        line = result[0]
        if line is None or line == "":
            # Process died
            stderr = self._stderr_text()
            self._proc = None
            raise RacketBridgeError(f"Racket process died. stderr: {stderr[:1000]}")

        return line.strip()

    def define_grid(self, name: str, grid_data: list):
        """Define a grid variable in Racket's namespace."""
        # Serialize grid as a Racket literal: '((1 0 2) (3 4 5))
        rows = " ".join(
            "(" + " ".join(str(v) for v in row) + ")"
            for row in grid_data
        )
        self.eval_text(f"(define {name} '({rows}))")

    def define_value(self, name: str, value):
        """Define a simple value in Racket's namespace."""
        if isinstance(value, bool):
            rkt = "#t" if value else "#f"
        elif isinstance(value, int):
            rkt = str(value)
        elif isinstance(value, float):
            rkt = str(value)
        elif isinstance(value, str):
            rkt = f'"{value}"'
        elif isinstance(value, list):
            rkt = "'" + self._serialize_list(value)
        elif value is None:
            rkt = "'()"
        else:
            rkt = f"'{value}"
        self.eval_text(f"(define {name} {rkt})")

    def _serialize_list(self, lst):
        """Serialize a Python list as a Racket list literal."""
        parts = []
        for item in lst:
            if isinstance(item, list):
                parts.append(self._serialize_list(item))
            elif isinstance(item, bool):
                parts.append("#t" if item else "#f")
            elif isinstance(item, (int, float)):
                parts.append(str(item))
            elif isinstance(item, str):
                parts.append(f'"{item}"')
            else:
                parts.append(str(item))
        return "(" + " ".join(parts) + ")"

    def shutdown(self):
        """Terminate and reap the persistent Racket subprocess.

        In smoke-test runs the bridge child can stay in its read/eval loop after
        Python closes stdin.  Reap it explicitly so command-line tools do not
        leak a CPU-spinning `racket` process or appear to die by signal when the
        harness later cleans up lingering children.
        """
        proc = self._proc
        stderr_thread = self._stderr_thread
        self._proc = None
        self._stderr_thread = None
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2)
            else:
                proc.wait(timeout=0)
        except Exception:
            try:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                pass
        # The stderr drainer blocks in BufferedReader.readline().  Terminating
        # the child closes the pipe's writer, so give the thread a chance to
        # observe EOF and release the BufferedReader lock before closing the
        # parent stream.  Without this join, long-lived bridges could hang
        # forever in stream.close() after a few hundred evaluator calls.
        if (
            stderr_thread is not None
            and stderr_thread is not threading.current_thread()
            and stderr_thread.is_alive()
        ):
            stderr_thread.join(timeout=2)
        # Closing these buffered streams during interpreter shutdown is what
        # produced `Fatal Python error: _enter_buffered_busy ... at
        # interpreter shutdown, possibly due to daemon threads` -> SIGABRT
        # (exit 134, core dumped), reproduced 3/3 via
        # ArcExecutor.__del__ -> close() -> shutdown(). The daemon `_drain`
        # thread can hold the BufferedReader lock. The child is already
        # terminated above and the OS reclaims the fds, so skipping the
        # explicit close costs nothing at finalization.
        if not getattr(sys, "is_finalizing", lambda: False)():
            streams = [proc.stdin, proc.stdout]
            # If a pathological platform still has the drainer alive, do not
            # contend for its buffered-reader lock.  The daemon owns the final
            # EOF read and the file object is reclaimed after it exits.
            if stderr_thread is None or not stderr_thread.is_alive():
                streams.append(proc.stderr)
            for stream in streams:
                try:
                    if stream is not None and not stream.closed:
                        stream.close()
                except Exception:
                    pass
        boot_file = getattr(self, "_boot_file", None)
        if boot_file is not None:
            try:
                os.unlink(boot_file.name)
            except Exception:
                pass

    def close(self):
        """Discoverable alias for :meth:`shutdown`."""
        self.shutdown()

    def __del__(self):
        # NEVER touch buffered I/O from __del__ during interpreter shutdown.
        # `shutdown()` closes proc.stdout/stderr, and the daemon `_drain`
        # thread may hold those buffer locks; CPython then dies with
        #   Fatal Python error: _enter_buffered_busy: could not acquire lock
        #   for <_io.BufferedReader ...> at interpreter shutdown
        # -> SIGABRT, exit 134, core dumped. Reproduced 3/3 with no GPU
        # involved, via ArcExecutor.__del__ -> close() -> bridge.shutdown().
        # At real interpreter shutdown the OS reaps the child anyway, so the
        # only thing lost by skipping is tidiness; explicit shutdown() calls
        # (the normal path) still reap properly.
        if getattr(sys, "is_finalizing", lambda: False)():
            return
        try:
            self.shutdown()
        except Exception:
            pass

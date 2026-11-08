# Confined memory workspace helper

This stdlib-only helper let the review proceed after the initial filesystem reported zero available bytes and normal extraction failed. It keeps one explicitly confined process alive so independent clients can run bounded commands against the same private tmpfs. It is a command transport, not a sandbox: all clients with socket access can request arbitrary commands within the server's privileges.

## Launch inside an explicit sandbox

The example below requires Linux user namespaces and bubblewrap. Use a fresh writable host directory for the control socket and exported results. Do not launch the server unrestricted to work around an unavailable sandbox.

From the returned packet's root, after extracting checks/tooling:

```sh
review_tools=$(realpath checks/tooling)
review_state=$(mktemp -d "$PWD/review-state.XXXXXX")
bwrap --unshare-user --unshare-pid --unshare-net --uid 0 --gid 0 \
  --ro-bind / / --tmpfs /tmp --dev /dev \
  --ro-bind "$review_tools" /review-tools \
  --bind "$review_state" /review-state --chdir /tmp -- \
  python3 -u /review-tools/memory_workspace.py server \
  --socket /review-state/workspace.sock
```

Keep that process alive. The root filesystem is read-only, /tmp is private and writable, network and process namespaces are isolated, and only review_state is a writable host export. Read access to the host root still exists; do not treat this example as a confidentiality boundary. The example intentionally omits a new /proc mount because this environment rejected it. The /dev mount is needed by subprocess DEVNULL.

Use a second terminal with the same review_tools and review_state values:

```sh
python3 "$review_tools/memory_workspace.py" client \
  --socket "$review_state/workspace.sock" <<'JSON'
{"argv":["python3","-c","from pathlib import Path; p=Path('/tmp/work'); p.mkdir(exist_ok=True); print(p)"],"cwd":"/tmp","timeout":30}
JSON
```

Extract the already-inspected input packet to /tmp/work through this channel, run its native review.py commands there, and export only the native return ZIP into /review-state. The original upload can be read from its read-only host path. Runtime payloads still use the native wrapper's WORK/repo working directory.

Before shutdown, copy every deliverable you need out of the private tmpfs. Then send:

```sh
python3 "$review_tools/memory_workspace.py" client \
  --socket "$review_state/workspace.sock" <<'JSON'
{"op":"shutdown"}
JSON
```

## Protocol and bounds

Each client supplies one JSON object. Execution accepts argv as a nonempty string array, cwd as an absolute existing directory, and timeout as a positive number (default 120 seconds, maximum 600). It uses shell=False. Set per-command environment variables by explicitly invoking env in argv if needed. Control requests are exactly {"op":"ping"} or {"op":"shutdown"}.

The response records returncode, stdout, stderr, timed_out, output_limit_exceeded and elapsed_seconds. Read those fields: a successful client transport does not mean the command passed. Requests and combined retained output are bounded at 8 MiB each. A timeout or output flood kills the command's process group. The server defaults to four concurrent jobs, creates a mode-0600 socket, and refuses to reuse an existing socket path. Clients must enforce their own source approval and task scope.

This helper does not reserve memory or guarantee tmpfs capacity. Memory contents disappear when the sandbox exits. It makes no Racket-authority, rule-safety, packaging or training-admission decision.

## Retained verification

Run `python3 checks/tooling/test_memory_workspace.py` from the packet root. The five tests cover socket permissions/ping, stdout/stderr/working directory/environment, malformed request/timeout handling, process-group termination, and output-flood termination. The retained tests.log reports five passes in 0.427 seconds; tests-command.json records the command and exit status.

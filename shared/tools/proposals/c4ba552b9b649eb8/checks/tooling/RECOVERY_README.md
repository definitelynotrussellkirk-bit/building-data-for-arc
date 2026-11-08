# ARCpuzzles packet recovery helper

This is a small, Python-standard-library-only recovery tool for the issued
`WORK/` packet layout. It keeps the original ZIP as the immutable source and
does not edit the issued manifest, outer entry files, workflow modules, or task
sources. It is an explicit infrastructure adaptation. Its development tests and
its later use in the actual assigned review are distinguished below.

## Validation performed for this deliverable

From `WORK/`, run the retained standalone synthetic test suite:

```sh
python -B -m unittest discover -s checks/tooling -p test_packet_recovery.py -v
```

The 24 tests cover ZIP traversal, duplicate members, ZIP and local symlinks,
corrupt bytes, exact-member hydration, preservation of local edits, durable seed
retries, adoption of existing/pending assignments, conflicting seeds, completed
draw resumption, native seed journal adoption/conflicts and strict schemas,
ENOSPC hydration retries without capacity preflight, ZIP fallback for absent
unchanged sources, corrupt/edited fallback rejection, and preservation of missing
assigned-candidate rejection.

During initial helper development, the original ZIP's manifest metadata was
inspected, and the original
`review_full_return.py` hash and exact AST guard shape were checked. No source
archive extraction, real assignment draw, or real seed commitment was performed
by the helper developer at that stage. The full original ZIP verification and
real review integration occurred subsequently, as recorded below. Synthetic
regression results are retained in `checks/tooling/recovery-tests.log`.

## Actual review integration in this session

`checks/tooling/original-archive-verification.json` records verification of
103,285 hashed files totaling 1,691,152,953 uncompressed bytes with zero hash
mismatches and a canonical manifest. The original ZIP is 343,271,382 bytes;
its SHA-256 is
`ff7d9140462c8e1ca65bed371db64ec84353f6a59b75c7bb35ec181804a3a3a0`.
This receipt concerns the original ZIP bytes. Its “no assignment drawn” scope
describes the verification moment, before the later draw.

The recovery helper subsequently bootstrapped verified workflow files,
committed one durable seed, hydrated the selected source closure, and invoked
the unchanged stock draw with that explicit seed. The resulting assignment is
`review-cd852f8d87a7ba3f`, selected task `7fc158ab7b70`. The issued manifest,
outer entry files, and repository workflow sources were not rewritten for this
adaptation. The optional native early-seed patch remains separately proposed.

The real review then installed the pinned Racket runtime and selected Python
environment, completed the blind solve, ran the original before battery
(11/12 stages; strict seed handling failed), implemented the selected production
seed fix and bounded prototype, ran the after battery (12/12 stages), and
completed both assigned audits. The relevant task evidence is under
`checks/before/`, `checks/after/`, `checks/parametric/`, and `checks/audit/`;
`checks/tooling/final-code-review.md` separately records the independent selected
implementation review and its limits. Those review results are distinct from
the recovery helper's 24 synthetic tests.

At the time of this documentation update, the optional sparse package command
has not run on this real reviewer return. Its AST guard compatibility was
checked and its candidate/deletion semantics have synthetic regression
coverage, but no successful real return packaging is claimed here. A complete
local extraction and a passing stock full-local `review.py verify` are also not
claimed. Original-ZIP hash verification and selected local hydration have
different scopes from that full-local command.

## Commands

All options before the subcommand apply to every command. `--outer` names the
new outer directory that will contain the unchanged issued entry files and
`WORK/`. Use a filesystem with enough free space for the review, baseline,
execution runtime, Racket, and check evidence. The uploaded ZIP path is the
default `--zip` value; specify it explicitly after moving this helper.

```sh
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered verify-zip
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered bootstrap
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered commit-seed
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered hydrate-main --plan-only
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered hydrate-main
```

`verify-zip` streams every manifest source file and both outer entry files,
checking their SHA-256. It does not extract them. Its output explicitly refers to
the original ZIP, not to stock `review.py verify` on a sparse working directory.

`bootstrap` extracts only the issued manifest, entry files, Python workflow
package, and top-level packet Python scripts. It does not extract task sources
or task data. It refuses to overwrite an existing changed file.

`commit-seed` durably records exactly one 32-byte OS-random seed in
`WORK/.review/portable-seed.json`, bound to the unchanged manifest's SHA-256. It
uses a filesystem lock, fsync, and atomic replacement. It adopts a seed already
present in a completed assignment, pending draw, or the optional native
`.review/main-draw-seed.json` journal instead of generating another one, and
rejects conflicts. Portable/native journal schemas and lowercase 64-character
seed encoding are validated strictly. It does not perform task selection. Preserve this
file across every retry; do not delete it to obtain a new assignment.

**`hydrate-main --plan-only` also commits the single seed.** It then uses the
original selection function and baseline path helper to report required source
and baseline bytes. It does not complete a draw. Repeating it uses the same seed.

`hydrate-main` uses that same committed seed, verifies and hydrates the exact
main-task baseline and selected question, then invokes the original `draw_main`
with the explicit saved seed. The original immutable-baseline copying and
pending-journal behavior remain in force. Size estimates are informational only:
the command does not query or gate on available disk capacity. Actual writes
determine success; an OS write failure preserves the committed seed for retry.
The estimate does not include later execution, blind-solve, audit, Racket, or
evidence costs. A completed existing assignment
returns idempotently without replacing task edits.

For a separately determined exact runtime closure or an audit target, hydrate
only explicit manifest members:

```sh
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered hydrate repo/catalog/puzzles.jsonl repo/catalog/runtime_files.json repo/catalog/authority_files.json
```

Hydration rejects unsafe/unknown names, symlink ancestors, duplicate ZIP members,
hash mismatches, and existing changed files. It streams to a temporary file,
verifies the complete bytes, fsyncs, and publishes without overwriting a late
existing destination. A corrupt or interrupted copy is never published as a
complete source file.

## Optional sparse return packaging

After satisfying the original duties and retaining all selected baseline members:

```sh
python -B recovery/packet_recovery.py --zip /path/request.zip --outer /path/recovered package --out /absolute/path/review_response.zip
```

This explicitly creates a private compiled copy of the original
`build_full_return` function. It recognizes exactly one AST expression: the
global unchanged-repository-source guard nested in the manifest loop and its
`path not in candidates` condition. It replaces only that expression with a
ZIP-aware guard. It does not monkeypatch the original module or alter any file.
The CLI verifies the original packager source against the issued manifest and
ZIP before compiling the private copy. Unrecognized guard shapes fail closed.

For each noncandidate source, an existing local file must still be regular and
match its issued SHA-256. An absent local file is accepted only after streaming
and verifying that exact original ZIP member against the same manifest digest.
Assigned candidates remain governed by the original candidate/deletion check;
their disappearance is rejected. Frozen baseline, allowed edit scope, solve
exposure, evidence, report, and static return-ZIP validation remain original.

This adaptation cannot authorize helper/core edits that the original return
format rejects. Keep infrastructure changes in this separate deliverable and
document their use in reviewer evidence.

## Current infrastructure limit

The observed shared 32 GiB overlay repeatedly filled during extraction. The
common selected runtime mapping alone contains 252 files totaling 83,863,042
uncompressed bytes, before selected generator/rule sources. The original runtime
builder physically copies its inputs; it does not use symlinks. The canonical
ledger is 21,618,506 bytes, the manifest is 18,758,107 bytes, and the offline Racket
archive is 34,026,024 bytes before expansion. Main baseline copies and later
check/runtime/evidence files add further space.

The helper makes source identity and seed recovery concrete; it does not create
free disk space or replace the required test, blind-solve, audit, and review
gates. Do not present sparse bootstrap success as completion of those gates.
Capacity reports can disagree with actual writable capacity, including reserved
filesystem blocks available to the current user. Attempt the authorized writes
and preserve real operation failures; do not reject work using capacity preflight.

Implementation uses Linux/Unix `fcntl.flock`, matching this packet's existing
draw code. General Windows support is outside this recovery's scope.

## Optional proc-fd source transport for stock replay logic

This bounded extension supports an original source ZIP held on an open Linux
descriptor during the session. Stock `replay_return` calls
`Path(source_zip).resolve()`, which dereferences `/proc/self/fd/N` to a deleted
memfd target that cannot be reopened. The explicit transport adapter accepts
only `/proc/self/fd/N`. It verifies issued `review_replay.py` against the original
manifest and ZIP, then compiles a private function copy changing exactly one
AST field: the source path's `resolve` method becomes `absolute`.
The return ZIP still uses `Path(return_zip).resolve()`; every other stock replay
statement and validator remains unchanged. Malformed/ambiguous source shapes,
changed module bytes, and ordinary non-fd source paths are rejected.

From `WORK/`, the CLI is:

```sh
python -B checks/tooling/packet_recovery.py --zip /proc/self/fd/N --outer /path/review replay --return-zip /path/return.zip --compare-work /path/review/WORK --out /path/fresh-replay --runtime-closure
```

The descriptor must already be open in that process. The equivalent API is
`replay_return(packet, outer, return_zip, compare_work, out, runtime_closure=True)`.
The helper neither obtains descriptors nor contacts the session's source
transport service. Original archive inventory/type checks, official return
validation, extracted hashes, ZIP hashes, complete Git patch inventory, exact
Git root, patch application, and every changed-byte comparison run unchanged.
This is a transport adaptation, not a verification relaxation or an unmodified
stock invocation. Replay itself runs no tests; fresh runtime/tests are separate.

Five new synthetic regressions bring the helper suite to 29 tests. They cover a
tiny real memfd source, preserved return symlink resolution and validator calls,
malformed/ambiguous assignment rejection, altered issued-module rejection, and
non-fd refusal. The original 24-test result above records development before
this extension; the current run is retained separately in
`checks/tooling/replay-adapter-tests.log`. The adapter author did not run an
actual reviewer replay during extension development; later root integration
and fresh tests require their own receipts. Use ordinary stock replay directly
when a stable source-ZIP file is available.


## Completed integration addendum

The optional package adapter built and statically validated the actual review
return. The explicit source-fd replay adapter applied its exact seven-file task
delta in a fresh 375-file declared runtime closure out of 103,286 original
archive files. Every changed byte matched. All 61 selected tests passed in that
fresh checkout's new Python environment and separately installed pinned Racket.
See `../fresh/verification.json`, `../fresh/replay.json` and the exact environment
commands. The official replay receipt itself correctly says tests_run=false;
the separate verification companion records the subsequent tests.

The final helper suite has 29 passing tests, including five transport-adapter
regressions. Initial development statements above describe that earlier stage,
not the final integration state. No full-local stock verify, complete corpus
extraction, training admission or universal portability is claimed.

# 44e865b6a43e: selected authority formatting divergence

**Conclusion:** the proposed selected-base `target_code` alignment is within the
actual return contract. The mismatch is whitespace-only. The supported proposal
and two non-applying patch checks passed. No authority, catalog, shared tool,
assignment, baseline, or control file was changed by this investigation.

## Exact cause

The baseline authority check compares active canonical `program_solution` and
selected `racket_target.target_code` by exact text. It found two exact groups,
one whitespace-normalized group, and passing execution parity over both texts.
The current source inspection confirms:

| Measurement | Selected target | Canonical program |
| --- | ---: | ---: |
| UTF-8 bytes / ASCII characters | 745 | 1,539 |
| Lines | 1 | 29 |
| Space characters | 126 | 892 |
| LF characters | 0 | 28 |
| Non-whitespace characters | 619 | 619 |
| Restricted-reader tokens | 281 | 281 |

The canonical presentation therefore adds 794 whitespace bytes: 766 net spaces
and 28 LF characters. Normalized text and reader-token sequences are identical.
The normalized rule hash stays `de38c98a1856`. The exact selected source hash is
`de38c98a18568a2fc509a998ce7bc154fb797ff615dd7ec5367ae9d3178e2443`;
the canonical text hash is
`f0df22d0b5156b7dca09f4aca449961861532a87b4e1d17073aa2703383eddf3`.

## Proposed change

`selected-authority-proposal.json` is the public command's unchanged, hash-bound,
non-applying proposal. It proposes one file:

`repo/shared/data/base/solutions/training/2601afb7__44e865b6a43e.json`

Only `/racket_target/target_code` changes, receiving the exact canonical string.
The parsed JSON otherwise stays identical, archival `raw_code` stays identical,
and the canonical ledger is unchanged. Whole-file hashes are:

- Before: `1fa0cdd94b60e36b9c55c46b4170d0d4977240cf1961a62e340cdda956e9c9d7`.
- Proposed: `b8656806ef5054599a4e8291a235745334114b391435075d133843577cdf617d`.

`selected-authority.patch` uses repository-root `shared/` paths.
`return-scope.patch` uses WORK-root `repo/` paths and was produced by the active
return builder's own `_diff` helper. Both are optional patches, not applications.

## Return scope evidence

`START-HERE.md` lines 71–74 describes shared paths as runtime/reference internals
to keep intact. The more specific executable return contract explicitly admits
selected task data changes:

1. `WORK/ASSIGNMENT.json` includes this exact base JSON and the canonical ledger
   in `baseline_sha256`. Both current files still match those baseline hashes.
2. `WORK/package_return.py` lines 7–9 imports the live
   `repo/src/arcpuzzles/review_full_return.py` builder.
3. That builder's `_allowed`, lines 34–37, permits the canonical ledger and
   `repo/shared/data/base/` paths included in the assignment baseline.
4. Its build loop, lines 376–398, includes baseline paths as candidates and
   enforces this allowlist. Canonical changes must preserve row count and modify
   only the selected rule task (lines 41–49 and 396–397).
5. Other shared sources remain protected by lines 399–413. Read-only tests
   rejected an unlisted base path, the authority catalog, the shared checker,
   and the authority-sync tool source. `_patch_paths` accepted the exact
   proposed WORK-root patch and identified only the selected base JSON.

These contracts allow this narrow field alignment without changing the scope
rules themselves. Source hashes and exact excerpts are retained in
`diagnostic.json`.

## Verification and limits

- The saved public proposal exactly equals a fresh read-only proposal.
- Both patch formats passed `git apply --check --no-index`, exit 0.
- JSON field isolation, preserved archival code, identical reader tokens,
  baseline identity, scope admission, and unchanged protected source hashes
  passed the assertions in `diagnose_authority.py`, exit 0.
- The retained baseline reports execution parity PASS for 3 training and 1 test
  canonical pairs for each exact source. This investigation did not rerun those
  executions or apply a live change.
- Fresh `authority_sync` and `rule_smoke` checks remain the parent's next step
  after any application. This report does not claim that a live authority check
  is fixed before applying the proposal.

The supported `authority-sync --apply` implementation creates recovery files
under `repo/var/review/authority-sync/` (`authority_sync.py`, line 219 onward).
Those new repository paths are outside this packet's return allowlist. The
prepared field-only patch lets the parent apply the reviewed source change
without generating those extra repository artifacts. No apply command was run
here; the parent owns that decision.

Commands and exit codes are in `commands.json`. The repository has no `.git`
directory: a read-only `git status` attempt exited 128, so the source-preservation
checks use the assignment/proposal SHA-256 pins. An initial attempt to read
`ASSIGNMENT.json` at the outer root exited 1; the actual contract was then found
and read at `WORK/ASSIGNMENT.json`. Neither inspection error affected the tests.

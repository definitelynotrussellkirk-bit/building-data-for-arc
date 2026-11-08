# Placement

| Content | Authoritative home |
|---|---|
| Generator implementation, summary, notes, workspace, evidence, and focused tests | `generators/<id>/` |
| Query metadata, original-ID aliases, and runtime path mappings | `catalog/` |
| Public Python API, CLI, HTTP service, generation, checks, and review operations | `src/arcpuzzles/` |
| Common generator helpers, Racket reference runtime, and loading primitives | `shared/runtime/` |
| Inherited linters, quality gates, and review helpers | `shared/tools/` |
| Inherited common regression tests | `shared/tests/` |
| Canonical puzzles, archival rule authorities, source puzzles, approval and notes ledgers | `shared/data/` |
| Review requests, assignments, incoming returns, and dispositions | `REVIEW/` |
| Executable DSL manual | `GUIDE/` |
| Public-interface regression tests | `tests/` |
| Maintained guides and extraction provenance | `docs/`, `docs/migration/` |
| Generated datasets, local checks, caches, and scratch work | ignored `var/` |
| Distribution packages and build staging | ignored `build/`, `dist/` |

Each generator owns its selected `generator.py`. Put design decisions and
findings in `notes.md`, experiment in `workspace/`, and retain review evidence in
`evidence/`. A workspace draft is never selected automatically. Shared behavior
belongs in `shared/` instead of being duplicated across generator homes.

## Generator notes and review retention

**Owner direction October 7: keep useful current state, not a historical ledger.**
Raw return ZIPs and expansions are temporary intake. After triage, extract useful
material into its owning generator, verify it independently of the archive, and
remove managed raw copies and cumulative transport history.

`arcpuzzles get ID` exposes `notes` from the single editable `notes.md` (the old
`working_notes` field is a compatibility alias). List metadata includes
`notes_path`, `review_notes_path`, `counterexamples_path`, and `audit_unresolved`.

- **notes.md:** the concise current rule, assumptions, limits, open findings and
  decisions. Keep a relevant reversal as prior choice → current choice, reason
  and evidence. Do not append old review narratives or repeated successful logs.
- **counterexamples/ and tests/:** minimal reproducible witnesses and focused
  regressions. Bind useful audit reproductions to the audited target and source,
  not to the return's repair target. Keep proposals separate from selected code.
- **evidence/review_index.json:** `arcpuzzles-task-review-current-v1`, containing
  the selected approval identity and actionable audits, with each finding's
  source hash, current resolution, reason and task-local asset manifest. No copied
  DECISIONS/REVIEW history, archive paths, solve logs or disposition event stream.
- **Audit status:** explicit current status lives with the finding. Source edits,
  generator acceptance and generic audit acceptance never resolve an audit.
  Unknown legacy findings remain `needs_triage`; old-source findings remain
  actionable. Explicitly `resolved`/`no_issue` findings leave the current list.
  The explicit status command retains one bounded assessment in `notes.md`,
  including audited bytes, evidence basis, original finding and current reason.
  A later assessment replaces only that generated section; surrounding author
  notes remain. Reopening the same finding updates its displayed disposition.
  This summary is not a fresh check or a cumulative closed-audit ledger.
  Reopening after compaction requires a concrete source-bound finding and evidence.
- **REVIEW/suggestions.json:** `arcpuzzles-tool-requests-v1`, one current row per
  request with its text, source identity, latest status and reason. Separate
  requests retain stable IDs; there is no cumulative event history. Replaying
  unchanged intake cannot overwrite a direct edit to the current request list.
  Explicitly cited reusable prototypes live in `shared/tools/proposals/<id>/`,
  linked by a hash-checked `assets_manifest` on that request. Keep the patch,
  reproducer and supporting evidence together; exclude copied runtime trees.
  See [the current tool index](../shared/tools/README.md) and each request's
  `owner_tool_review` for tested, integrated, static-only or unselected status.
  These files are passive proposals until a maintainer reviews and implements
  them. Packaging and archive disposal check their hashes without executing them.
  Cite a tool's full `checks/<folder>/` path to retain its authored files,
  tests and fixtures together; custom folder names are supported. Prefer full
  paths in each audit section. A quoted relative receipt name is resolved within
  that audit's target; ambiguous names or names resolving only to another target
  stop disposal until clarified. Put the exact `checks/...` file path in the
  current `review feedback --reason` or `review audit-status --reason`; the
  original reviewer text stays unchanged and audit status remains explicit.
  For a bare `generator.py` mention that describes source code, clarify it with
  `repo/generators/<audited-id>/generator.py` in the current audit reason.
  Task-local source snapshots used as evidence still require an unambiguous
  `checks/` path; another task's snapshot cannot supply the audited source.
  A verification receipt that reuses the native gzip-index schema is retained
  only when its explicit expanded-member inventory identifies one real nonempty
  index and exactly that index's payload closure. The archive count, paths,
  compressed bytes and restored bytes are checked independently; the receipt's
  reported success does not grant qualification or approval.
  A synthetic-only compatibility receipt with the exact supported observation
  fields and no inventory/path fields is retained as passive metadata. It adds
  no verified archive or dependency; real indexes and payload hashes are still
  checked separately, regardless of the receipt's reported success.
  Copied runtime trees are excluded. Known check
  reports keep results, errors and task-source bindings while replacing unrelated
  runtime inventories with their original hash and explicit selection counts.
  Selected `arc-review-evidence-archive-v1`, `review-large-evidence-v1` and
  `arcpuzzles-evidence-gzip-v1` indexes also retain their listed compressed files
  beside the index in each task/proposal home. Disposal verifies compressed and
  decompressed sizes and SHA-256 hashes without running supplied restore scripts. Missing, corrupt,
  conflicting or unsafe dependencies stop disposal. Other index formats remain
  ordinary evidence and require explicit dependency citations.
  The first two schemas name complete `checks/` transport members. The third
  names files relative to its own manifest directory; same-named files in another
  bundle cannot satisfy it. Its exact `path` → `path.gz` mapping and file/directory
  collision checks are preserved.
- **Useful authored solve data and approval:** retain task-owned source-bound
  data and compact necessary approval records. Correctness claims stay reported
  unless independently verified. Retention never admits data to training.

Fresh returns still use the candidate/check/integrate workflow. The inbox overlays
fresh pending returns on current task state; it does not recreate old history.
Processed receipts can be marked `retention_status: extracted` during cleanup,
then removed with their assignment directories after the retention gate passes.
Both audits from each return must be considered before processing is complete.

```bash
arcpuzzles list --audit-unresolved --format json
arcpuzzles review audit-status GENERATOR_ID --return-id 'review-ID:v0001' \
  --status resolved --reason 'SOURCE_SHA and focused test PATH verify the repair.'
arcpuzzles review compact          # preview retained/discarded material
arcpuzzles review compact --apply  # verified extraction, then managed cleanup
```

The compaction gate keeps current notes/decisions, useful proposed patches,
actionable audits and their minimal reproductions, focused tests, compact
source/rule-bound approvals, and unique useful solve evidence. It verifies kept
hashes and relocated consumers with archives absent before deletion. Keep an
unclassified or unextracted source intact until its disposition is explicit.
Discard repeated green logs, copied runtime trees, stale narrative ledgers and
redundant transport archives after that gate passes. User-owned originals outside
the managed review storage are not part of managed cleanup.

`review notes-migrate` only previews/compacts metadata and legacy indexes; it does
not extract archive assets or establish disposal readiness. The current-state
helpers accept legacy records as migration input; packet and catalog readers
consume the compact schema directly after migration.

Public commands copy the needed local library into an ordinary working directory
with the inherited tools' original layout (`puzzle_generators/`, `scripts/`,
`arc_repl/`, and `data/`). This preserves the original code without symlinks or
sibling imports. Edit authoritative files above and prepare a new runtime to
verify them. Edits in a disposable runtime do not change the selected library.

`catalog/runtime_files.json` maps authoritative files to execution paths.
`catalog/authority_files.json` selects task-local archival rules. Per-runtime
manifests record the actual copied hashes; original extraction provenance lives
in `docs/migration/import-manifest.json`.

If one generator imports another generator's helper, declare the helper's
generator ID in its catalog row's `runtime_dependencies` list. Selected runtime
snapshots copy the transitive closure once, record `dependency_task_ids` and all
source hashes, and include those bytes in generation source identity. Unknown or
malformed declarations fail before source copying. This packages a dependency;
it does not grant its generator approval or add it to a sampling pool.

Training experiments belong in ARC2train. Promoted model candidates, inference,
and competition packaging belong in ARC2model. Consumers can install a pinned
ARCpuzzles wheel or receive exported data; they must not depend on a neighboring
source checkout. Retain source identities, seeds, rule hashes, review evidence,
and family/split lineage with exported data. Keep reference answers/programs
separate from model-visible evaluation challenges.

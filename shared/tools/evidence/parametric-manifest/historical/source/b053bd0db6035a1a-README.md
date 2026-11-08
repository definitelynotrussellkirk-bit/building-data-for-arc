# Reviewer tools: current use and disposition

The request list is [REVIEW/suggestions.json](../../REVIEW/suggestions.json). Each code-bearing proposal has one current `owner_tool_review`: exact reviewed files, selected source when applicable, check scope and remaining work. This page is the current index, not a cumulative intake log.

For a browsable view, run `arcpuzzles review inbox` and open
`var/review/full-inbox/index.html`. Tool requests are collapsed by status with
links to generator notes and retained proposal evidence. Exact repeated text is
shown once within a status; each request keeps its own ID, reason and review.
Expand **Retained files** to open the authored scripts, patches, fixtures and
tests directly. Their request identity and stored hashes are checked while the
view is built; missing or changed inventories remain visible as unavailable.
**Implementation sources and review files** links selected code and recorded
tests. It states whether current source bytes match the recorded review hash;
a changed source is not covered by the earlier test result. Missing local run
receipts are labelled unavailable, including when omitted from a review packet.
Reviewer question answers have a separate section. Edit the JSON request list,
then rebuild the view; the HTML does not change dispositions.

**Retained is not selected.** `prototype_cpu_tested` means its relocated synthetic fixtures passed; it does not establish full packet authenticity, real generator quality or training admission. `needs_qualification` is static review only. Task-specific witnesses stay evidence, not universal gates. Original proposals and their hashes remain unchanged.

## Selected tools and mechanisms

Build a task-local prototype inventory with
[`arcpuzzles parametric manifest`](../../docs/parametric-promotion.md#prepare-another-prototype).
It derives current catalog/rule hashes and inventories declared evidence without
executing code. Author-reported checks, qualification and acceptance stay separate.

Primitive-name lint reports AST scope and line. Isolated local data bindings
without callable syntax are advisory. Definitions, direct calls, lambda/name/
attribute aliases, imports, module/class or external bindings, and multiple
primitive names in one scope remain warnings. This is a naming heuristic;
legitimate callable helpers can still warn, and it does not prove whether a
generator mirrors a reference rule.

`reviewer_support.find_root(__file__)` supports retained `WORK/checks/...`
artifacts by selecting the contained `WORK/repo`. A nearer copied runtime or
direct library ancestor wins. It does not inspect cwd, `ARCPUZZLES_HOME`,
arbitrary siblings, or escaping repository/ledger symlinks. Scripts under other
layouts still need an explicit supported repository root.

| Use | Entry point | Checks / limits |
|---|---|---|
| Compare remote storage starting states | `python3 review.py storage` (also works with this single file before extraction) | Read-only counters, optional bounded scan of an explicitly owned directory; no deletion or capacity gate. Temporary four-checkpoint collection through Oct 29 / 16 reports is consumed by native intake into `REVIEW/storage-study.json`. [Protocol](../../src/arcpuzzles/review_full_packet_files/RETURN-GUIDE.md#temporary-storage-comparison), [tests](../../tests/test_review_storage_study.py). |
| Load the selected generator for an authoring probe | `reviewer_support.load_selected_generator(ID, root=...)` | Returns module, exact source path and SHA-256 in repository or staged runtime; rejects mixed-tree dependency caches. Executes module imports, not generation or reference labels. |
| Replay a returned source delta | `arcpuzzles review replay-return --source-zip ORIGINAL --return-zip RETURN --compare-work WORK --out NEW [--runtime-closure]` | Validates source/return inventories, exact Git root, full patch inventory and every changed file hash. Optional declared-dependency extraction is explicitly partial; tests remain pending. [Command](../../REVIEW/README.md#replay-an-exact-return-in-a-fresh-checkout), [implementation](../../src/arcpuzzles/review_replay.py), [regressions](../../tests/test_review_replay.py). |
| Label hand-made repair/audit inputs | `arcpuzzles apply ID --input INPUT.json --out NEW.json`; `Catalog.apply(ID, grids)` | Public staged reference runner, per-input errors and generator/rule/input/output hashes; per-puzzle only, up to 64 grids. Exposes reference answers; keep outside blind solves. [Commands and identity contract](../../docs/verification.md#hand-made-inputs-and-reference-identity). |
| Check active and archival rule agreement | `arcpuzzles check ID --stage authority_sync --out NEW` | Prepares the local runtime before checking exact text and execution parity. Direct helper invocations with missing runtime dependencies report unscored infrastructure errors and the supported command. |
| Propose selected authority formatting | `arcpuzzles authority-sync ID --selected-only --out NEW.json` | Non-applying canonical-to-selected patch, exact file/source hashes and follow-up checks. Archival raw_code stays unchanged; semantic/unsupported edits are refused. |
| Apply reviewed formatting proposal | `arcpuzzles authority-sync ID --selected-only --apply REVIEWED.json` | Requires an identical regenerated proposal under the review lock; retains recovery snapshots and an applied/rollback receipt. It never edits canonical or archival sources. |
| Record a peer check as audit evidence | `arcpuzzles check ID --phase audit`; `check-run start ID --phase audit` | Keeps exact target/source and audit phase in isolated checks, summaries and resume. Strict policy matches after; checks neither approve the generator nor close findings. |
| Run task tests and semantic evidence together | `arcpuzzles check ID --stage audit --out NEW` | One snapshot, two retained outcomes and one execution allowance. Missing/skipped tests and advisory semantics do not count as a pass. [Preset, interruption and timeout contract](../../docs/reviewer-check-resume.md#combined-peer-audit). |
| Probe a large finite categorical axis | Existing `check ID --stage override --phase audit` | At most 16 planned values per enum; declared/tested coverage is explicit, sampled values require an observer, and omitted alternatives remain unqualified. |
| Read a battery result | `python3 shared/tools/summarize_battery.py result.json --json` | Standard library; distinguishes pass/advisory/failure/incomplete; rejects ambiguous JSON, incoherent counts and verdicts. Reads recorded statuses, does not rerun gates or authenticate them. |
| Give native checks a longer execution allowance | Existing `arcpuzzles check ID --timeout SECONDS` | Remaining allowance reaches the native wrapper; whole batteries share it, and actual caps/grace are recorded. Timeout stays a resource stop; pending stages remain unqualified. [Time contract](../../docs/reviewer-check-resume.md#execution-time-allowance). |
| Recover an interrupted assignment draw | Existing `python3 assignment.py` in an extracted packet | Same draw resumes from a durable journal; source hashes checked; conflicts block. POSIX filesystem locking, no real task draw in owner tests. Completed draws stay idempotent. |
| Enforce named lesson rivals | Existing generator worker / episode builder | Named callable `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS` join the hook; rivals fitting every demo and disagreeing on query prevent automatic lesson use. Finite declarations, not universal identifiability. Labels are checked only in the data-authoring worker. |
| Retain a checked semantic counterexample | Existing `generator_semantic_gate.py` JSON report | `rival_claims[W].witness_examples[R]` keeps the first checked disagreement for each declared witness/rival pair, complete grids, exact default recipe and observed source hashes; no additional Racket call. |
| Check integer-axis provenance | Existing `generator_defect_lint.py` | Includes all declared integer draw-choice options, not just selected values or draw-int bounds. Envelope does not prove interior occupancy. |
| Check scalar request contracts | Existing `check ID --stage defect_lint` | Separates seed/index/difficulty arguments from exact integer/color overrides. Reuses the override domain parser, confirms a valid control, then tests booleans, numeric strings, integral/fractional floats and out-of-domain negative indices. Unknown controls/domains remain explicit. No reference-label scoring in this probe. |
| CPU inventory integrity | ARC2train `scripts/replay_inventory_integrity.py --require-fixed --owner-root ... --out NEW` | 58 synthetic exposure/count controls; explicit fixtures, output directory and source hashes. No silent omission. |
| Intended training population | ARC2train `scripts/build_training_population.py PUBLIC_JSONL SOURCE_MANIFEST NEW_OUT` | Hash-only public roster, missing records retained in denominator, reservations preserved. Supplied-roster scope; no proof of actual whole-pool retention. |

### Scalar request diagnostics

`strict_scalar_probes` contains accepted invalid requests, unexpected exceptions
and unscored controls/domains, with `probe_kind`, actual `difficulty` and the
accepted `control_value` for scored probes. The existing structural receipt
binds the selected generator and rule source. The shared probe uses the same
domain parser as the override checker from this repository or copied runtime;
it never searches a sibling checkout. Diagnostic/non-exact, noninteger and
reserved call-argument axes are excluded from override probing.

The cohort is easy, default (`None`) and hard. Each exact integer/color axis
uses surviving endpoints or its singleton from the parser; sparse enums and
color exclusions retain that parser's semantics. Floating probes derive from
the accepted integer, including `n + 0.75`; the upper endpoint is probed only
when its valid integer control succeeds. Signed integer seeds and lawful `-1`
override values are not declared invalid. This is finite type/request evidence,
not an exhaustive axis, seed, lesson or correctness guarantee.

The probe costs at most 51 common-argument calls plus 42 per exact integer/color
axis across those bands, with no Racket labels. Missing domains and rejected
controls are recorded as unknown rather than a clean rejection. The combined
`--stage audit` preset still runs task tests and semantic checks; it does not
silently add this stage. Select `defect_lint` or the battery to exercise it.

### Semantic witness records

The semantic gate's JSON report retains one complete example per declared
witness/rival pair that actually disagrees. Its `recipe` records the pinned
`seed`, `sample_index`, `difficulty` and empty `overrides` used by the ordinary
census. Replay that recipe against the identified generator and apply the
identified Racket rule to its input. `input`, `authoritative_output` and
`rival_output` are full rectangular ARC grids, never clipped previews. The
selection is the first checked disagreement, not a minimization search.

`source_binding` hashes the observed Python file, the oracle's selected rule
source and its exact executed callable. Missing identities remain null with
`status: incomplete`; a file hash alone does not prove loaded-code authenticity.
`validation.self_check` separately records passed, failed, error or not declared.
A failed validator is still visible even when a rival disagrees. Rule or rival
errors produce no positive witness; grids outside the 1–30, integer 0–9 ARC
contract produce a bounded `witness_retention_errors` entry. These additional
records do not change existing census counts, gate verdicts, approval or training
admission. Existing comparison behavior is not upgraded by a retained example.

Owner checks: [witness records](../../tests/test_semantic_witness_records.py),
including one real Racket fixture, mutable rival outputs, missing identities,
validator errors and malformed grids. This is bounded tool evidence, not a new
real-generator battery or a proof of universal lesson identifiability.

### Selected source imports for reviewer probes

Use the public helper instead of importing the check runtime's private
`puzzle_generators.per_puzzle.<id>` alias. From an installed review packet,
`python3 review.py run python3 YOUR_PROBE.py` supplies the helper import path.
From this repository, use `PYTHONPATH=src:shared/runtime python3 YOUR_PROBE.py`.
In a probe kept with its generator:

```python
from reviewer_support import find_root, load_selected_generator

module, source_path, source_sha256 = load_selected_generator(
    "71e2e99645f4", root=find_root(__file__)
)
print(source_path, source_sha256)
```

Exact IDs are required; aliases and path strings are rejected. An explicit root
wins over `ARCPUZZLES_HOME`; without either, the helper uses its own tree,
not the working directory. Staged runtimes select both per-puzzle and generic
sources through `RUNTIME_MANIFEST.json`; an unselected task fails visibly.
The hash identifies the current Python bytes actually compiled, including edits
made after staging. It does not confirm a snapshot hash, generator approval,
Racket-label correctness or training admission. Imports execute top-level Python,
so this helper is for trusted authoring sources, outside the blind-solve lane.
Use a fresh process to inspect another library if `puzzle_generators` dependencies
are already cached from a different tree. The helper restores `sys.path` after
loading; it does not borrow a sibling checkout or change `ARCPUZZLES_HOME`.

Owner regressions: [selected-source loader](../../tests/test_selected_generator_loader.py),
including relocated generic/runtime selection, dataclasses, conflicting dependency
caches, stale-bytecode avoidance, unsafe paths and failed-import cleanup.

### Finite enum coverage

Override contract v8 distinguishes a finite enum exceeding the **16-value probe
cap** (`finite_enum_too_large`) from malformed or unparseable metadata. Literal
lists/tuples and pipe-separated strings use distinct choices in declaration order.
Up to 16 choices are all planned. Above 16, the plan uses indices
`floor(i * (N - 1) / 15)` for `i = 0..15`, including first and last plus 14
interior choices. Pairwise cases use that same bounded sample. This does not
enumerate every alternative or every higher-order combination.

The console plan's `sampled_enum_axes` and JSON `axis_domains` give the declared
cardinality, cap and `planned_coverage`. `probed_values` is the planned list;
`attempted_override_values` records only values actually requested in this run.
A shard or fail-fast stop can attempt fewer than planned. An attempted call is
not evidence that an override was honored: findings still record refusals,
missing observations and mismatches. A clean sampled run is
`PASS_WITH_WARNINGS`, with no qualification of omitted values.

Sampled exact categorical axes require `observe_overrides(grid)` to recover the
requested value; missing, omitted or clamped observations fail. Explicit
diagnostic axes stay outside the matrix and observer requirement. Existing
small-enum observation policy is unchanged. Static lint reports the sample as
a warning, not malformed metadata. Owner controls are in
[test_override_enum_domains.py](../../tests/test_override_enum_domains.py);
these are synthetic checker tests, not new generator approvals or corpus audits.

### Compact lesson-census evidence

`arcpuzzles lesson-census ID --out checks/census.json` now also writes
`checks/census.summary.json`. Both paths must be new. The full report remains
unchanged; the companion binds its byte count and SHA-256, source/rule/runtime
identities, invocation, counts and verdict. It keeps every production/rotation
failure or warning recipe, accepted sampling indices, named rivals and one exact
materialized witness per ambiguous rival. The worker records a declared rival's
wrong query prediction from its existing cache; older reports explicitly say
`not_recorded` when that prediction is absent. Advisory search findings retain
their separate basis and never change the census exit status.

`unique_rivals` counts exact named callable identities; `declaration_bindings`
counts namespace entries. `rival_identities` preserves every binding and its
`declared_in` list. Existing per-binding outcomes remain explicit. See the
[identity and caching contract](../../docs/SEMANTIC_GATE_CONTRACT.md#lessons-rotations-and-verdicts)
and [alias controls](../../tests/test_census_rival_identity.py).

Use the companion for concise authoring feedback and the full report for
`--rescore` or `check --schedule-census`. The companion is not a substitute gate
receipt and includes authoring labels. It omits successful lesson grids and the
copied runtime inventory; the full report is never removed automatically.
Interrupted or partial counts/errors stay explicit. Controls:
[test_census_companion.py](../../tests/test_census_companion.py).

For large reports, use `arcpuzzles lesson-census ID --gzip --out checks/census.json`.
It writes the complete `census.json.gz`, `census.compression.json` and the same
compact companion; the uncompressed file is not written. All four names,
including the logical `census.json`, must be unused before the census starts.
Gzip uses timestamp zero and no stored filename. Its manifest uses the existing
`arcpuzzles-evidence-gzip-v1` contract with original/compressed sizes and hashes,
so citing `checks/census.compression.json` retains its payload during ZIP disposal.
The verdict, failure details, labels and exit code are unchanged.

To generate and check a declared schedule within the ordinary semantic stage:

```bash
arcpuzzles check ID --stage semantic_gate --enumerate-schedule-period \
  --schedule-seed 0 --phase after --out var/checks/new-enumeration
```

The same flag works with `--battery` or `--stage audit`. It calls the existing
Racket-backed census on the staged source, with every declared starting residue
in every band and each labelled pair held out once. Query rotations are blocking;
use this for a curriculum that supports arbitrary query positions. An ordered-only
curriculum can still be inspected separately with `lesson-census --rotation-policy
diagnostic`. Missing or malformed periods, ambiguity, hook warnings and failed
draws do not satisfy the gate. This opt-in work uses the check's existing time
allowance; the default smoke check still does not enumerate a period.

The full labelled receipt is retained at
`checks/ID_PHASE_semantic_gate.schedule-census.json`, checkpointed after each
requested lesson. Interrupted coverage stays incomplete. A passing result says
`complete_fixed_seed_executed`, identifying source-bound execution at that seed,
bands, declared period and demo count. This does not prove the period declaration,
all random support, audit resolution or training admission. The flag and seed
bind public resume and native marker reuse. An explicitly supplied receipt is
mutually exclusive with fresh enumeration.
Coverage names its `semantic_contract` and exact `rivals`: a clean hook-only
census checks that hook and does not claim a rival was tested. Missing contracts
remain incomplete work under strict repair checking.

To consume an existing schedule receipt directly, use:

```bash
arcpuzzles check ID --stage semantic_gate --schedule-census checks/census.json.gz \
  --schedule-seed 0 --out var/checks/new-schedule-check
```

The native `.json.gz` requires the neighboring `.compression.json` written by
the producer. You can instead pass that one-file manifest. The reader verifies
both size/SHA-256 pairs, JSON validity and the exact requested payload before
staging. It rejects corrupt, missing, ambiguous or escaped inputs. The check
retains the decoded full JSON and exact compressed transport, binding both in
its settings; changing even the manifest bytes prevents checkpoint reuse.
Source/rule/seed/band/rotation validation still applies. Coverage remains reported
fixed-seed evidence, not re-executed labels, all-seed proof or audit closure.

`--rescore` still needs full JSON: copy the gzip to a new directory, run
`python3 -m gzip -d census.json.gz`, and verify restored size/SHA-256 against
the manifest. Curated retention summaries and the compact authoring companion
are not complete gate receipts. The manifest's
`restore_argv` is data for this step; intake never executes it. A raw report above
the return's expanded-size limit is exercised through the real return builder
and validator in [test_census_gzip.py](../../tests/test_census_gzip.py).
Reader and source/staleness controls are in
[test_check_schedule_receipt.py](../../tests/test_check_schedule_receipt.py) and
[test_semantic_rotations.py](../../tests/test_semantic_rotations.py).

### Authority execution setup

Use `arcpuzzles check ID --stage authority_sync --out NEW` for executable
authority checks. The direct `shared/tools/check_task_authority_sync.py` helper
can inspect text in the source checkout, but execution parity requires its
prepared runtime's `scripts/`, `arc_repl/` and `puzzle_generators/` dependencies.
Missing files produce `INFRASTRUCTURE_ERROR`, `executed: false`, no per-source
scores, and the exact public command to run. The gate fails until checked in a
complete runtime. Equivalent and incorrect rules remain separate `PASS`/`FAIL`
outcomes when actually executed.

Canonical `program_solution` and selected `target_code` are active authorities;
`raw_code` is preserved archival source and can differ. This diagnostic does not
edit any rule or synchronize text. Controls:
[execution layout](../../tests/test_authority_execution_layout.py).

For a formatting mismatch, `arcpuzzles authority-sync ID --selected-only`
prints a JSON proposal; `--out NEW.json` saves it exclusively. It copies the
one unambiguous canonical `program_solution` into catalog-bound selected
`racket_target.target_code` strings, preserving every surrounding file byte and
archival `raw_code`. The report includes each file's old/new SHA-256, source
hashes, canonical/catalog inspection pins and a minimal unified patch.
**Without `--apply`, it never applies the patch.** Review the hashes and recreate
the proposal if any source changes. The patch uses
repository-root `shared/` paths; it is not the flattened helper's `--patch` format.

Only identical tokens in a restricted Racket reader subset are eligible:
inter-token whitespace and `;` line comments can differ; strings, escaped
symbols, character literals, reader extensions and ambiguous canonical sources
require manual review. No generic semantic-equivalence claim is made. After
an explicitly selected edit, run the emitted `authority_sync` and
`rule_smoke` commands in new output directories. These checks and generator
approval remain separate. Controls: [read-only proposals](../../tests/test_authority_sync_proposal.py).

### Apply a reviewed proposal

```bash
arcpuzzles authority-sync ID --selected-only --out NEW.json
# Inspect the file list, old/new hashes and patch in NEW.json.
arcpuzzles authority-sync ID --selected-only --apply NEW.json
```

Apply regenerates the full proposal and requires exact equality, including the
canonical/catalog pins, selected file hashes and patch. Stale/tampered proposals
are refused before authority writes. `--out` is for dry runs; apply saves its
own receipt under `var/review/authority-sync/` and prints the receipt and recovery
directory. Canonical `program_solution`, archival `raw_code` and unrelated fields
are preserved. Approval and generator-audit dispositions are not changed.

The existing `REVIEW/.lock` coordinates cooperating review writers. Stop editors
that do not use that lock before applying. Each file is replaced atomically with
its mode preserved; multiple replacements are **not crash-atomic**. Original
bytes and a `prepared` receipt are saved before the first replacement. On a
caught failure, the tool restores only files still equal to its proposed bytes;
competing edits remain untouched and produce `recovery_required` with named
conflicts. After a forced termination, inspect current old/new hashes against
the recovery receipt before restoring any snapshot. Run the emitted follow-up
checks after success; keep recovery files until those checks finish, then treat
them as temporary managed recovery material. Controls:
[apply, refusal and recovery](../../tests/test_authority_sync_apply.py).

## Retained code-bearing proposals

Six relocated standard-library fixture suites passed **107 tests**. The already-selected evidence-root guard passed **13** original controls. Draw, lesson, axis and battery repairs have tests in the owner `tests/` directory. The isolated full packet repeats the relevant checks.

| Proposal | Role | Current disposition | Reason |
|---|---|---|---|
| [43b07938ee7eae0f](proposals/43b07938ee7eae0f/manifest.json) | Bounded compressed evidence restoration | `needs_qualification` | Source inspected; four compressed dependencies independently hash-checked after bounded decompression. Helper not executed or selected as a shared census command. |
| [12d0ecfd24887b45](proposals/12d0ecfd24887b45/manifest.json) | Foreground-majority rival probe | `task_scoped_evidence` | Source inspected; intermediate generator snapshot retained. Private runner interfaces and overwriteable report path; evidence only, not a general gate. |
| [dcb7ea5a5fd92605](proposals/dcb7ea5a5fd92605/manifest.json) | Original-source repository failure reproduction | `not_selected` | Hard-coded reviewer/archive/runtime paths. Preserve classification and source; no owner execution or test-expectation changes. |
| [05ca913838280d63](proposals/05ca913838280d63/manifest.json) | Offline pytest environment snapshot | `not_selected` | Source inspected; enables `system_site_packages` and borrows host dependencies. The reported 116-test run is not an owner replay or hermetic dependency qualification. Keep the isolated prerequisite-probe request; do not install this helper as the default. |
| [ee3de564aa37e045](proposals/ee3de564aa37e045/manifest.json) | Startup capacity / pending checkpoint | `needs_qualification` | Source inspected; metadata-only advisory report and lock-bound exact control-file checkpoint. Reviewer reports 33 tests, not rerun by the owner. No restore support; format is incompatible with current recovery. Needs production lifecycle and relocated qualification before selection. |
| [01cbdb9c913c0649](proposals/01cbdb9c913c0649/manifest.json) | Task-specific rival/audit probe | `task_scoped_evidence` | Static-reviewed task-specific witness with source/layout assumptions. Keep it with the cited task/audit; not a general shared gate or an unmeasured proof of universal ambiguity. No extra generator execution. |
| [02949d01df708d51](proposals/02949d01df708d51/manifest.json) | Integer draw-choice provenance | `implemented` | Reviewed and integrated into shared/tools/generator_defect_lint.py; synthetic owner regressions in tests/test_axis_choice_provenance.py. Declared scope only, no real-data or model qualification. |
| [06276e0db3f7691d](proposals/06276e0db3f7691d/manifest.json) | Executable lesson rivals | `implemented` | Reviewed and integrated into src/arcpuzzles/worker.py; synthetic owner regressions in tests/test_lesson_rival_contract.py. Declared scope only, no real-data or model qualification. |
| [1ecd13a65c9024a8](proposals/1ecd13a65c9024a8/manifest.json) | Battery verdict reader / console fix | `implemented` | Selected strict reader and truthful advisory console; 11 owner tests and 14 subtests. Original proposal bytes retained. |
| [141ed1817683dbda](proposals/141ed1817683dbda/manifest.json) | Racket failure diagnostics | `already_implemented` | Current packet setup_racket.py already reports timeout, return code and signal. Current extracted runtime smoke was verified; the retained old patch should not be reapplied. |
| [1750e3d4532ef969](proposals/1750e3d4532ef969/manifest.json) | replay_return.py | `prototype_cpu_tested` | 21 relocated synthetic tests passed. Original remains a passive proposal; not selected or a full packet/source authority check. |
| [24d572f146bca9e3](proposals/24d572f146bca9e3/manifest.json) | Task-specific rival/audit probe | `task_scoped_evidence` | Static-reviewed task-specific witness with source/layout assumptions. Keep it with the cited task/audit; not a general shared gate or an unmeasured proof of universal ambiguity. No extra generator execution. |
| [3038ee3fbeac21af](proposals/3038ee3fbeac21af/manifest.json) | compress_evidence.py | `prototype_cpu_tested` | 4 relocated synthetic tests passed. Original remains a passive proposal; not selected or a full packet/source authority check. |
| [46f396ad0a6d1f6f](proposals/46f396ad0a6d1f6f/manifest.json) | Earlier ZIP replay helper | `not_selected` | Static review: no duplicate/member expansion limits for original ZIP, ordinary Git initialization inherits environment/config, and only final generator hash is checked. Prefer owner candidate/check path; better isolated replay prototypes have synthetic tests. |
| [48033795b67c935a](proposals/48033795b67c935a/manifest.json) | Offline Python provisioning | `needs_qualification` | Static-reviewed installer only; no installation run. Host distribution/cache bytes and compatible native dependency closure need explicit qualification. Do not treat copied metadata or an import probe as independent dependency provenance. |
| [4841641f9776ed0b](proposals/4841641f9776ed0b/manifest.json) | replay_return.py | `prototype_cpu_tested` | 7 relocated synthetic tests passed. Original remains a passive proposal; not selected or a full packet/source authority check. |
| [4f4d1a051e2fd68c](proposals/4f4d1a051e2fd68c/manifest.json) | Historical generator candidate | `task_scoped_evidence` | Retained candidate snapshot, not a reusable tool. It cannot approve or replace current generator bytes. |
| [570bbfcd3ce1ce8b](proposals/570bbfcd3ce1ce8b/manifest.json) | Offline Python provisioning | `needs_qualification` | Static-reviewed installer only; no installation run. Host distribution/cache bytes and compatible native dependency closure need explicit qualification. Do not treat copied metadata or an import probe as independent dependency provenance. |
| [7a69411ca82fd8e6](proposals/7a69411ca82fd8e6/manifest.json) | Offline copied-distribution environment | `not_selected` | Static review found system_site_packages=True: imports borrow the host environment. No fresh-destination guard before provisioning. This cannot establish packet isolation; use declared dependencies in a clean environment. |
| [7fa6695cc83ddd1e](proposals/7fa6695cc83ddd1e/manifest.json) | Task-specific rival/audit probe | `task_scoped_evidence` | Static-reviewed task-specific witness with source/layout assumptions. Keep it with the cited task/audit; not a general shared gate or an unmeasured proof of universal ambiguity. No extra generator execution. |
| [867decc98fa458d9](proposals/867decc98fa458d9/manifest.json) | Bounded exact-override probe | `needs_qualification` | Static-reviewed bounded generator subprocess tool. Packet layout/reviewer_support assumptions need a portable fixture and explicit dependency tests before selection; no blanket task replay performed. |
| [93878cbb507c63c4](proposals/93878cbb507c63c4/manifest.json) | Evidence-root symlink guard | `already_implemented` | Current selected review_full_return.py already contains all three root checks; 13 original synthetic reproductions pass against current source. |
| [9e04fa4729d1a6be](proposals/9e04fa4729d1a6be/manifest.json) | Task-specific rival/audit probe | `task_scoped_evidence` | Static-reviewed task-specific witness with source/layout assumptions. Keep it with the cited task/audit; not a general shared gate or an unmeasured proof of universal ambiguity. No extra generator execution. |
| [9e21bf07bc72fcc6](proposals/9e21bf07bc72fcc6/manifest.json) | Task-specific rival/audit probe | `task_scoped_evidence` | Static-reviewed task-specific witness with source/layout assumptions. Keep it with the cited task/audit; not a general shared gate or an unmeasured proof of universal ambiguity. No extra generator execution. |
| [9f4544cc18e5e84a](proposals/9f4544cc18e5e84a/manifest.json) | Historical generator candidate | `task_scoped_evidence` | Retained candidate snapshot, not a reusable tool. It cannot approve or replace current generator bytes. |
| [af521284af4f7ab9](proposals/af521284af4f7ab9/manifest.json) | Earlier destructive evidence packer | `not_selected` | Static review: packing unlinks originals, iterates reports without rejecting symlink sources, and updates its map without durable transactional publication. Use canonical retention/compaction or the separately tested retained-original compression prototype. |
| [b89fcb4b9114fa2f](proposals/b89fcb4b9114fa2f/manifest.json) | replay_review_return.py | `prototype_cpu_tested` | 26 relocated synthetic tests passed. Original remains a passive proposal; not selected or a full packet/source authority check. |
| [ba1930710e980910](proposals/ba1930710e980910/manifest.json) | Full fresh-return replay orchestration | `needs_qualification` | Static-reviewed orchestration that can execute packet setup and batteries. Synthetic lifecycle/interrupt/closure qualification is still needed; not run on current tasks or installed as an active tool. |
| [f47fb55fd2080c1a](proposals/f47fb55fd2080c1a/checks/tooling/evidence-compression/README.md) | Explicit gzip compression and exact restoration | `prototype_cpu_tested` | 11 isolated synthetic CLI tests pass. The `arcpuzzles-evidence-gzip-v1` manifest is supported by owner retention, with directory-relative payloads and compressed/original hash checks. Supplied compressor remains passive; no automatic deletion or duplicate installed command. |
| [c9fcdc27f1434736](proposals/c9fcdc27f1434736/manifest.json) | finish_recovery.py | `prototype_cpu_tested` | 42 relocated synthetic tests passed. Original remains a passive proposal; not selected or a full packet/source authority check. |
| [f067eb92fdc48c7e](proposals/f067eb92fdc48c7e/manifest.json) | packet_resource_preflight.py | `prototype_cpu_tested` | 7 relocated synthetic tests passed. Original remains a passive proposal; not selected or a full packet/source authority check. |
| [f9b3a0495d41f2fb](proposals/f9b3a0495d41f2fb/manifest.json) | Crash-safe assignment draw | `implemented` | Reviewed and integrated into src/arcpuzzles/review_full_draw.py; synthetic owner regressions in tests/test_review_draw_recovery.py. Declared scope only, no real-data or model qualification. |

The older environment helper using `system_site_packages=True` is not selected. Earlier weaker replay and destructive compression scripts are not selected. Their useful ideas are retained without installing duplicate active commands. New tool requests remain editable in the request list; reviewers should name one existing tool to extend and supply a relocated synthetic counterexample plus the expected exit/status.

The color-role probe for [34f8510e39d0](../../generators/34f8510e39d0/workspace/README.md) stays task-specific. Two actual CLI destination-collision controls pass; its reported sampler/Racket witnesses are not a new universal shared gate.

The bounded searched-rival interface is selected below. Broader independent
object-selector libraries, axis-schema/observability checks and authority-sync
dry runs remain proposals in the request list. Task-local probes for
[e51349aef7b1](../../generators/e51349aef7b1/workspace/README.md) stay witnesses;
static inspection is not execution or a global gate.

The [output-profile diagnostic for 8738d400fb96](../../generators/8738d400fb96/workspace/check_output_profile_support.py)
was inspected and exercised: 31 focused tests, including five CLI output-preservation
regressions, and two replays over retained labelled receipts. It binds the complete
canonical pair set and checks full/partial/empty support per band using a task-specific
green-to-cyan mass adapter. Reports require a new destination. Labels were not
recomputed. Shared adapters, a canonical identity-map helper and global schedule
correlation diagnostics remain proposals; finite support does not establish correct
labels, useful balance, universal lesson identifiability or training admission.

The [X-selector replay](../../generators/70f97d6b605b/workspace/replay_selector_contract.py) is task-specific: it uses authentic `arcpuzzles apply` labels, checks source/rule identities and linked rivals, preserves failures, and requires a new report directory. Static source inspection only; its reported 122-case replay and 91 tests were not rerun by the owner. Finite rivals are not universal identifiability.

## Selected audit diagnostics

- `arcpuzzles apply TASK --input INPUT.json --check-generator-domain` keeps Racket
  output independent and adds per-input `generator_domain` status/errors against
  the selected generator hash. Missing checkers and checker exceptions remain
  explicit; a checker receives a copy after the authority has run.
- Defect lint retains canonical/generated object-count, output-shape, palette-role
  and singleton-marker signatures, including a representative Racket-labelled
  mismatch witness and source hashes. This is an advisory comparison of measured
  support, not a prose parser or proof of the intended semantics.
- Semantic gate and lesson census separately report bounded searched rivals.
  Generic candidates mutate measured labels (first color, nearest-component
  attribution, positional/tie choices, no fill, omitted changed cell). They are
  hypotheses on that measured support, not independent solvers. A task can expose
  `SEARCHED_RIVAL_PROVIDER()` yielding `(name, transform)` for independent families,
  including task-specific omitted construction steps. Providers remain separate
  from `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`. Each candidate reports `refuted`,
  `ambiguous`, or `support_equivalent`, plus errors/nonapplicability as needed.
  Ambiguous witnesses remove duplicate demonstrations while preserving distinct
  teaching evidence. Candidate enumeration is bounded; it is not universal search.
  Searched findings are advisory and do not silently change declared-rival verdicts.
- Census summaries distinguish `declared_schedule_period`,
  `reporting_residue_modulus`, and `enumerated_schedule_period`; a short declared
  period warns when not enumerated. The semantic gate separately reports
  `schedule_coverage.status=declared_period_not_enumerated` for any positive
  declared period and marks the smoke result advisory. Its `followup_argv`
  enumerates every declared start and query position at seed 0 across the three
  difficulty bands; the console prints the same command. Run it with a new
  output path. This remains finite fixed-seed evidence, and does not establish
  all-seed support or replace production/rotation checks.
  Production and rotated queries keep their
  explicit `rotation_policy`. Ordinary samples do not prove schedule coverage.
- See [resume and report modes](../../docs/reviewer-check-resume.md) for managed
  detached `check-run start/status/wait/resume`, root-cause summary defaults,
  `--full-results`, and the retained `--compact-results` compatibility format.

The selected implementations are `shared/runtime/review_diagnostics.py`,
`shared/tools/write_generator_test.py`, the existing gates/census, and
`src/arcpuzzles/check_jobs.py`. Retained proposal manifests and assets remain
immutable evidence. No capacity preflight or resource guard is introduced.

# Working notes: a8a8969ab4f1

## Review baseline

No prior return for this task was used as a repair lead; `evidence/associated_notes.jsonl`
was empty. The retained passing task `b90d4c3d5553` was consulted only as an
example of the shared semantic-contract and exact-override interfaces.

The selected v2.1.0 baseline generated a key in every row even though all three
canonical inputs have exactly three keyed rows separated by zero-key rows. Its
validator rejected those canonical inputs, several advertised axes were dead or
unprobeable, exact overrides were not observable, `RULE_HASH` was missing, and
there was no executable semantic contract. The immutable before battery therefore
had five blocking stages: lint, self-check, defect lint, profile floor, and
override; semantic gate was advisory (`NO_CONTRACT`).

## Repair decisions

- Kept the selected Racket authority unchanged and pinned `RULE_HASH =
  "1130750019d1"`.
- Replaced ten broad/dead controls with four literal, pixel-observable controls:
  `shape`, `row_pattern`, `key_color_pattern`, and `marker_profile`.
- Restricted dimensions to the three canonical size profiles and made exactly
  three rows keyed. Blank rows are now lawful; keyed rows each have one to three
  cyan markers.
- Preserved full support for every exact override in every difficulty band.
  Difficulty changes sampling weights only.
- Added a deterministic period-three teaching schedule. Indices congruent to
  zero are canonical anchors; the other two indices add one or two cyan markers
  to zero-key rows. Any four consecutive pairs retain at least one such witness
  after any single query is held out.
- Declared the plausible canonical shortcut `erase_unkeyed_markers`, its witness,
  rival mapping, lesson competitor, strict-manifold hook, and
  `lesson_identifiable` check.
- Added malformed-input diagnostics and destructive-mutation sensitivity.

## Independent review tools

`workspace/reference_probe.py` loads an alternate candidate source, reads
canonical pairs through the public reviewer helper, analyzes pixels without
calling generator internals, and provides an independently written rule mirror
for focused tests.

`workspace/qualify.py` dynamically reads the generator's declared competitors,
checks overlapping four-pair windows and all four query rotations, exhausts the
joint exact-axis product in every band, and confirms every declared canonical
shortcut actually fits all canonical labels. It supports `--source` so future
reviewers can compare retained candidates without editing the selected file.

## Final evidence and limits

The final generator source SHA-256 is
`ec942e8175f3e057c5b00b39371fe55851413e1b954a8362a8d7aaa21f24134b`.
The native after battery was 12/12 green with no advisories; strict support was
168/600 (28.0%), canonical acceptance 3/3, exact-profile support 49/60, and the
override matrix accepted and observed all 6,930 draws. The source-bound lesson
census materialized 300/300 lessons and found 0 ambiguous outcomes across 1,200
query rotations. The task-local overlapping-start probe checked 3,000 windows,
12,000 rotations, 3,009 unique inputs, and all 324 joint exact-override cases
with no finding.

These are finite checks against the declared shortcut, not proof of unique
induction against every imaginable program. The production manifold intentionally
retains the canonical convention of exactly three keyed rows, and it does not
claim to teach behavior for malformed keys or non-`0`/`8` payload cells.
## Current reviewer considerations

Source SHA-256: `ec942e8175f3e057c5b00b39371fe55851413e1b954a8362a8d7aaa21f24134b`.

# Decisions — a8a8969ab4f1

## D1 / R1 — Repair the sampler, not the authority

**Choice.** Keep the selected Racket authority unchanged and rebuild the Python
input sampler around the actual canonical task. Pin `RULE_HASH =
"1130750019d1"` so the generator declares which authority it targets.

**Rationale.** The baseline's transformation checks were already healthy:
`rule_smoke`, grammar, Racket lint, and authority synchronization passed. The
failures came from input-domain and metadata mismatches: all-row keys, rejection
of canonical blank rows, dead axes, and no semantic contract. Changing the
Racket rule would have treated a generator defect as an authority defect.

**Alternatives rejected.** I rejected modifying canonical examples, weakening
the validators until the baseline passed, or embedding a different Python rule
as authority. Those approaches would conceal the mismatch rather than produce
better training inputs.

**Probe.** Before/after batteries at
`checks/before/checks/a8a8969ab4f1_before_battery_summary.json` and
`checks/after/checks/a8a8969ab4f1_after_battery_summary.json`; final authority
synchronization remains green.

**Limitation.** The local Python mirror used by task probes is not authority. It
is independently checked against canonical pairs and backed by the shared
Racket-labelled battery.

## D2 / R1 — Use only the three canonical grid shapes

**Choice.** Define the exact shape axis as `6x8`, `7x9`, and `8x10`.
Difficulty changes weights but never removes support.

**Rationale.** Those are the three canonical profiles. Restricting the size axis
to literal, recoverable values makes each override meaningful, guarantees
canonical profile support, and avoids inventing geometry unsupported by the
examples.

**Alternatives rejected.** The baseline's broad or implicit dimensions made the
axis hard to probe and permitted training mass outside the demonstrated size
manifold. A continuous height/width range was also rejected because it would
create many untested profiles without teaching a new semantic branch.

**Probe.** `strict_canonical_like`, `observe_overrides`, the 60-draw profile
floor, all 324 joint exact-axis combinations, and focused shape tests. Profile
report: `checks/after/checks/a8a8969ab4f1_after_profile_floor.json`.

**Limitation.** The generator does not claim generalization to arbitrary grid
sizes.

## D3 / R1 — Exactly three keyed rows, with lawful blank rows

**Choice.** Every production grid contains exactly three rows with a nonzero,
non-cyan key in column zero. Other rows are valid zero-key rows.

**Rationale.** Every canonical input has exactly three keyed rows. This repairs
the baseline's strongest domain mismatch—placing a key in every row—and permits
canonical inputs to pass `self_check`.

**Alternatives rejected.** Randomizing the number of keyed rows would broaden
the task without canonical evidence and would confound the intended semantic
counterexample. Keeping all rows keyed would leave the zero-key branch
unreachable and preserve the original failure.

**Probe.** Canonical acceptance is 3/3, focused tests check exactly three keys,
and the independent pixel probe reconstructs active/blank rows without calling
generator internals.

**Limitation.** This is an intentional distribution restriction. The authority
may have defined behavior outside it, but the returned training generator does
not claim to teach that extension.

## D4 / R1 — Four literal, pixel-observable axes

**Choice.** Replace the baseline's broad/dead controls with:

1. `shape`: three canonical sizes;
2. `row_pattern`: `alternating`, `clustered`, `scattered`;
3. `key_color_pattern`: `distinct`, `mixed`, `repeated`;
4. `marker_profile`: `one_each`, `two_each`, `three_each`, `mixed`.

**Rationale.** Each value changes visible pixels, can be recovered exactly by
`observe_overrides`, has full support in every band, and expresses a useful
structural variation without changing the rule. The controls separate geometry,
key identity, and marker multiplicity instead of advertising hidden parameters
that cannot be verified.

**Alternatives rejected.** I rejected cosmetic RNG controls, integer axes with
unbounded or "varied" metadata, and parameters whose accepted values silently
clamp or fall back. I also rejected adding more axes merely to increase nominal
diversity; four axes already yield 108 joint combinations per band.

**Probe.** The shared override matrix accepted and observed 6,930/6,930 draws
across 77 cases and three bands; the task-local qualification exhausts all 324
joint axis combinations. Evidence:
`checks/after/checks/a8a8969ab4f1_after_override_results.json` and
`checks/qualification.json`.

**Limitation.** `row_pattern` is a three-class summary, not an enumeration of
every possible row placement. Random placement remains within the selected
class.

## D5 / R1 — Keep marker counts small and directly legible

**Choice.** Keyed rows contain one to three cyan markers. The marker-profile
axis either fixes all three row counts or selects a mixed triple.

**Rationale.** One to three markers fit all three widths, remain visually simple
for a 9B training target, and provide enough multiplicity to prevent a solver
from treating the rule as a single-cell edit. Mixed profiles make per-row
application explicit.

**Alternatives rejected.** Dense rows would make examples noisier without adding
a semantic branch. A single fixed count would unnecessarily couple the rule to
one geometry. Zero markers in a keyed row were rejected because such a key would
provide no observable transformation.

**Probe.** `self_check`, exact marker-profile recovery, focused tests for all
profiles, and the exhaustive joint-override probe.

**Limitation.** The production domain intentionally excludes keyed rows with
more than three markers.

## D6 / R2 — Add a period-three zero-key preservation witness

**Choice.** `sample_index % 3 == 0` produces a strict canonical anchor. The next
two positions add respectively one and two cyan markers to rows whose key is
zero. The authority preserves those markers.

**Rationale.** All canonical pairs are compatible with the plausible shortcut
"recolor keyed rows, erase cyan from zero-key rows." Individual correct labels
are therefore insufficient to teach the hidden preservation branch. A
one-anchor/two-witness cadence guarantees that any four consecutive pairs still
contain at least one witness after any one pair becomes the query.

**Alternatives rejected.** Purely random witness insertion could produce an
all-anchor lesson. Putting witnesses in every sample would abandon the strict
canonical manifold and fail the profile floor. A longer or stateful schedule
would be harder to audit and offer no benefit for three-demo lessons.

**Probe.** Final semantic battery: 392/600 witness hits and 208/600 anchors;
strict rotation run: 100/100 lessons and 400/400 rotations identifiable;
qualification: every rotation of 3,000 overlapping windows clean. Evidence at
`checks/after/checks/a8a8969ab4f1_after_semantic_gate.json`,
`checks/rotation-runtime/rotations.json`, and `checks/qualification.json`.

**Limitation.** The guarantee is specific to four-pair lessons with three
demonstrations and one query. It is not a proof against undeclared rivals.

## D7 / R2 — Declare one concrete shortcut consistently

**Choice.** Use `erase_unkeyed_markers` as the canonical shortcut, semantic
rival, lesson competitor, and witness target.

**Rationale.** It fits every usable canonical pair, differs only on the branch
missing from canonical examples, and is simple enough to be a realistic model
shortcut. Reusing one executable hypothesis across declarations prevents
metadata drift.

**Alternatives rejected.** Identity, flips, rotations, and transpose do not fit
all canonical labels and therefore are not the relevant ambiguity. I rejected a
large hand-written rival catalog because it would be difficult to justify and
maintain.

**Probe.** The qualification tool dynamically reads the generator's actual
competitor declarations and verifies that each declared canonical shortcut fits
all canonical pairs before scoring lessons. The witness rival disagreed on all
60 checked witness cases in both semantic runs.

**Limitation.** Passing this competitor does not establish uniqueness among all
possible programs.

## D8 / R3 — Test through public paths and independent pixel analysis

**Choice.** Add portable tests using `reviewer_support.find_root`,
`canonical_path`, and `canonical_pairs`; add `workspace/reference_probe.py` to
load a selected source and analyze grids without importing the generator's
private classifiers.

**Rationale.** Tests tied to a fixed parent depth or the working packet layout
would fail after packaging. An independent pixel analyzer catches a generator
whose internal observer and sampler share the same mistake.

**Alternatives rejected.** I rejected tests that only call `observe_overrides`
and assert its own output, and tests that read private labels or runner internals.

**Probe.** The final portable copied-runtime test stage passed 27/27; the same
suite run against the retained baseline failed 22 and passed 5. Fresh-packet
application and rerun also passed 27/27.

**Limitation.** The independent Python rule mirror is still code written during
this review; Racket-labelled shared checks remain the external binding.

## D9 / R3 — Build a reusable qualification harness

**Choice.** Add `workspace/qualify.py` with source selection, all cyclic query
positions, overlapping lesson starts, dynamically discovered competitors,
canonical-shortcut fit checks, and exhaustive joint exact overrides.

**Rationale.** The shared battery samples broadly but does not exhaust this
small deterministic schedule or the full four-axis Cartesian product. A
source-selectable harness lets future agents compare retained candidates without
editing the selected generator.

**Alternatives rejected.** Hard-coding rival names in the harness was rejected;
it would silently become stale. Sampling only isolated pairs was also rejected
because individual correctness does not prove lesson identifiability.

**Probe.** With seed 404 and 1,000 starts per band: 3,000 windows, 12,000 query
rotations, 3,009 unique inputs, 324 joint exact-override cases, zero ambiguity,
invalid input, or hook error. `checks/qualification.json`.

**Limitation.** The harness uses finite seeds and declared competitors. Its
result is evidence, not a completeness theorem.

## D10 / H1 — Bind the final patch, tests, and solve to identical bytes

**Choice.** Generate the exact final delta with the same diff routine used by
the packager, apply it to a fresh extraction under an isolated Git root, verify
the generator SHA-256, rerun focused tests, and compare the solve summary hash.

**Rationale.** A passing working tree is not enough if the packaged patch omits a
new file, applies under a parent worktree, or differs from the generator used for
tests or the solve episode.

**Alternatives rejected.** I rejected relying on the current workspace or merely
inspecting the patch text.

**Probe.** `checks/final-handoff/source.patch`, `apply.log`, `pytest.log`, and
`handoff.json`. `git apply --check` and apply exited 0; fresh generator hash and
post-repair solve hash both equal
`ec942e8175f3e057c5b00b39371fe55851413e1b954a8362a8d7aaa21f24134b`.

## D11 / A1-A2 — Audit targets are evidence-only

**Choice.** Construct minimized Racket/rival counterexamples and distribution
censuses for `87388eaff4ce` and `71e2e99645f4`, but do not edit either target.

**Rationale.** They are assigned adversarial audits, not the selected repair
scope. Source-bound evidence is more useful than an unauthorized patch.

**Probe.** See `AUDIT.md` and `checks/audit/`.

**Limitation.** The audits establish concrete coverage/override defects, not a
complete review of every behavior in those generators.

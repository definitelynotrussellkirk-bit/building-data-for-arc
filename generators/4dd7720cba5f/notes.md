# Working notes: 4dd7720cba5f

## 2026-10-03 review-1c635e9ee25e57a2

### Reproduced defect

All 10 canonical pairs, and every version-3 generated input, have at most one
nonempty source motif per color. Two plausible wrong rules therefore fit all
canonical examples: (1) copy only the first source motif and (2) fill blank
same-color peers but never merge partial sources. The baseline also declared no
semantic witnesses, rivals, or lesson-identifiability contract.

The isolated task-test runtime exposed two independent test defects: canonical
data was located by a source-tree-relative path, and the rule test hashed raw
text instead of the repository's whitespace-normalized `RULE_HASH` convention.
Authority sync also showed selected `target_code` semantically equivalent but
not byte-exact with canonical `program_solution`.

### Selected repair

- Added one lawful multi-source union profile per difficulty band. Each splits a
  3-, 4-, or 5-cell central motif across two same-color source frames.
- Scheduled a union profile at every third default `sample_index`, so every
  three consecutive demonstrations contains a source-bound counterexample.
- Declared `strict_canonical_like`, two canonical shortcuts/semantic rivals, a
  verified multi-source witness, and `lesson_identifiable`.
- Kept all five linked public profiles and four previous extrapolated profiles
  as exact `scene_profile` controls.
- Made focused tests portable with `reviewer_support`, fixed normalized rule
  hashing, and synchronized both selected base `target_code` fields exactly to
  canonical. `raw_code` remains archival and unchanged.

### Measured final evidence

- Task tests: 28 passed, 796 subtests passed.
- Semantic gate: 600/600 strict, 10/10 canonical accepted, witness fired 189/600,
  both rival claims verified, and 12/12 smoke lessons identifiable.
- Lesson census: 300/300 lessons materialized and unambiguous, 1200/1200 exact
  inputs unique; both shortcuts refuted in every lesson in every band.
- Task-local cyclic probe: 36/36 starts passed (12 starts × 3 bands).
- Canonical Racket semantics and `RULE_HASH=d947d085ded3` did not change.

The finite rival set is not a proof of universal induction. The generator
intentionally limits multi-source fragments to two sources, a center-sharing
partition, and union size at most five, matching the existing motif grammar.
## Current reviewer considerations

Source SHA-256: `c8f1c702550341633a5183fa20a56ff490d281433f9b452c23d05904cc22af91`.

# Decisions for 4dd7720cba5f

## D1 — Preserve the canonical Racket rule

- **Input choice:** No rule-source change; keep `RULE_HASH=d947d085ded3`.
- **Original rationale:** The baseline generator already matched the canonical
  outputs, and the authority/rule-smoke gates showed no execution defect. The
  defect was underdetermined training data, not the oracle.
- **Alternatives considered:** Rewrite the rule around the Python analyzer, or
  narrow the task to “copy one source motif.” Both would change or weaken the
  canonical semantics to fit deficient data.
- **Probe:** Canonical shortcut analysis found two wrong rules fitting all 10
  pairs; rule smoke and authority sync pass on the unchanged rule.
- **Failure mode / limitation:** A finite oracle comparison does not prove the
  Racket program is the only intended abstraction; it establishes the selected
  authority remained stable.

## D2 — Retain all nine pre-existing linked/extrapolated profiles

- **Input choice:** Keep five public-layout profiles and four lawful
  extrapolations as exact `scene_profile` controls.
- **Original rationale:** The baseline's choice rationale was not recorded. The
  profiles collectively preserve the demonstrated 5×5 frame grammar, public
  multiplicities, transpositions, and palette range.
- **Alternatives considered:** Replace the old distribution with only new union
  cases, or alter tile/frame size. Both would trade away canonical support to fix
  one ambiguity.
- **Probe:** Focused tests generate every exact profile, recover it through the
  analyzer, and verify override observability. The final override, profile-floor,
  diversity, and distribution gates pass.
- **Failure mode / limitation:** The task still fixes tile size at 5×5 because
  separator-band parsing and canonical motifs are all demonstrated there.

## D3 — Add one multi-source union profile per difficulty band

- **Input choice:** Split a center-sharing motif across two same-color source
  tiles: union sizes 3, 4, and 5 for easy, medium, and hard respectively.
- **Rationale:** This is the smallest legal intervention that separates true
  union semantics from both canonical-fitting rivals while staying within the
  existing motif grammar.
- **Alternatives considered:** Use three or more sources, disconnected fragments,
  noncentral motifs, or larger motifs. They add extrapolation risk without being
  needed to refute the reproduced shortcuts.
- **Probe:** Each new profile makes both `first_source_only` and
  `blank_targets_only` disagree with `solve_python`; focused tests cover 12 seeds
  per band. Semantic gate reports the witness on 189/600 draws.
- **Failure mode / limitation:** Coverage is intentionally limited to two source
  fragments, center-sharing partitions, and union size at most five.

## D4 — Schedule a union witness every third default draw

- **Input choice:** `sample_index % 3 == 0` selects the band's union profile;
  other slots retain the standard weighted distribution.
- **Rationale:** `EXAMPLES_NEEDED=3`; therefore every three consecutive draws,
  including cyclic starts, has a source-bound counterexample while two thirds of
  examples retain prior distribution breadth.
- **Alternatives considered:** Pure random witness frequency could leave some
  lessons ambiguous; all-union lessons would overrepresent the repair case.
- **Probe:** The reusable workspace probe checks 12 cyclic starts × 3 bands = 36
  windows. The 100-lessons-per-band census found both rivals refuted in all 300
  lessons and all 1,200 exact inputs unique.
- **Failure mode / limitation:** This guarantee assumes production assembles
  consecutive sample indices in groups of three. The probe records that policy;
  a different sampler must be audited separately.

## D5 — Declare executable rivals, witness, and identifiability

- **Input choice:** Expose `strict_canonical_like`,
  `multi_source_union_required`, two canonical shortcuts/semantic rivals, and
  `lesson_identifiable` from the generator.
- **Rationale:** A prose claim cannot be enforced by the shared semantic gate.
  Source-bound callables make canonical fit and generated refutation replayable.
- **Alternatives considered:** Test-only rival copies were rejected because they
  can drift from the generator contract.
- **Probe:** The semantic gate verifies both rival claims, all 10 canonical
  inputs, and 12/12 smoke lessons; the task-local probe iterates the declarations
  rather than a duplicated name list.
- **Failure mode / limitation:** Passing declared rivals is not a proof against
  all possible shortcuts. New credible rivals should be added as discovered.

## D6 — Repair portable tests and synchronize selected authority text

- **Input choice:** Locate canonical data through `reviewer_support`, hash
  whitespace-normalized rule text, and make selected `target_code` byte-exact to
  canonical in both active base solution records. Archival `raw_code` is
  unchanged.
- **Rationale:** The copied task-test runtime has a different directory layout;
  and repository `RULE_HASH` uses normalized text. Authority sync requires the
  selected source to be exact, not merely semantically equivalent.
- **Alternatives considered:** Hard-code another relative path, weaken the hash
  assertion, or alter canonical authority. Those would hide rather than repair
  the mismatch.
- **Probe:** TDD retained the expected red runtime failures, the intermediate
  implementation error, and final green evidence. Final result: 28 tests and 796
  subtests pass; authority execution parity passes.
- **Failure mode / limitation:** The two base JSON edits are textual selection
  sync only; they do not independently re-prove program semantics.

## D7 — Build a reusable cyclic curriculum probe

- **Input choice:** Add
  `workspace/probe_semantic_curriculum.py`, runnable in both source-tree and
  copied-runtime layouts.
- **Rationale:** The shared smoke sample and census do not rotate every small
  deterministic schedule window into query position.
- **Probe:** `checks/semantic-curriculum-probe.json` records canonical shortcut
  fit and all 36 cyclic windows.
- **Failure mode / limitation:** It tests the declared schedule and rivals, not
  arbitrary downstream shuffling or undeclared hypotheses.

## 2026-10-23 review-689546527b3652c2 — proposed parametric extension

Added a task-local, unapproved episode prototype under `workspace/parametric/`.
The one parameter is `destination_scope` with values `all_tiles` and
`empty_tiles_only`; `all_tiles` is the exact canonical/default program. Both
settings preserve separator parsing, frame-color grouping, and same-color offset
union. The alternative changes only the destination set, writing the union into
input-empty peers while leaving partial source interiors unchanged.

The prototype uses the existing lawful multi-source union profiles so every
retained pair distinguishes the settings. A deterministic seed chooses one
setting for the whole episode. Default episodes contain 3 identifying
demonstrations and 4 distinct queries, with counts exposed separately. Public
challenge IDs are hashes of visible bytes only; seeds, settings, programs, and
query labels stay private.

Retained evidence at `checks/parametric/destination-scope-v1/report.json` covers
seeds 0 and 2, both settings, 2 episodes, 14 pairs, and 28 selected/rival Racket
executions. Python/Racket parity, demonstration identifiability, per-query rival
disagreement, and within-episode input uniqueness all passed. The portable staged
task suite at `checks/parametric/task-tests-v1/result.json` passed 435 tests
(23 pytest items, 412 subtests). Canonical program SHA-256 remains
`83711946021311fb3b33477e3b2e385cc8f8f9a4c5831cfcaaa1660c0789888f`;
production generator SHA-256 remains
`c8f1c702550341633a5183fa20a56ff490d281433f9b452c23d05904cc22af91`.

Limit: this two-setting, two-seed receipt is bounded authoring evidence, not an
exhaustive rule proof, production approval, or training admission.

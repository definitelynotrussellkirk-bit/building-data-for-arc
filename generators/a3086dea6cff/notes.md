# Working notes: a3086dea6cff

## Review 2026-10-02

The frozen version generated individually valid pair-connector inputs, but its
lesson distribution was not identifiable: in an independent census of 540
sliding three-example windows, every window omitted at least one required
witness, 280/660 scenes omitted one orientation, and both strongest
canonical-fitting rivals survived every window.

Version 3.0.0 uses a deterministic three-profile schedule (`canonical`,
`triple_decoy`, `nonaligned_decoy`) while keeping layouts, colors, dimensions,
and segment choices seeded and varied. Canonical anchors exactly reproduce one
of the four observed source profiles. Both decoy profiles retain 2–4 ordinary
aligned pairs and both orientations.

The first repaired version passed the repository's complete battery but failed a
broader audit in 3/540 windows: a triple decoy's min-to-max span crossed an active
segment, so row-major paint order could hide the `connect_aligned_any_count`
rival's extra fill. The final placement rule keeps the entire implied triple
span off active segments. Focused regression and the wider audit are green.

Reusable evidence and tools:

- `workspace/generator-before.py` — frozen imported implementation;
- `workspace/audit_curriculum.py` — independent rule/rival/window probe;
- `tests/test_generator_a3086dea6cff.py` — generator and semantic regressions;
- `tests/test_curriculum_probe.py` — independent probe regression;
- packet `checks/a3086dea6cff_curriculum_before.json`,
  `checks/a3086dea6cff_curriculum_after.json`, and
  `checks/a3086dea6cff_curriculum_stress.json` — before/after/stress census;
- packet `checks/shortcut_counterexample_authority.json` — exact Racket-verified
  disagreement with the strongest count-agnostic shortcut.

Known tradeoffs: the three-profile order is predictable; dimensions are narrower
than the imported version; and the named rival set is not exhaustive. The Racket
program remains authoritative and unchanged.
## Current reviewer considerations

Source SHA-256: `b1484fb79f42b3fc3e2a92cfc9bcc2c7b83676d5e0cdfee5fcb50b291a19653f`.

# Distribution and implementation decisions

## D1 — Guarantee both connector orientations in every scene

- **Imported behavior/rationale:** the old generator sampled pair orientations;
  its comments said mixed orientations should pin the rule, but did not guarantee
  that property in a lesson.
- **Failure observed:** 280/660 frozen scenes omitted one orientation, and
  orientation-only rivals survived some windows.
- **Decision:** seed each scene with at least one horizontal and one vertical
  active segment.
- **Probe:** `workspace/audit_curriculum.py`; before/after reports under
  `checks/a3086dea6cff_curriculum_{before,after}.json`.
- **Rejected alternative:** simply increase random pair count. It raises the
  probability of mixed orientations but does not make the lesson invariant
  falsifiable.
- **Cost/limitation:** every scene is somewhat denser and one-pair scenes are no
  longer generated.

## D2 — Use a three-profile sliding curriculum

- **Decision:** `sample_index % 3` selects `canonical`, `triple_decoy`, or
  `nonaligned_decoy`; `EXAMPLES_NEEDED = 3`.
- **Rationale:** every three consecutive examples contain all required evidence,
  independent of the starting index.
- **Alternatives considered:**
  - random profile mixture: more varied, but can omit decisive evidence;
  - raise `EXAMPLES_NEEDED`: increases solve cost and still needs coverage
    guarantees;
  - put both decoys in every scene: maximally explicit but visually overloaded
    and less canonical-like.
- **Probe:** all 540 primary sampled sliding windows and all 1,800 stress
  windows are complete and reject all declared competitors in
  `checks/a3086dea6cff_curriculum_after.json` and
  `checks/a3086dea6cff_curriculum_stress.json`.
- **Cost/limitation:** deterministic profile order is learnable as a schedule and
  less distributionally diverse than a free mixture.

## D3 — Preserve a canonical-scale anchor in each lesson

- **Decision:** the canonical profile chooses one of the four observed canonical
  `(height, width, active-pair-count)` profiles exactly.
- **Rationale:** counterexamples alone can over-teach exceptional cases; each
  lesson should also contain a source-shaped positive anchor.
- **Measured effect:** exact canonical-profile support rose from 1/60 to 25/60;
  canonical-envelope support rose from 7/60 to 48/60.
- **Rejected alternative:** sample the full old 7–16 ranges and hope to hit source
  shapes. The frozen profile-floor result showed this was too sparse.
- **Cost/limitation:** the declared size ranges are narrower than the imported
  generator's ranges.

## D4 — Add a gapped collinear three-cell color

- **Decision:** one scheduled scene contains a color appearing exactly three
  times in one row or column, with gaps, and leaves it unchanged.
- **Rationale:** all canonical examples are consistent with the shortcut
  “connect any collinear repeated color,” because their active colors occur
  exactly twice.
- **Probe:** `connect_aligned_any_count` fits all four canonical pairs but is
  refuted by generated scenes; exact Racket-verified example is in
  `checks/shortcut_counterexample_authority.json`.
- **Rejected alternative:** use three scattered non-collinear cells. That would
  not directly distinguish count from alignment.
- **Failure and repair:** the first version allowed the triple's implied span to
  cross an active segment; later overwriting hid the rival on 3/540 windows.
  Triple placement now requires the whole implied span to avoid active segments.
- **Cost/limitation:** the decoy is intentionally conspicuous and may make exact
  count easier than in naturally occurring clutter.

## D5 — Add a non-aligned pair

- **Decision:** one scheduled scene contains a same-color pair sharing neither
  row nor column and leaves it unchanged.
- **Rationale:** the canonical examples cannot distinguish the intended rule
  from an L-connector that also handles non-aligned pairs.
- **Probe:** `connect_non_aligned_with_l` fits all canonical pairs but receives a
  generated counterexample in every three-example lesson.
- **Rejected alternative:** a diagonally adjacent pair. A one-step diagonal is
  too easy to dismiss as a special adjacency rule, so endpoints are separated
  by Manhattan distance at least four.
- **Cost/limitation:** only one explicit L-path convention is modeled as the
  rival, although the unchanged non-aligned pair also argues against other
  connection paths.

## D6 — Include interior crossings and preserve source paint order

- **Decision:** canonical and non-aligned profiles contain an interior
  horizontal/vertical crossing; endpoints may not lie on another segment.
- **Rationale:** crossings identify overwrite precedence. The rule mirror and
  fresh solve process colors by first row-major occurrence, so later segments
  overwrite earlier segments.
- **Rejected alternative:** prohibit all crossings. That avoids ambiguity in
  individual grids but leaves precedence untested.
- **Probe:** 386/600 final semantic-gate scenes contain a crossing, and the
  `vertical_wins_crossings` rival is explicitly refuted.
- **Cost/limitation:** crossing scenes require careful endpoint and decoy
  placement to prevent accidental evidence masking.

## D7 — Make override axes exact contracts

- **Decision:** declare only `grid_h=8..13`, `grid_w=10..15`, and `n_pairs=2..4`;
  accept every declared boundary in every difficulty; reject unknown keys; expose
  `observe_overrides`.
- **Failure observed:** baseline had 1,170 declared/default generation errors,
  no exact `n_pairs` provenance, and silently accepted unknown keys.
- **Probe:** final override stage accepted 8,100/8,100 draws over 90 cases and
  rejected the unknown key.
- **Rejected alternative:** keep band-local ranges while advertising a wider
  global domain. That is precisely the contract mismatch the baseline found.
- **Cost/limitation:** difficulty affects default sampling, not which explicit
  values are legal.

## D8 — Add semantic hooks and an independent audit tool

- **Decision:** declare strict canonical likeness, witnesses, named rivals,
  lesson identifiability, and a pure mirror; also build
  `workspace/audit_curriculum.py` without importing those semantic helpers.
- **Rationale:** self-checks establish shape validity, not teachability. An
  independent implementation reduces the chance that generator and checker
  share the same bug.
- **Probe:** semantic gate is green and the independent 540-window census is
  green.
- **Rejected alternative:** rely only on the repository semantic gate. Its
  capped 12-window lesson sample missed the rare paint-order masking defect.
- **Cost/limitation:** review instrumentation substantially increases the module
  size and still covers only named rival families.

## D9 — Keep the Racket authority unchanged

- **Decision:** change the input curriculum only; do not modify the canonical
  Racket solution.
- **Rationale:** canonical examples, rule hash, rule smoke, and direct
  counterexamples all agree with the existing authority. The defect was in
  coverage and contracts, not output semantics.
- **Probe:** final `rule_smoke`, `racket_lint`, and `authority_sync` are green.
- **Alternative rejected:** changing authority to fit generator artifacts would
  alter the task rather than repair its distribution.

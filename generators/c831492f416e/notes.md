# Working notes: c831492f416e

## 2026-09-28 generator review

### Findings in version 2.0.1

- The generator had no `RULE_HASH` pin.
- Eight public axes overstated the actual controls. Four palette textures were
  byte-identical aliases, two single-token axes were unprobeable, negative
  fixtures appeared in the ordinary valid texture domain, unknown keys were
  accepted, and the override gate reported more than sixteen thousand findings.
- Placement retried only 20 times per color, could silently return fewer pairs,
  and fell back to `[[0]]` instead of failing loudly.
- The ordinary distribution never taught exact-two/alignment preconditions or
  the canonical rule's numeric crossing precedence. The canonical test contains
  an interior crossing where color 7 overwrites color 5.
- No strict manifold, semantic witnesses, rival rules, or lesson-level
  identifiability contract was declared.

### Implemented design

- Replaced the eight contradictory controls with one exact, grid-observable
  `scene_profile` axis.
- Scheduled five profiles by `sample_index % 5`, so every consecutive
  five-example lesson is branch-complete regardless of start offset.
- Constructively place all scenes and raise on impossible placement; no partial
  pair count or fallback grid is allowed.
- Preserve canonical shape/palette signatures for four profiles and use one
  explicit three-color decoy profile. Declared `MIN_STRICT_FRAC = 0.80`.
- Added `rule_mirror`, `strict_canonical_like`, `analyze_grid`,
  `observe_overrides`, named rivals/witnesses, and `lesson_identifiable`.
- Added focused regression tests and `workspace/profile_audit.py` for future
  edits.

### Regression found during verification

The first semantic-gate run warned that a one-cell-gap witness sometimes fired
inside a crossing even though the higher-color segment overwrote that sole
interior cell. In the minimized easy-band case (`seed=156925347025477`,
`sample_index=6062`) the long-gap rival therefore matched the authority. A
failing regression test was added first; crossing spans now have distance at
least three, and the witness is restricted to the non-crossing `short_gap`
profile. The final gate verifies the rival disagreement on 60/60 sampled
firings.

### Final evidence

- Final battery: 12/12 green.
- Racket smoke: 120/120 applied; Python mirror parity 120/120; no crashes,
  identities, out-of-bounds outputs, mutations, or stateful replays.
- Semantic gate: strict 487/600 (81.2%); canonical accepted 5/5; witnesses 7/7;
  rival claims 7/7; lessons 12/12 identifiable.
- Override contract: 540/540 accepted, six cases over three bands, zero
  findings; unknown keys rejected.
- Task-local census: 1,500/1,500 unique inputs and outputs over 100 seeds per
  band/profile; exact 300-per-profile balance; zero canonical mismatches,
  observer mismatches, endpoint risks, lesson failures, or surviving rivals.
- Repository Python suite: 104 passed, 28 Racket-dependent tests skipped when
  Racket was not on `PATH`. A second all-Racket run exceeded ten minutes after
  five tests; the task-specific Racket battery remained fully green.

### Remaining limitations

- The canonical Racket source still has style-only `dummy-let-binding` and
  `style-not-eq` linter findings. It is synchronized and execution-equivalent
  across all authorities, so changing it would create a needless rule-hash and
  authority patch.
- The five profiles are intentionally a compact semantic curriculum, not a
  broad free-form distribution. New profiles should only be added with an
  observable contract, a rival they uniquely refute, and a consecutive-window
  schedule test.
## Current reviewer considerations

Source SHA-256: `c9befa230e1e4f8682419669ccfd8bc6e24815c197750928229ce2568368fb1e`.

# Decisions for c831492f416e

## D1 — Keep the canonical Racket authority unchanged

**Original rationale:** The source imported an existing bank solution; no local
rationale was recorded. The authority fills exactly-two aligned colors and
processes colors in ascending numeric order.

**Decision:** Pin its normalized hash (`91f9e86ee830`) and mirror it in Python,
but do not edit the Racket source.

**Alternatives considered:** Rewrite the style-only dummy `let`, change the
output construction to copy the input, or avoid crossing semantics in generated
inputs.

**Probe:** All five canonical pairs match the Python mirror; Racket smoke mirror
parity is 120/120; authority sync reports one exact group and execution parity.

**Failure modes / limits:** The Racket linter still reports two nonblocking style
findings. Editing them would change authority hashes without improving behavior.

## D2 — Expose only `scene_profile`

**Original rationale:** Unknown. Version 2.0.1 declared eight generic axes,
including aliases, constants, and negative fixtures.

**Decision:** Replace them with one semantic axis whose requested value is
recoverable from the returned grid.

**Alternatives considered:** Repair all eight axes; keep dimensions and pair
count as separate controls; mark dead controls diagnostic.

**Probe:** Override contract passes 540/540 draws with six cases, three bands,
zero findings, and unknown-key rejection. `observe_overrides` exactly recovers
all requested profiles in focused and 1,500-draw census tests.

**Failure modes / limits:** External callers using removed legacy overrides must
migrate to `scene_profile`. Preserving misleading compatibility would be worse
than a loud break.

## D3 — Use a five-profile consecutive-window schedule

**Original rationale:** Version 2.0.1 sampled independent disjoint pair scenes;
there was no lesson schedule.

**Decision:** Cycle the five profiles by `sample_index % 5` and set
`EXAMPLES_NEEDED = 5`.

**Alternatives considered:** Independent random profile sampling; a four-profile
schedule without the minimum-gap case; encoding multiple semantic branches in
one dense scene.

**Probe:** Every five consecutive indices covers all profiles, including all
start offsets tested. The semantic gate materializes 12 lessons using its own
stride and finds 12/12 identifiable.

**Failure modes / limits:** A downstream exporter that does not preserve
consecutive sample indices could destroy coverage. `QUESTION_ANSWER.md`
proposes a final-materialized-lesson gate for that boundary.

## D4 — Preserve canonical shape/palette support

**Original rationale:** The old difficulty bands expanded grids from about
8×8 to 15×15 and did not link them to canonical signatures.

**Decision:** Draw from the five canonical shapes. Four profiles use background
plus two nonzero colors; the precondition profile intentionally uses three
nonzero colors. Declare `MIN_STRICT_FRAC = 0.80`.

**Alternatives considered:** Exact replay of canonical dimensions only per
band; arbitrary larger hard grids; treating the decoy profile as strict.

**Probe:** Canonical profile support rises from 6/60 to 44/60; strict semantic
support is 487/600 (81.2%); all five canonical inputs are accepted.

**Failure modes / limits:** Shape diversity is lower than the original broad
range, although layouts and colors remain fully diverse (100% unique in both
300-pair and 1,500-draw censuses).

## D5 — Generate exactly one horizontal and one vertical valid pair

**Original rationale:** Canonical examples each contain two aligned colors, one
horizontal and one vertical.

**Decision:** Keep that morphology in the four ordinary profiles. Use
constructive candidate selection and forbid endpoint overwrite.

**Alternatives considered:** Two same-orientation pairs; 2–4 random pairs;
bounded retry placement with a fallback.

**Probe:** All generated ordinary inputs have exactly two valid pairs, no
endpoint risk, and a nonidentity output. Self-check accepts all canonical inputs
and rejects destructive mutations except color relabelings, which are lawful
symmetries.

**Failure modes / limits:** The generator does not teach arbitrary many-pair
scenes. The `connect_only_lowest_valued_pair` rival is still refuted by every
ordinary two-pair profile.

## D6 — Teach numeric crossing precedence in both directions

**Original rationale:** The old generator explicitly prevented overlap, hiding
the selected authority's sorted-color overwrite behavior.

**Decision:** Include one profile where the horizontal color is higher and one
where the vertical color is higher. Cross only at an interior cell.

**Alternatives considered:** Continue forbidding crossings; teach one crossing
direction only; define fixed axis precedence instead of following authority.

**Probe:** The Python mirror matches Racket on 120/120 generated draws. Both
fixed-axis rivals and the low-color-wins rival are refuted, with 60/60 verified
disagreements for each corresponding witness sample.

**Failure modes / limits:** Crossing behavior depends on numeric color order,
not semantic color identity. Color remapping that changes order can change the
answer and is therefore not a lawful augmentation.

## D7 — Separate the minimum-gap witness from crossings

**Original rationale:** No explicit original minimum-gap rationale was recorded;
the old prose required endpoint distance at least two.

**Decision:** Give `short_gap` a noncrossing segment with exactly one interior
cell. Crossing profiles require endpoint distance at least three.

**Alternatives considered:** Let any profile contain short spans; define the
witness as mere input presence; remove the gap rival.

**Probe:** The first semantic run produced a minimized counterexample where the
only short interior cell was overwritten and the rival survived. A failing test
was added first; the final rival claim is 60/60.

**Failure modes / limits:** The witness is profile-specific by design. If the
profile classifier changes, the witness and regression test must change with it.

## D8 — Include one lawful precondition-decoy scene

**Original rationale:** Version 2.0.1 exposed `no_pairs`, `single_endpoint`, and
`off_axis_pair` as ordinary negative textures, even though self-check rejected
them.

**Decision:** Remove all destructive textures. Instead, create one valid scene
with a connectable pair, a 45-degree diagonal pair, and an aligned triple. The
rule fires on the valid pair and preserves the decoys.

**Alternatives considered:** Keep invalid fixtures outside `AXES`; use a lone
single cell; place each precondition in a separate profile.

**Probe:** The decoy profile passes self-check, is nonidentity, and refutes both
`connect_diagonal_pairs` and `connect_any_aligned_color_with_at_least_two_cells`
on 60/60 checked firings.

**Failure modes / limits:** This profile is intentionally outside the exact
canonical palette signature and accounts for the 20% non-strict share.

## D9 — Fail loudly instead of returning partial scenes

**Original rationale:** The old code used 20 retries per pair and returned
`[[0]]` when fewer than two pairs were placed.

**Decision:** Enumerate legal candidates, select constructively, and raise a
clear `RuntimeError` if no scene can be built.

**Alternatives considered:** Increase retries; silently reduce requested pair
count; retain a canned fallback.

**Probe:** 1,500 census draws and all battery draws complete with no crash,
partial profile, self-check failure, or fallback signature.

**Failure modes / limits:** A future shape smaller than the current canonical
minimum could empty a candidate set and will now fail immediately, as intended.

## D10 — Add a task-local semantic census

**Original rationale:** No future-agent diagnostic existed beyond shared gates.

**Decision:** Add `workspace/profile_audit.py` with a deterministic JSON report
and nonzero exit on failure.

**Alternatives considered:** Rely only on the shared battery; add an ad hoc
notebook; duplicate the Racket runner.

**Probe:** The 100-seed census checks 1,500 draws and passes with exact profile
balance, 0.80 strict rate, and no semantic failures.

**Failure modes / limits:** The tool uses the Python mirror and final stored
canonical outputs; Racket parity remains the shared battery's responsibility.

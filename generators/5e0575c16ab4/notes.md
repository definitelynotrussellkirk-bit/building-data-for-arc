# Working notes: 5e0575c16ab4

## Review review-01c692811d9c592c

The canonical Racket authority was not edited. Candidate generator version is
`2.0.0`; selected rule hash remains `8cad321146ee`.

### Baseline diagnosis

The imported version-1.1 sampler emitted only globally unique horizontal endpoint
pairs. That made the strongest rival, "apply the rule independently per row,"
indistinguishable from the intended global-count rule. It also did not exercise
blocked interiors, vertical pairs, or colors appearing three times.

The immutable before battery measured 7 green, 2 advisory, and 3 failed stages.
The major concrete failures were a missing rule pin, dead/overlapping textures,
weak canonical-profile support, no semantic contract, 25,430 override findings,
and silent acceptance of an unknown override key.

### Implemented curriculum

Every four-example schedule cycle contains:

1. `canonical` — one or two valid positive pairs;
2. `global_repeat` — one color makes two blank row-local pairs and therefore has
   four global occurrences;
3. `blocked_bridge` — a two-occurrence horizontal pair has a foreign blocker;
4. `count_alignment` — one vertical pair and one three-cell row remain unchanged.

Canonical anchors use source-like dimensions; other profiles use difficulty-banded
sizes. The four public axes are exact and observable. `pairs` and `texture` are
validated compatibility aliases, not separately advertised axes.

### TDD/regressions

The tests were written to fail first for the missing rule pin, exact overrides,
profile observability, shortcut counterexamples, schedule coverage, canonical
anchors, replay purity, and malformed controls. One implementation iteration
left the vertical-pair witness vulnerable to an endpoint occupying its bridge;
reserving that column fixed the failing test. Final focused result: 12 passed.

### Semantic evidence

Named rivals are identity, row-local pairs, ignore-blank-guard, connect-vertical-
pairs, and row-extremes-for-repeated-color. Witnesses cover positive fill,
global count, blank interior, same row, and exactly two occurrences.

Final semantic battery: 600/600 strict draws, 5/5 witnesses, 5/5 rival claims,
and 12/12 identifiable four-demo lessons. `workspace/shortcut_probe.py` records
an exact row-local counterexample and verifies that ordinary `global_repeat`
draws expose the same disagreement.

### Verification and limitations

The final source-bound generator battery is 12/12 green. The one-shot wrapper was
interrupted by the outer process cap; a documented per-stage/`--resume` run in one
persistent source-pinned runtime produced the final aggregate. The full repository
pytest command timed out in an unrelated dataset-export test after 25 passes; no
assertion failure was observed. Focused tests, Racket parity, authority checks,
and every required generator stage passed.
## Current reviewer considerations

Source SHA-256: `bc9f62c6e3e8748dff84a17bae2b0756d8421d148c3fc682797441ce04698903`.

# Design decisions: 5e0575c16ab4

## D1 — Preserve and pin the selected rule

**Choice.** Keep the canonical transformation unchanged and add `RULE_HASH = "8cad321146ee"` plus a Python mirror for tests.

**Rationale.** The original generator's positive examples agreed with the selected authority; the defect was distributional, not a demonstrated rule error. The before rule-smoke, grammar, Racket-lint, and authority-sync stages were already green.

**Probe.** Canonical pairs are checked against the mirror in the focused suite, and the final Racket smoke measured 120/120 parity.

**Rejected alternative.** Editing the Racket rule to match the old prose would change authority without evidence and would not cure the missing negative branches.

## D2 — Use four explicit teaching profiles

**Choice.** Cycle `canonical`, `global_repeat`, `blocked_bridge`, and `count_alignment` by `sample_index mod 4`.

**Rationale.** A four-demo ARC lesson can now expose the positive branch and every material guard exactly once per window. A deterministic schedule is stronger than hoping independent random distractors happen to cover all guards.

**Failure modes addressed.** Row-local pairing, ignoring interior blockers, connecting vertical pairs, and filling colors that occur three or four times.

**Probe.** `test_every_four_example_window_contains_all_profiles_and_is_identifiable` checks overlapping windows; the semantic gate found 12/12 generated lessons identifiable.

**Rejected alternatives.** Pure random profile choice could omit a guard from a lesson. Putting all decoys in every example would make scenes cluttered and reduce attribution of which condition matters.

## D3 — Keep canonical anchors while broadening geometry

**Choice.** Canonical-profile draws use heights 5 or 8 and widths 7, 8, or 9; non-anchor draws use difficulty-banded ranges up to 14-by-18.

**Rationale.** Small anchors keep a visible bridge to the canonical demonstrations while broader dimensions prevent fixed-shape shortcuts and exercise placement logic.

**Probe.** The profile-floor result improved from 4/60 exact and 12/60 envelope, including zero hard-band exact support, to 8/60 exact and 16/60 envelope with support in all three bands.

**Rejected alternatives.** Always using canonical dimensions would encourage shape memorization. Eliminating anchors would make the generator less visibly tied to the source task.

## D4 — Expose only exact, observable override axes

**Choice.** Replace nine partly decorative axes with `grid_h`, `grid_w`, `positive_pairs`, and `profile`. Every accepted override is observable from the resulting grid. Unknown keys and out-of-range values fail loudly. Legacy `pairs` and `texture` aliases are normalized only when consistent.

**Rationale.** The original metadata promised controls that were dead, silently ignored, or incompatible with actual difficulty ranges. A smaller truthful API is better than a large nominal search space.

**Probe.** The override stage moved from 25,430 findings and an accepted unknown key to 26,190 accepted draws with zero findings/warnings and unknown-key rejection.

**Rejected alternatives.** Retaining `palette_kind`, `density`, `position_bias`, `palette_size`, and `n_distinct_colors` would preserve labels without independent semantic effects. Negative fixtures were not kept in the ordinary texture domain because ordinary samples should remain valid lessons.

## D5 — Encode competitors as executable semantics

**Choice.** Add rivals for identity, row-local pairing, ignoring blockers, connecting vertical pairs, and filling row extremes for repeated colors. Add witnesses for positive filling, global count, blank bridge, row alignment, and exactly-two count.

**Rationale.** Distribution quality should be judged by whether generated examples distinguish the intended transformation from plausible alternatives, not only by syntactic diversity.

**Probe.** The semantic gate checked 600 lawful draws, verified every rival claim, and found all 12 sampled lessons identifiable. The task-local `shortcut_probe.py` provides a stable concrete counterexample for the strongest rival.

**Rejected alternative.** A prose-only claim about shortcut resistance would be hard for future agents to replay and easy to regress.

## D6 — Separate grammar validity from teaching-profile recognition

**Choice.** `self_check` requires rectangular ARC grids, declared dimensions, one or two genuine positive pairs, and one recognizable profile. `rule_mirror` still handles the selected rule generally, including identity cases such as adjacent endpoints.

**Rationale.** The authority can define more inputs than the training distribution should emit. Ordinary generated lessons need a visible transformation and an interpretable branch profile.

**Failure mode.** Treating no-op degenerates as ordinary valid samples previously mixed invalid or uninformative fixtures into the declared texture domain.

## D7 — Reserve the vertical decoy column

**Choice.** In `count_alignment`, choose the vertical pair's column first and prohibit positive endpoints and the three-cell row endpoints from using it.

**Rationale.** An early TDD run found that an unrelated endpoint could accidentally occupy the vertical bridge, weakening or misclassifying the same-row witness. Reserving the column makes the intended counterexample structural rather than probabilistic.

**Probe.** The initially failing focused test became green, and the final same-row witness fired in 138/600 semantic draws across all bands.

**Rejected alternative.** Retrying after collisions would be more complex and could obscure deterministic draw provenance.

## D8 — Retain failures and recovery evidence

**Choice.** Keep the failed baseline battery, the interrupted one-shot after attempt, and the initial audit staging failure; use documented recovery paths rather than deleting inconvenient evidence.

**Rationale.** These files distinguish generator defects from harness/runtime issues and make the final claims auditable.

**Limitation.** The repository-wide suite timed out in an unrelated dataset test, so I do not claim full-repository pytest completion.

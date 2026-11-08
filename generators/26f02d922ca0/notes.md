# Working notes: 26f02d922ca0

## 2026-09-28 review repair

### Authority and ambiguity

- Canonical Racket rule hash: `2ec8ce6b9b7f`; the authority was not changed.
- All three canonical demonstrations have candidate colors in the same role:
  colors 3 and 4 are positive, colors 5 and 6 are negative, and the output is
  `[8,8,0,0]`. Therefore three wrong rules fit every canonical pair:
  `colors_3_and_4_are_matches`, `first_two_candidates_match`, and
  `fixed_canonical_vector`.
- The retained probe at `workspace/review_probe.py` emits exact JSON
  counterexamples and rival outputs. Seed 91, hard, sample index 0 is a `9×16`
  canonical-profile example with reading-order colors `[5,3,6,4]` and authority
  output `[8,0,8,0]`; all four declared rivals disagree.

### Generator design

- Version raised from `2.0.2` to `3.0.0`.
- Public axes were reduced to truthful, exact, observable dimensions:
  `grid_h=9..18` and `grid_w=12..24`. Unknown overrides now fail loudly.
- Connected shapes are selected from a deterministic 3×3 library. Five objects
  fit the minimum `9×12` canvas in separated 3×3 slots without retry logic.
- `sample_index % 4` schedules canonical-color, non-prefix-order, mirror-only,
  and variable-candidate-count profiles. Every four-example lesson contains all
  named semantic witnesses.
- `self_check` validates the broad executable teaching grammar;
  `strict_canonical_like` separately models the empirical canonical manifold.
- The ordinary output codomain is finite and declared: 21 mixed-label states
  across 2-, 3-, and 4-candidate examples.

### Before / after evidence

Baseline defects:

- lint: missing `RULE_HASH`; fictitious/unprobed `position_bias`;
- strict defect lint: degenerate textures in the ordinary domain and four dead
  helpful textures;
- canonical-profile support: `0/60` exact and `0/60` envelope;
- semantic gate: `NO_CONTRACT`;
- override contract: 67,911 findings across 63,360 draws, including silently
  ignored dimensions and an accepted unknown key.

After repair:

- focused pytest: `16 passed`;
- battery: `12 green / 12`, subject SHA16 `d7d26c58c61cb3e1`, generator SHA-256
  `9bcae6b6715ce0ca185d67f3ae9e5cb92507af24b30f385eb71251456b175caa`;
- profile floor: 16/60 exact hits, with support in easy/medium/hard;
- semantic gate: 600 draws, 4/4 witnesses, 4/4 rival claims, 12/12 lessons;
- override contract: 13,860 accepted draws, 154 cases, zero findings;
- rule smoke: 120 applications, zero crashes, A–B–A reentrant, mirror 120/120.

### Limitations

- The answer space is intrinsically small; declaring 21 ordinary states makes
  this explicit rather than pretending output diversity is unbounded.
- Objects are intentionally limited to connected 3×3 masks. The Racket rule can
  accept larger shapes, but larger masks are not needed to distinguish the
  known canonical rivals and would make the minimum-canvas contract harder.
- Canonical-profile support reproduces the observed `9×16`, six-color, four-
  candidate manifold, not the exact canonical grids.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `9bcae6b6715ce0ca185d67f3ae9e5cb92507af24b30f385eb71251456b175caa`.

# Design Decisions: 26f02d922ca0

## D1. Preserve the Racket authority

**Choice.** Keep the canonical rule unchanged and pin its normalized hash as
`RULE_HASH = "2ec8ce6b9b7f"`.

**Original rationale.** Unknown. The baseline generator omitted the pin, but
its ordinary outputs already executed correctly under the canonical rule.

**Alternatives considered.** Rewrite or simplify the Racket; duplicate the rule
only in Python; leave the source unpinned.

**Probe.** Canonical pairs pass the Python mirror and the Racket authority;
rule smoke applies 120 generated inputs without a crash; authority sync and
execution parity pass.

**Failure mode avoided.** A later canonical-rule replacement silently leaves a
stale generator attached to the wrong task.

## D2. Design against the strongest canonical shortcuts

**Choice.** Treat fixed color roles, fixed first-two ordering, fixed
`[8,8,0,0]`, and exact-key-only matching as explicit rival rules.

**Original rationale.** The baseline claimed that colors, positions, and match
roles varied freely, but did not measure whether those variations actually
falsified a rival.

**Alternatives considered.** Rely on random generation to eventually produce a
counterexample; test only morphology; declare the canonical ambiguity without
changing the curriculum.

**Probe.** All three declared canonical shortcuts fit every real canonical pair.
Each rival is contradicted by named generated witnesses, and the semantic gate
verifies every witness-to-rival claim using the Racket authority.

**Limitation.** The finite rival set is not a proof against every possible
learned heuristic; it covers the strongest simple hypotheses exposed by the
canonical data and task structure.

## D3. Use a deterministic four-profile schedule

**Choice.** Let `sample_index % 4` choose one of four profiles: canonical color
conflict, non-prefix ordering, mirror-only relation, or variable candidate
count.

**Original rationale.** Unknown. The old generator sampled roles from one broad
random path.

**Alternatives considered.** Independent Bernoulli witnesses; one highly
constrained universal example; a larger curriculum state machine.

**Why this choice.** Four consecutive examples are the unit consumed by
`lesson_identifiable`, so deterministic profile coverage gives every lesson a
known semantic purpose without retries or rare-event assumptions.

**Probe.** Every seed and every difficulty band passes the four-profile test;
12/12 sampled lessons are identifiable.

**Failure mode avoided.** A batch contains four superficially varied examples
that all preserve the same wrong rule.

## D4. Anchor one profile to the canonical manifold

**Choice.** Profile 0 emits a `9×16` grid with palette
`{0,2,3,4,5,6}`, four candidates, 4–5-cell objects, and exactly two positives,
while deliberately permuting color roles and reading order.

**Original rationale.** The baseline had zero exact or envelope support for the
only observed canonical profile.

**Alternatives considered.** Literal canonical copies; a profile opt-out;
matching only independent morphology marginals.

**Probe.** The strict profile gate reports 16/60 exact hits with nonzero support
in easy, medium, and hard. The retained seed-91 example is canonical-profile
compatible but makes every rival disagree.

**Failure mode avoided.** A learner can separate “generated” from “real” by
canvas/palette profile, or sees canonical-looking scenes only with canonical
shortcut roles.

## D5. Expose only exact dimensions as public axes

**Choice.** Public `AXES` now contains only `grid_h=9..18` and
`grid_w=12..24`. Candidate count, shape size, relation pattern, color
assignment, and placement are internal curriculum choices. Unknown keys raise.

**Original rationale.** Unknown. The baseline declared seven controls but used
one unkeyed RNG path and silently ignored many requested values.

**Alternatives considered.** Repair every old axis; declare all controls as
merely diagnostic; accept unknown keys for compatibility.

**Why this choice.** A public axis is a contract, not a description. Dimensions
are independently meaningful, exactly observable, and valid across every band
and profile. The removed controls were coupled to semantic schedules and could
not honestly be promised as arbitrary combinations.

**Probe.** All four dimension corners work in every profile and band, including
`9×12`; the official matrix accepts 13,860/13,860 draws with zero findings.

**Failure mode avoided.** Dataset requests appear to succeed while producing a
different distribution than requested.

## D6. Enumerate connected 3×3 shapes

**Choice.** Build a deterministic library of all normalized 4-connected masks
of area 3–7 inside a 3×3 box; select asymmetric keys when a mirror witness is
needed.

**Original rationale.** The old generator used random shape construction and
placement behavior that was harder to reason about at axis boundaries.

**Alternatives considered.** Random walks with retries; a hand-written template
list; arbitrary larger bounding boxes.

**Why this choice.** Enumeration is tiny (`2^9` masks), deterministic under all
hash seeds after sorting, and guarantees exact/nonmatch/mirror choices exist.

**Probe.** Hash-seed lint passes; minimum-canvas tests pass; rule smoke reports
input purity and 120/120 Python-oracle parity.

**Limitation.** Larger shapes accepted by the authority are not generated.

## D7. Place objects in separated slots

**Choice.** Use one-cell-separated 3×3 slots rather than repeated random
placement attempts.

**Original rationale.** Unknown.

**Alternatives considered.** Retry until non-overlap; rejection sampling;
packing arbitrary bounding boxes.

**Why this choice.** The minimum `9×12` canvas deterministically supports the
key plus four candidates, and separation guarantees that same-color or
adjacent objects never merge into accidental components.

**Probe.** All boundary dimension/profile/band combinations pass self-check and
exact override observation.

**Failure mode avoided.** Rare placement failure, component merging, or hidden
clamping at small dimensions.

## D8. Separate executable grammar from canonical profile

**Choice.** `self_check` validates the broad rule-bearing grammar;
`strict_canonical_like` validates the empirical canonical manifold.

**Original rationale.** The old self-check was strong for ordinary structure
but provided no profile signal.

**Alternatives considered.** Make `self_check` reject every noncanonical size;
put profile logic only in an external script.

**Why this choice.** The Racket rule is valid on a broader class than the three
canonical scenes. Conflating “lawful” with “looks canonical” would delete useful
variation or make degenerates appear lawful.

**Probe.** All canonical inputs pass both; ordinary varied sizes pass
`self_check`; only the scheduled anchor profile passes the strict manifold.

## D9. Declare the finite output codomain

**Choice.** Set `EXPECTED_OUTPUT_CODOMAIN = 21` and generate every mixed-label
state supported by 2–4 candidates, excluding only all-zero/all-eight ordinary
lessons and the canonical fixed vector from the four-candidate random pool.

**Original rationale.** The baseline summary noted low cardinality but did not
make the exact contract machine-readable.

**Alternatives considered.** Inflate input candidate count solely for output
variety; tolerate generic low-diversity warnings; include uninformative all-
match/all-nonmatch ordinary cases.

**Probe.** Lint recognizes the full finite codomain; rule smoke observes 14 of
21 in 120 applications; diversity passes.

**Limitation.** Output diversity remains intrinsically small because the task's
answer is a short binary vector.

## D10. Retain a machine-checkable review probe

**Choice.** Add `workspace/review_probe.py`, producing stable JSON with exact
grids, oracle outputs, rival outputs, fired witnesses, authority hash, source
hash, and canonical-shortcut fit checks.

**Original rationale.** No reusable task-local semantic probe existed.

**Alternatives considered.** Put one hand-copied example only in prose; depend
on the full battery for every future inspection.

**Probe.** Its subprocess regression test passes, the seed-91 report is retained
under `checks/after-probe/`, and its main example was independently replayed
through Racket.

**Failure mode avoided.** A future agent repeats the same semantic archaeology
or copies an unverified counterexample into a report.

## Review review-666e86ed85a2b7e1 — native parametric family

- Preserved the byte-exact canonical source-or-horizontal-mirror flag program and unchanged base `generator.py`.
- Added `report_mode={all_matches, match_count_pointer}`. The alternate computes every candidate match flag, counts the matches, then emits a one-hot row at that one-based candidate index.
- Declared support: 4–6 demonstrations and exactly four controller-side queries; inputs are setting-neutral and prefix-stable. Four examples are required because fewer leave count-pointer rivals alive.
- The minimum curriculum separates canonical all-flags, fixed/first/last-match pointers, nonmatch count, and first-match-count rivals.
- Bounded audit: 192 episodes / 290 distinct inputs / 48 protected-Racket evaluations / zero failures; substantive 30×30 case has 117 nonzero cells, four candidates, and three matches.
- Authoring preflight and causal witness passed; the wrong-intermediate replay substitutes nonmatch count for match count and changes the selected position. Public one-query projection, first-turn privacy, and hidden-field invariance checks passed.
- Updated the existing test to resolve the repository root through `reviewer_support.find_root`, eliminating fixed-parent-path dependence without changing generator behavior.
- Current state is reviewer-ready only. Owner source review, native qualification, fresh acceptance, and training admission remain pending.

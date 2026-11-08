# Working notes: a178821cc6bf

## 2026-10-02 review-b63381328c4badce

### Root cause

The imported generator modeled a fabricated separator and generated `h x 9`
inputs (`4 + separator + 4`).  Every canonical input is `4 x 8` with adjacent
4-column halves, so `self_check` rejected all six canonical inputs and the
generator's right-panel offset was wrong for this task.  The apparent prior
"independent panel" fix improved diversity only inside that incorrect geometry.

### Preserved rule

The canonical rule is unchanged: at output `(r,c)`, emit `4` exactly when input
`(r,c)` and `(r,c+4)` are both zero.  `RULE_HASH` is `ff2f0d5fbd0c`.  The active
base `racket_target.target_code` was synchronized byte-for-byte to the canonical
program; the historical executable `raw_code` remains preserved.

### Distribution design

- True input geometry is `h x 8`, no separator.
- Each panel has background `0` plus exactly one nonzero, non-`4` color.
- Every ordinary input contains `00`, `10`, `01`, and `11` aligned states.
- `both_zero_count` is exact and observable in `1..8`; six layout values have
  exact observable state-order signatures.
- Even/odd sample indexes alternate different/same panel foreground colors.
  Every consecutive two-example lesson therefore includes both relations and
  a same-color `11` witness; periodic 4-row draws separately anchor the
  canonical profile in every difficulty band.
- Every fourth draw in every difficulty band uses height `4`; easy/medium also
  retain additional even-index anchors.  This preserves measurable support for
  the canonical `(4,8,3-color)` profile while non-anchor draws broaden scale.

### Strongest canonical shortcut

All canonical examples use different left/right foreground values.  Therefore
`left_value == right_value` is equivalent to "both are zero" on canonical data:
nonzero aligned pairs are `6` versus `5`, never equal.  A same-color `11` pair
breaks this equivalence.  The generator declares that rival as
`CANONICAL_SHORTCUTS["raw_value_equality"]`, alternates a same-color witness into
every two-example window, and exposes task-linked semantic witnesses/rivals to
the semantic gate.

### Regression boundary

Do not reintroduce a separator, allow color `4` in the input, remove either
one-sided occupancy state, or randomize palette relation without preserving the
two-draw coverage guarantee.  If `EXAMPLES_NEEDED` or the schedule period
changes, exhaustively retest all sliding windows and named competitors.
## Current reviewer considerations

Source SHA-256: `27b24a2de22bc10ad14f247234c6bfdd2b83d94c2e1013f43ae084141cf32f68`.

# Design decisions: a178821cc6bf

## D1. Restore the canonical adjacent 4+4 geometry

**Input choice.** Inputs are `h x 8`: columns `0..3` are the left panel and
`4..7` are the aligned right panel. There is no separator.

**Original rationale.** Unknown. The imported version described `h x 9` with a
colored separator and indexed the right panel at `c+5`. That model contradicted
all six canonical inputs, which are `4 x 8`, and caused `self_check` to reject
every canonical pair.

**Alternatives considered.** Preserve the separator as a broader synthetic
variant; accept both widths; infer panel offset from width. All were rejected.
The canonical program has fixed output width 4 and fixed right offset `+4`, so
a width-9 grammar is not a lawful variation of this rule.

**Probes.** The before battery rejected 6/6 canonical inputs and reported zero
canonical-profile support. The focused canonical regression now accepts all six
and checks exact Python-mirror outputs without mutating inputs. Racket-backed
self-check, smoke, parity, and profile gates pass after the repair.

**Failure modes / limitations.** The grammar intentionally does not accept
separator-bearing inputs or panels wider than four columns, even though a
related generalized NOR task could be defined.

## D2. Preserve the rule and make its identity explicit

**Input/output rule.** For each row and panel column, output `4` iff both aligned
input cells are zero, else `0`. The canonical rule hash is
`ff2f0d5fbd0c`.

**Original rationale.** The canonical Racket program solved every public pair
and the duplicate base solution was behaviorally equivalent. The defect was in
the generator geometry, not the rule.

**Alternatives considered.** Rewrite or generalize the Racket rule; make width
dynamic; switch to raw equality. Rejected because they either alter authority
semantics or encode a canonical-data shortcut.

**Probes.** `rule_mirror` matches all six canonical outputs. The Racket smoke
and source-parity stages pass across generated samples. `RULE_HASH` is now
declared and tested.

**Failure modes / limitations.** The Racket rule assumes at least eight input
columns. Distribution legality remains the generator/self-check's job.

## D3. Require all four occupancy states in every ordinary input

**Input choice.** Every ordinary scene contains at least one `00`, `10`, `01`,
and `11` aligned pair; `00` count is exactly controlled in `1..8`.

**Original rationale.** The imported generator guaranteed only at least one
`00`. That permits one-panel complement, equality, OR, XOR, and count-only
interpretations on unlucky examples.

**Alternatives considered.** Rely on aggregate random coverage; require only one
of `10`/`01`; distribute witnesses across a lesson rather than each example.
Requiring all four in each scene is simpler, deterministic, and makes every
single example informative about the local truth table.

**Probes.** A 160-draw census in each difficulty band checks all four states,
input/output diversity, and answer-color exclusion. Named rivals are exercised
by the semantic gate and every ordinary draw is strict-canonical-like under the
declared grammar.

**Failure modes / limitations.** The resulting examples are deliberately
pedagogical and may be easier than natural sparse examples. Very small or
single-branch cases are available only as rejected negative controls, not
ordinary training items.

## D4. Alternate different-color and same-color panels

**Input choice.** `schedule_profile(sample_index)` alternates `different` and
`same` panel foreground relations. `EXAMPLES_NEEDED = 2`, so every consecutive
two-demo window contains both.

**Original rationale.** All canonical inputs use `6` on the left and `5` on the
right. Consequently raw value equality is identical to occupancy-NOR on the
canonical corpus: only `(0,0)` has equal raw values. This is the strongest
canonical-surviving shortcut.

**Alternatives considered.** Always use distinct colors to mimic canonical;
always share one color; choose relation randomly. Distinct-only preserves the
shortcut, same-only loses canonical palette support, and random choice gives no
sliding-window guarantee.

**Probes.** The exact generated witness in `QUESTION_ANSWER.md` has same-color
`11` pairs where raw equality outputs `4` but the rule outputs `0`.
`test_two_consecutive_examples_refute_raw_value_equality_shortcut` exhausts
multiple start residues, and the semantic gate verifies the named canonical
shortcut against the Racket authority.

**Failure modes / limitations.** Relation is scheduled rather than exposed as a
separate override axis. Explicit `left_color` and `right_color` overrides may
choose either relation; the schedule guarantee concerns default lessons.

## D5. Keep broad scale while anchoring every difficulty band

**Input choice.** Heights span `3..18`; non-anchor ranges are easy `3..7`,
medium `5..12`, hard `10..18`. Every fourth sample is a 4-row,
different-color canonical-profile anchor in every band; easy/medium have
additional even-index anchors. `both_zero_count` ranges vary by difficulty.

**Original rationale.** The first repaired version anchored only easy/medium.
The profile floor then passed pooled support but correctly failed hard-band
coverage.

**Alternatives considered.** Make every draw 4 rows; remove canonical anchors;
anchor half of hard draws. A sparse one-in-four hard anchor satisfies
cross-band support while preserving mostly large hard examples.

**Probes.** A test first reproduced the absent hard anchor, then checks every
four-sample window in every band. The profile floor moved from 21/60 pooled with
zero hard hits to passing cross-band support.

**Failure modes / limitations.** A nominal hard batch includes occasional
4-row anchors. Consumers that interpret every hard sample as large should use
observed dimensions rather than the label alone.

## D6. Make every declared override exact, observable, and machine-parseable

**Input choice.** Exact axes are `grid_h`, `left_color`, `right_color`,
`both_zero_count`, and `layout`. `observe_overrides` recovers all five from the
returned grid. Six layout values use distinct permutations of the first three
row-major non-`00` states, so layout is not a cosmetic/unobservable label.

**Original rationale.** The imported generator declared dynamic densities,
separate patterns, a separator color, and a count target that could not be
recovered exactly. It also silently accepted controls tied to the fabricated
separator.

**Alternatives considered.** Keep density/pattern as approximate axes; omit
observability; retain all aliases. Approximate controls were removed from AXES;
only useful non-conflicting legacy aliases are normalized. `sep_color` now
fails loudly.

**Probes.** Boundary tests cover min/max values, exact provenance, unknown and
conflicting overrides, replay freshness, and global-RNG isolation. The full
override checker exposed that its parser recognizes `≠4` but not the phrase
`not 4`; a regression test was added and the metadata changed to the
machine-readable spelling.

**Failure modes / limitations.** Layout is encoded partly through semantic
state order, not purely through visual texture. This is intentional to make the
axis falsifiable, but its name should not be interpreted as a guarantee of a
single geometric motif.

## D7. Retain explicit rejected negative controls

**Input choice.** `no_both_zero`, `all_both_zero`, and `same_occupancy` can be
requested through `texture` for diagnostics. They execute under the oracle but
must fail `self_check`.

**Original rationale.** Negative controls distinguish oracle executability from
teaching-distribution legality and make missing truth-table branches easy to
probe.

**Alternatives considered.** Remove all degenerate modes; declare some lawful.
They remain useful for tests, but none teaches the complete rule, so none is in
the ordinary distribution.

**Probes.** Tests require every negative control to be rejected while
`rule_mirror` still returns an `h x 4` output. Conflicting count/layout controls
with a degenerate texture reject loudly.

**Failure modes / limitations.** These controls are intentionally outside
AXES and therefore are not part of the ordinary Cartesian override contract.

## D8. Synchronize active Racket authority text without deleting history

**Input choice.** `racket_target.target_code` in the selected base solution is
byte-for-byte the canonical `program_solution`. The prior executable
`raw_code` is retained unchanged as archival source.

**Original rationale.** Before review, canonical and selected target code were
semantically equal but exact-text divergent, causing authority synchronization
to fail.

**Alternatives considered.** Rewrite canonical to the legacy `cell-at` form;
delete `raw_code`; ignore the warning. Canonical remains the selected authority,
so only the active duplicate target was synchronized.

**Probes.** Authority-sync and Racket-lint stages are required in the final
battery. The baseline divergence is preserved in before evidence.

**Failure modes / limitations.** Primitive metadata still describes the mined
historical source and may mention `cell-at`; it is provenance metadata, not an
active executable authority.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e4d659481462eded:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `27b24a2de22bc10ad14f247234c6bfdd2b83d94c2e1013f43ae084141cf32f68`. At disposition, audited bytes match the current source.

### Current decision

Bounded source27b24a2de22b audit:15 reported tests,6canonical pairs,160draws/band, occupancy cases and two-example alternating colors; no issue found within this exact source/sample. This closes only this new no-issue report, not any independent finding. Audit target unchanged.

### Assessment or prior finding

## a178821cc6bf

**No issue found** for generator SHA-256 `27b24a2de22bc10ad14f247234c6bfdd2b83d94c2e1013f43ae084141cf32f68` after the bounded checks below.

I inspected all six labeled canonical pairs, the current generator, its named rivals/witnesses, its retained raw-value-equality counterexample, and the two-example alternating same/different-color schedule. Every ordinary input contains all four occupancy states, and every two consecutive examples contain one same-color case, which refutes the strongest canonical shortcut: raw equality instead of “both cells are zero.”

The portable audit task-test stage passed **15/15** (`checks/audit/a178821cc6bf-task-tests/result.json`). Those tests include exact canonical acceptance, 160 default draws per band, multiple consecutive lesson starts, exact overrides, determinism, malformed inputs, and rejected negative controls. I did not find a new concrete counterexample. This is a finite review, not a proof against every possible rival; the audited source was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a178821cc6bf/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 parametric handoff `review-2f669e754965367d`

Built `workspace/parametric/aligned_state_episodes.py` with one episode-fixed
parameter, `marked_state`:

- `both_zero` is the exact canonical Racket program and remains the default.
- `both_nonzero` preserves the same aligned 4+4 panel inputs but marks the
  complementary informative occupancy branch.

The adapter supports 2–6 demonstrations and exactly four private, distinct
queries.  Public projection contains only demonstrations and query inputs;
settings, programs, query answers, and future turns remain private.  The largest
lawful source-shaped stress is 30x8, not 30x30, because both canonical programs
index two fixed four-column panels.  All four occupancy states are dense in that
stress case.

Focused tests replay both settings through Racket, cover every supported demo
count, validate sequential reveal/public IDs, and reject corrupted private
labels.  Native qualification succeeded on seeds 0 and 17 for both settings.
This is a proposed source-bound variant family only; no acceptance or training
admission was requested.

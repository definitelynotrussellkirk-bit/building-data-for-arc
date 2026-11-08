# Working notes: `7d8fc2325e02`

## Current rule and domain

The authoritative rule is unchanged. Rows 0–3 and 5–8 are aligned four-row
panels separated by a uniform nonzero row 4. The 4×W output is color 3 wherever
either aligned panel cell is nonzero, and 0 only when both are zero. Generated
widths are 3–14. Panel and separator roles are positional; their nonzero colors
may be equal.

Version remains `3.0.0`. Final selected generator SHA-256:
`2a50dc1cd6412ff6ff7fc2e227c1e5bce5cf8e8de4fa8cef374abca8218a0ff6`.
Canonical `RULE_HASH=e9653f7b4ad7`; exact Racket authority SHA-256:
`9116d803cf35a1c5a327caffc009bbbc3ac4bb3ff93e9302bdc070039066f90c`.

## Current review reversal

**Prior choice:** all five ordinary Boolean rivals were copied into
`CANONICAL_SHORTCUTS`.

**New choice:** `copy_top`, `copy_bottom`, `and`, `xor`, and
`constant_filled` remain lesson competitors only. The sole declared canonical
shortcut is `canonical_colors_only`, which treats only top color 2 and bottom
color 1 as occupied.

**Reason:** the prior five fit 0/5 labeled canonical pairs and caused the only
baseline battery failure. `canonical_colors_only` fits 5/5 but is refuted by
lawful generated noncanonical palettes. The exact seed-991/index-7 witness is in
`counterexamples/canonical-colors-only-shortcut.json`; Racket and the independent
Python mirror agree, while the shortcut differs at 15 cells.

The production sampler, public controls, output law, lesson ordering, canonical
source, and version were not changed by this repair.

## Parametric authoring proposal

`workspace/parametric/boolean_mode.py` is an isolated proposed family extension:
choose `boolean_mode` once per episode from `{or, xor}`, with `or` as the
canonical default. Both settings retain the same panel roles, separator,
alignment, dimensions, and output color. All generated pairs contain overlap,
so each pair separates OR from XOR.

Retained evidence under `checks/parametric/boolean-mode-v1/` covers two complete
episodes (three demonstrations plus one query), 21 exact Racket evaluations,
5/5 canonical OR replays, 8/8 setting-separating pairs, and independent Python
agreement. OR program SHA-256 is
`9116d803cf35a1c5a327caffc009bbbc3ac4bb3ff93e9302bdc070039066f90c`;
XOR is `711f8508ef539c1a7b98e10e30f65d0071bcadfc8158097511faaf89c26df20b`.
This does not change production approval, labels, or API.

## Final evidence

- Twelve-stage after battery: 12/12 green, no advisory/failure/interruption/pending.
- Portable task-local suite: 74/74 passed.
- Strict semantic census: 600/600 lawful; five witnesses each fired 600/600.
- Profile floor: exact hits 4/20 easy, 6/20 medium, 7/20 hard.
- Exact override matrix: 54,810/54,810 accepted over 609 cases, zero findings;
  unknown keys rejected.
- Large lesson census: 300/300 lessons, three demonstrations plus one query,
  1,200 unique inputs, zero production ambiguity, and 0/1,200 query-rotation
  ambiguities under six unique declared rivals.

## Retained earlier counterexample

`counterexamples/old-copy-panel-shortcut.json` remains the exact v2.0.1 sample
where shared panel masks made copy-panel rivals indistinguishable. The v3.0.0
constructor still requires all four Boolean relations in every input.

## Assumptions and known limits

The finite rival family is not proof of unique induction against every possible
program. The schedule deliberately guarantees the complete Boolean truth table
in each input, which is stronger than the sparse canonical examples but preserves
the same rule. Difficulty changes deterministic ordering rather than restricting
legal width support, so exact public width overrides remain valid in every band.
No unrelated prior return was used as a design lead; the pinned baseline,
canonical pairs, current gates, and task-local retained evidence supplied the
repair evidence.

## Open findings

No selected-task check is currently failing. The only open item is governance:
the OR/XOR extension is proposed and requires separate review before any
production or training use.
## Current reviewer considerations

Source SHA-256: `2a50dc1cd6412ff6ff7fc2e227c1e5bce5cf8e8de4fa8cef374abca8218a0ff6`.

# Decisions — `7d8fc2325e02`

## D1 — Preserve the canonical rule and production sampler

**Prior state:** v3.0.0 already generated 9-row separated-panel inputs with all
four aligned occupancy relations and labeled them with occupancy OR.

**Decision:** do not change the Racket rule, public axes, lesson assembly,
sampling distribution, generator version, or canonical anchors. Keep
`RULE_HASH=e9653f7b4ad7` and the exact canonical program bytes.

**Reason:** the before battery had 11/12 green stages. The sole failure was a
semantic declaration error, while rule smoke, authority synchronization,
profile support, exact overrides, diversity, grammar, and Racket lint passed.
Changing production behavior would have enlarged risk without addressing the
root cause.

**Rejected alternative:** rewrite the OR law or resample inputs. Neither was
supported by the reproduced failure.

## D2 — Repair the meaning of `CANONICAL_SHORTCUTS`

**Prior choice:** `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)`, so five rules
that were already refuted by every canonical pair were presented as
canonical-fitting shortcuts.

**New choice:** retain those five as ordinary lesson competitors, and declare
only `canonical_colors_only` as the canonical shortcut.

**Reason:** the namespace contract is behavioral: a canonical shortcut must fit
all labeled canonical pairs. `canonical_colors_only` fits 5/5 because those
pairs use top color 2 and bottom color 1. The other five fit 0/5. The red/green
regression is retained in `checks/tdd/`.

**Failure mode controlled:** stale bookkeeping can make semantic-gate claims
internally contradictory even when generated labels are correct.

## D3 — Add a generated palette-generalization witness

**Decision:** add a `palette_generalization` witness mapped to
`canonical_colors_only`, and retain the exact seed-991/index-7 counterexample.

**Reason:** merely naming a canonical-fitting heuristic is insufficient. The
selected generator must emit examples that distinguish positional role semantics
from canonical color identity. The retained case uses top 9, bottom 8, separator
4; exact Racket and Python OR outputs agree, while the shortcut differs at 15
cells.

**Rejected alternative:** use a hand-written validator-only grid. A production
generator example is stronger and replayable through the public exact controls.

**Limit:** one minimized case proves disagreement for that rule, not uniqueness
against arbitrary color heuristics.

## D4 — Prototype one episode-level Boolean parameter

**Decision:** implement the isolated proposed parameter
`boolean_mode ∈ {or, xor}`, with `or` as the canonical default. Select it once
per episode and use it for all three demonstrations and the query.

**Reason:** XOR changes the executed transformation while preserving the
original family’s two aligned panels, separator, output color, and cellwise
occupancy comparison. It is a nearby rule, not a cosmetic reskin or unrelated
composition. The existing truth-table grammar guarantees overlap, which is the
specific witness that separates OR from XOR.

**Rejected alternatives:**

- output-color variation: meaningful but mostly a color remapping, weaker than a
  changed Boolean relation;
- width, palette, density, or ordering: these change inputs or sampling, not the
  rule;
- AND as a second setting: possible, but two values are sufficient for a bounded
  prototype and keep the inference contrast simple.

**Boundary:** the code remains under `workspace/parametric/`; no production
parametric API, approval hash, catalog entry, or canonical label was changed.

## D5 — Execute exact Racket for every prototype label

**Decision:** materialize one exact Racket program per setting, unwrap the
canonical `(rule! (lambda ...))` form, apply the lambda through public
`RacketBridge`, and cross-check every result with an independent Python oracle.

**Reason:** the first implementation wrapped the whole stored rule in an
identity `rule!` expression and received a Racket procedure object rather than a
grid. That reproduced failure is in `checks/parametric/prototype-green.log`.
The corrected focused run passes 3/3 and the evidence build records 21 exact
Racket evaluations.

**Limit:** two deterministic episodes and two settings are bounded authoring
evidence, not a general solver or training claim.

## D6 — Keep the lesson policy and test arbitrary held-out positions

**Decision:** retain three demonstrations plus one query in production order,
then run the shared 300-lesson census with required hold-one-pair-out rotations.

**Reason:** the generator already constructs all four truth-table relations in
every input, so each individual pair refutes the named Boolean rivals. The
larger source-bound census verifies the actual exported assembly rather than
inferring lesson quality from isolated witness rates.

**Measured result:** 300/300 production lessons were unambiguous under the six
unique declared rivals; all 1,200 rotations were also unambiguous. This finite
family does not prove universal induction.

## D7 — Update the closed semantic inventory rather than weaken it

**Decision:** update the exact inventory assertion in the existing task test to
include the intentionally added shortcut and witness.

**Reason:** the broader suite initially produced 73 passes and one failure
because the test deliberately treated the semantic registry as a closed schema.
The production change was intended, so the correct action was to update that
contract and keep it exact—not remove or loosen the assertion. The final portable
suite is 74/74.

## D8 — Leave audit targets unchanged

The two drawn audit targets are findings-only. `d57d5daa0895` has a reproduced
public override-contract defect and no retained task tests; `99601629ab88` has a
portable test-path defect while its bounded lint and rule-smoke checks pass.
Neither source was edited, and neither audit is represented as an approval or a
complete semantic review.

## D9 — No new composition annotation claim

This family requires aligned spatial comparison and a Boolean relation, but the
optional four-axis curriculum vocabulary does not cleanly require sequential
state, task-defined symbol learning, contextual gating, or multiple interacting
operations. I therefore did not manufacture a `present` curriculum annotation.

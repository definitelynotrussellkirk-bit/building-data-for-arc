# Working notes: 0994294912bf

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-04 reviewer repair (`review-a9c6435c422ea287`)

- Baseline semantic gate: 8/12 four-demo lessons unidentifiable because the
  ordinary schedule had five profiles and decisive witnesses could fall into
  the query.
- Version 4.1.0 uses `solid | multicolor | br_decoy | clip`, exactly matching
  `EXAMPLES_NEEDED = 4`.
- Adjacent profiles overlap interior, multicolor, pre-filled-target, and clipping
  witnesses so every allowed one-pair query rotation retains each distinction.
- Declared seven executable semantic rivals and four canonical-fitting
  shortcuts; all have generated counterexample witnesses.
- Realigned strict canonical anchors to solid slots and canonical-envelope
  anchors to br-decoy slots after a retained profile-floor regression.
- Added portable focused tests plus `workspace/probe_cyclic_lessons.py` for
  source-hashed exhaustive schedule/rotation checks.
- Final generator SHA-256:
  `bf7c48abf69578ffb0280d00490e28ef0ed2a7e842969bd72a89599c36613005`.
- Final evidence: 12/12 battery stages green, 42/42 staged task tests, 300/300
  production lessons and 1,500/1,500 rotations identifiable, plus 1,440/1,440
  exhaustive task-local rotations.
- Canonical Racket authority was not changed (`ebb564e19380`).

### Limits

Finite rival checks do not prove universal identifiability. Difficulty bands
change presentation ranges rather than measuring solver difficulty. `plain` and
`no_shape` are lawful override-only cases and therefore are not represented in
ordinary production lessons.
## Current reviewer considerations

Source SHA-256: `bf7c48abf69578ffb0280d00490e28ef0ed2a7e842969bd72a89599c36613005`.

# Decisions for 0994294912bf

## D1 — Preserve the canonical Racket authority

**Choice.** Leave the Racket rule unchanged and keep `RULE_HASH = ebb564e19380`.

**Rationale.** Canonical examples, Python mirror checks, Racket smoke, and
selected-authority synchronization all agreed. The defect was not label
semantics; it was the generated lesson schedule failing to teach those semantics.
Changing the oracle would have hidden a curriculum bug.

**Rejected alternative.** Simplify the rule to a per-cell or modal-color
variant. Both fit all canonical demonstrations but disagree with the retained
authority on generated multicolor cases. The exact witness is
`checks/shortcut-counterexample/counterexample.json`.

**Failure mode/limit.** The archival raw-code copy remains divergent, as the
authority-sync report already classifies; selected execution parity is green.
No archival source was edited.

## D2 — Match the ordinary schedule length to the four-demo budget

**Choice.** Replace the five-slot ordinary cycle with
`solid | multicolor | br_decoy | clip`, exactly `EXAMPLES_NEEDED == 4`.

**Rationale.** In the baseline, a four-demo window over five profiles could omit
the only profile that refuted a query-changing shortcut. The semantic gate
reproduced this in 8/12 lessons.

**Rejected alternatives.** Increasing `EXAMPLES_NEEDED` to five would alter the
downstream lesson contract. Keeping `plain` in the ordinary cycle and merely
changing the start offset would only move the bad windows. Random resampling
would make teaching support probabilistic and source-order dependent.

**Failure mode/limit.** A four-slot schedule alone was insufficient for arbitrary
query rotation; the first repair still had 801/1,500 ambiguous rotations. D3
addresses that stronger requirement.

## D3 — Overlap causal witnesses across adjacent profiles

**Choice.** Put each decisive feature in two profiles:

| Feature | Profiles |
|---|---|
| true source interior | `solid`, `multicolor` |
| two source colors / first-scan rule | `multicolor`, `clip` |
| pre-filled BR collision and survivor | `multicolor`, `br_decoy` |
| clipped stamp | `br_decoy`, `clip` |

**Rationale.** A five-pair lesson rotated through each possible query has only
four remaining demonstrations. Duplicate causal coverage guarantees that
holding out one pair does not remove the sole witness for a canonical-fitting
shortcut.

**Rejected alternatives.** Duplicating exact grids would reduce diversity.
Adding more profiles would recreate the budget mismatch. Teaching several
features only in `plain` would make the axis less observable and weaken the
explicit profile contract.

**Probe.** `workspace/probe_cyclic_lessons.py` imports the live schedule and
competitor declarations, hashes the source, checks every configured cyclic
start, and rotates every pair into the query. The final retained run passed
1,440/1,440 rotations.

**Failure mode/limit.** This guarantees coverage only for the declared seven
rivals and the enumerated schedule policy, not every possible abstract rival.

## D4 — Make profile classification observable from grid features

**Choice.** Extend `_analyze` with explicit `source_multicolor`, `clipped`,
`br_prefilled`, and `has_interior` observations, then classify the four ordinary
feature bundles exactly.

**Rationale.** Override checks should recover the requested axis from the grid,
not from hidden generation metadata. Exact feature bundles also make schedule
regressions testable.

**Rejected alternative.** Infer profile solely from generation index. That
would let malformed grids pass axis observation and would not verify that the
promised witness actually exists.

**Failure mode/limit.** Fallback classification remains intentionally permissive
for the explicit `plain` domain; `self_check` still enforces the structural rule.

## D5 — Retain `plain` and `no_shape` as explicit override-only cases

**Choice.** Keep both legal and observable, but do not place them in ordinary
training windows.

**Rationale.** They are useful edge/grammar coverage. `no_shape` verifies the
lawful identity case, and `plain` preserves nonrectangular variation. Neither is
needed as a unique causal teaching profile, so including it in the fixed cycle
spends scarce demonstration budget.

**Rejected alternative.** Remove them from `AXES`. That would unnecessarily
narrow the documented generator domain and break valid explicit callers.

**Failure mode/limit.** Ordinary sampling will not estimate solver behavior on
these override-only cases; override and focused tests cover correctness instead.

## D6 — Realign canonical anchors with the new schedule

**Choice.** Make every fourth `solid` slot a strict 9×9 or 11×11 canonical
anchor. Make every fourth `br_decoy` slot use canonical dimensions and palette
size four by reusing the worked-example color.

**Rationale.** The first shortened cycle inherited an every-tenth anchor cadence
that no longer aligned consistently with strict profiles, producing a 16.7%
canonical-envelope warning. The new cadence provides measured support in every
band without removing broad dimensions from the other slots.

**Rejected alternatives.** Lowering the profile-floor threshold would hide a
real distribution regression. Making every sample canonical-sized would
collapse dimension diversity.

**Failure mode/limit.** The anchor rate is a curriculum policy, not inferred
from a theoretical optimum. Final measured support is 25/60 exact hits.

## D7 — Declare executable rivals and witness ownership

**Choice.** Add `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`,
`CANONICAL_SHORTCUTS`, and `WITNESS_RIVALS` for seven concrete alternatives.

**Rationale.** The baseline hook used unnamed local modes, so the semantic gate
could count failures but often could not identify the surviving competitor.
Declarations let shared tools verify canonical fit, generated counterexamples,
and lesson survival directly.

**Rejected alternative.** Keep only prose descriptions. Prose cannot be replayed
against canonical pairs or saved lessons and drifts from code.

**Failure mode/limit.** The set is intentionally finite. It includes the
strongest local shortcuts found but is not exhaustive.

## D8 — Add portable tests and a source-bound future-agent probe

**Choice.** Add focused tests under the selected generator, make them portable
across source and staged runtime layouts, and add
`workspace/probe_cyclic_lessons.py` plus usage documentation.

**Rationale.** The general battery does not automatically discover selected-task
tests. Future reviewers need one command that checks live declarations rather
than a copied rival list and records the generator SHA.

**Rejected alternative.** Rely only on a one-off notebook/script in `checks/`.
That would not travel with the generator or guard future edits.

**Failure mode/limit.** The probe deliberately avoids Racket calls for speed and
uses the generator's audited mirror; separate battery and census runs establish
Racket parity.

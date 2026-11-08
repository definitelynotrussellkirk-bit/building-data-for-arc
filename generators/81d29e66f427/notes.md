# Working notes: 81d29e66f427

## Review 2026-10-05 — version 3.0.0

Baseline SHA-256 was
`243c44159cf3fa603ce2d5750951659283dbbd4b60231deffefe318418afb852`.
The before battery failed lint, self-check, defect lint, profile floor and exact
overrides; the semantic stage had no contract. The canonical Racket authority
was independently checked against all five labeled pairs and left unchanged.

The repair removes dead/derived advertised axes and exposes four exact controls:
`interior_h`, `interior_w`, `n_keys`, and `gap`. Canonical geometry is sampled in
every band, broad profiles retain controlled variation, default masks realize
00/10/01/11, and three-example windows include key 4 plus a non-4 XOR key.
Executable witnesses and competitors cover OR, AND, XOR, key order and the
canonical-only key-4 shortcut. See `workspace/progress.md`,
`workspace/reference_probe.py`, and `tests/test_generator.py`.

Final generator SHA-256 is
`4b70cb6f8f0d9a669b363c2182d76367ffb951ac16c4a4f2216f3acd7ff9acd4`.
The completed after battery is 12/12 green, task tests are 49/49, exact override
checks accepted 11,520/11,520 draws, and the source-bound lesson census found no
ambiguity in 300 lessons / 1,200 query rotations against the five declared
competitors. These are finite declared-rival checks, not a proof of universal
identifiability.

The two assigned peer audits were findings-only and did not modify their
sources. Their reproducible witnesses are under `checks/audit/`, generated and
verified by `workspace/audit_probe.py`.
## Current reviewer considerations

Source SHA-256: `4b70cb6f8f0d9a669b363c2182d76367ffb951ac16c4a4f2216f3acd7ff9acd4`.

# Decisions — 81d29e66f427

## Evidence policy

**Choice.** Treat the packet baseline and current executions as authoritative;
do not inherit unverified claims from older work. The selected task's
`evidence/associated_notes.jsonl` was empty, so no prior return was used as a
lead. Canonical pairs and Racket authority were inspected only during generator
work, never during either visible-only solve.

**Probe.** `workspace/reference_probe.py` independently parses frame geometry
and computes the OR/AND/XOR gallery without importing generator-owned semantic
helpers. It matched all five labeled canonical pairs.

**Failure mode / limit.** Python parity is supplementary, not label authority.
All final rule claims remain bound to the Racket smoke and authority-sync
receipts.

## D1 — Keep the Racket authority unchanged

**Choice.** Keep `RULE_HASH=dfc8cc699169` and repair only sampling,
validation, controls and lesson construction.

**Rationale.** The independent oracle matched 5/5 canonical outputs; before
`rule_smoke` and `authority_sync` were already green. The observed failures were
caused by the generator and its validator, not the reference program.

**Alternatives rejected.** Loosening the Racket rule to make baseline examples
pass would have changed the task and hidden generator defects. Rewriting the
canonical row was unnecessary.

**Probe.** Final battery stages `rule_smoke`, `racket_lint` and
`authority_sync` pass; authority execution parity is recorded in
`checks/after/checks/81d29e66f427_after_authority_sync.json`.

## D2 — Separate legality from teaching quality

**Choice.** `self_check` validates only lawful structure and colors. It accepts
canonical masks even when AND is empty or OR equals XOR. Teaching-quality
requirements—coverage of all truth states, semantic branches and rivals—are
implemented in the default sampler and semantic hooks instead.

**Original rationale.** Baseline code required OR, AND and XOR outputs to be
nonempty and distinct. That rejected a canonical input, proving the condition
was not part of the task law.

**Alternative rejected.** Keeping the strict relationship check only for
generated examples inside `self_check` would make legality depend on provenance
or metadata and would continue to reject valid external/canonical grids.

**Failure mode / limit.** A manually supplied lawful override or external grid
can still be a weak teaching example. The production schedule, not
`self_check`, carries the lesson-quality guarantee.

## D3 — Advertise only exact, pixel-observable axes

**Choice.** Replace nine baseline axes with four controls that are both causal
and recoverable from the returned grid:

| Axis | Domain | Observable as |
|---|---:|---|
| `interior_h` | 3..6 | frame interior height |
| `interior_w` | 3..6 | frame interior width |
| `n_keys` | 1..5 | number of nonzero row-0 keys |
| `gap` | 1..4 | blank columns between frames |

All values are legal in every difficulty band; unknown names, booleans,
non-integers and out-of-range values are rejected. `observe_overrides` performs
pixel-based recovery.

**Original rationale.** `grid_h` and `grid_w` were derived, while palette,
density and texture were ignored/dead aliases. Per-band bounds contradicted the
global AXES contract. The before override stage produced 88,530+ findings.

**Alternatives rejected.** Making derived height/width jointly solvable would
add incompatible-combination machinery without creating useful independent
variation. Keeping decorative aliases would make typoed or dead controls appear
supported.

**Probe.** The final contract exercised 128 override cases over 11,520 draws;
all were accepted and observed exactly, with zero findings. Unknown-key
rejection passed.

**Failure mode / limit.** There are no advertised controls for mask density,
key identities or palette. Those still vary deterministically as latent sampler
choices, but callers cannot request them exactly.

## D4 — Anchor canonical geometry in every band

**Choice.** Two of the three schedule positions use canonical geometry:
interior height 5, interior width 4/5/6, three keys, frame gap 1, row 0 keys,
row 1 blank, frames starting at row 2, left frame flush left, bottom-flush
frames and two trailing blank columns.

**Original rationale.** The baseline had arbitrary margins and easy produced no
exact canonical profile in the 20-draw floor check.

**Alternative rejected.** Sampling canonical geometry only in easy or only at a
small global probability could leave an entire band unsupported. Making every
sample canonical would eliminate useful size/gap/key-count variation.

**Probe.** Final profile floor accepted 5/5 canonical inputs and observed 46/60
exact-profile draws: easy 17/20, medium 16/20 and hard 13/20.

**Failure mode / limit.** This intentionally weights canonical-scale geometry
heavily (roughly two schedule positions of three). It is not meant to reproduce
the empirical frequency of any external ARC distribution; it is a teaching
mixture.

## D5 — Retain a broad profile with band-specific defaults

**Choice.** The `broad` schedule position varies dimensions, key count and gap.
Easy favors smaller 3–4 interiors and gap 1–2; hard favors 4–6 interiors,
4–5 keys and gap 2–4; medium spans the full default set. Exact overrides always
use the full global domain regardless of band.

**Rationale.** Difficulty should affect defaults without making an advertised
control illegal. Broad examples reduce overfitting to one frame width, one gap
or exactly three output panels.

**Alternatives rejected.** Uniform full-range defaults in easy/hard would erase
useful difficulty shaping. Narrow per-band override ranges recreated the
baseline contract defect.

**Failure mode / limit.** Difficulty labels here are geometric, not measured
model difficulty. No claim is made that the hard distribution is monotonically
harder for every solver.

## D6 — Make default masks realize all four Boolean truth states

**Choice.** Every default mask pair contains at least one `00`, `10`, `01` and
`11` cell. Remaining cells receive randomized states.

**Rationale.** OR, AND and XOR can be inferred only when private A cells,
private B cells, overlap and background are all visible. This is a sampling
requirement, not a validity requirement.

**Alternatives rejected.** Rejection-sampling arbitrary masks worked in the
baseline but coupled success to density and could silently fall back; requiring
nonempty/distinct outputs in `self_check` rejected canonical data. The direct
truth-state construction is deterministic and guarantees the needed witness.

**Failure mode / limit.** Small interiors are bounded at 3×3, so four states fit.
The distribution is not calibrated to canonical mask-density frequencies.

## D7 — Use key values that expose the full branch law

**Choice.** Default semantic keys include 2 (OR), 3 (AND), and an XOR key. The
canonical profile uses 4; the generalized profiles use 6, 7 or 9. Key 5 is
excluded because it is the frame color, and key 8 is excluded because it is the
output color. Additional keys are distinct XOR keys.

**Rationale.** The Racket branch is “2, 3, otherwise,” not “2, 3, 4.” All five
canonical pairs use key 4 for XOR, so a key-4-only shortcut fits them.
Non-4 keys are the decisive counterexample.

**Alternative rejected.** Always using only 2/3/4 preserves canonical
appearance but never teaches the general else branch. Using 5 or 8 as operation
keys creates avoidable perceptual role collisions.

**Failure mode / limit.** Other legal ARC colors are not exhaustively sampled.
The selected set is enough to demonstrate more than one value in the else
branch.

## D8 — Randomize key order while forcing a fixed-order counterexample

**Choice.** Key values are placed left-to-right in their requested panel order,
but the semantic operation sequence is shuffled. A three-key draw that would
accidentally equal OR/AND/XOR order is swapped; four-plus-key examples already
disagree by the fourth panel.

**Rationale.** Without this constraint, a learner can ignore key values and
emit OR, AND and XOR in a fixed gallery order.

**Alternative rejected.** A fixed canonical `[2,3,4]` order is visually simple
but teaches the shortcut directly. Random order without a guard gives a
nonzero chance of weak examples.

**Probe.** `key_order` fired on 600/600 semantic-gate draws, and the declared
`fixed_order` rival disagreed on every checked witness.

## D9 — Three-position, three-demonstration schedule

**Choice.** `schedule_profile(sample_index) = profiles[sample_index % 3]` with
profiles `canonical_key4`, `canonical_other_xor`, `broad`.
`EXAMPLES_NEEDED=3`; production lessons use three demonstrations and one query.
Every consecutive triple contains one of each profile, independent of starting
residue.

**Rationale.** Three examples are the cheapest deterministic window that can
carry canonical grounding, a generalized XOR witness and broad variation while
repeating OR/AND semantics. The modulo schedule makes all cyclic starts
inspectable.

**Alternatives rejected.** Two demonstrations can omit a branch or the
canonical-only shortcut witness. Four or more increase SFT token cost without
being needed for the declared rivals. Random profile selection has a real
chance of weak windows and makes replay harder.

**Ordering/query policy.** The intended exporter may use any one of the four
materialized pairs as query. The semantic smoke checked 48 rotations and the
larger census checked all 1,200 rotations; no declared rival remained ambiguous.

**Failure mode / limit.** This proves only the tested deterministic schedule and
declared competitors. It does not enumerate arbitrary resampling policies or
all possible rules consistent with the pixels.

## D10 — Declare executable witnesses, competitors and canonical shortcut

**Choice.** Add five witnesses and five pure competitor functions:
`all_or`, `all_and`, `all_xor`, `fixed_order`, and `key4_only_xor`. Declare
`key4_only_xor` in `CANONICAL_SHORTCUTS` and all five in
`LESSON_COMPETITORS`; implement `lesson_identifiable` against actual labeled
demos/query.

**Rationale.** Per-grid correctness does not establish that a three-example
lesson teaches the intended mapping. The canonical-only shortcut is concrete:
it fits all five canonical pairs yet differs on any non-4 XOR query.

**Alternative rejected.** Describing rivals only in prose leaves no automated
contract. Declaring only all-OR/AND/XOR misses the key-order and branch-domain
shortcuts that were most relevant here.

**Probe.** Semantic gate: 5/5 witnesses fired in every band, every witness/rival
claim held, 12/12 lessons identifiable and 0/48 rotations ambiguous. Census:
300 lessons, 1,200 unique inputs, zero production or rotation ambiguity.

**Failure mode / limit.** The rival set is finite and author-supplied. An
undeclared shortcut can still survive. `QUESTION_ANSWER.md` proposes the shared
gate that would reduce this dependence on manual declarations.

## D11 — Preserve exact low-key overrides but exclude them from defaults

**Choice.** `n_keys=1` and `n_keys=2` remain legal exact controls; default
profiles use at least three keys.

**Rationale.** The task law supports one or two panels, and an exact override
should be truthful. But a default training example with fewer than three keys
need not show OR, AND and XOR simultaneously.

**Alternative rejected.** Removing 1–2 from the legal domain would narrow the
rule unnecessarily. Sampling them by default would weaken lesson guarantees.

**Failure mode / limit.** A caller who manually assembles lessons entirely from
low-key overrides must run its own lesson-identifiability check.

## D12 — Tests and reusable tooling

**Choice.** Add 49 task-local tests plus two workspace tools. Tests cover
canonical acceptance/oracle parity, exact overrides in every band, invalid
controls, profile support, truth-state coverage, schedule windows, declared
witnesses/rivals, destructive mutations and deterministic replay.
`reference_probe.py` is an independent task oracle; `audit_probe.py` recreates
and verifies both assigned peer-audit findings using public Racket receipts.

**Rationale.** The shared battery does not automatically discover selected-task
tests, and future reviewers need portable probes rather than narrative-only
claims.

**Probe.** TDD red was 36 failed / 13 passed; first green and staged portable
runs are 49/49.

## D13 — Solve records and post-solve changes

**Choice.** Finish the blind solve before task inspection, then prepare the
post-repair solve from exact final generator bytes. After solve freeze, only
reports, notes, summary and workspace audit tooling were added; the generator
was not changed.

**Rationale.** Solve evidence must remain bound to the generator hash used to
prepare it.

**Probe.** `solve/summary.json` records generator hash
`4b70cb6f...f9acd4`, identical to the final generator file. Earlier exposure is
honestly `yes`; reference consulted during solve is `false`.

## D14 — Audit targets remain untouched

**Choice.** Report findings for `15dd333aa99b` and `d17f2bbc0878` without
patching either target.

**Rationale.** Assignment step 7 requests adversarial reviews, not repairs.
Both findings are bound to target source hashes and public `arcpuzzles apply`
receipts in `checks/audit/`.

**Limit.** The 300-draw audit probes are finite. The reported source-level root
causes make the witnesses reproducible, but prevalence outside those exact
seed/index ranges is not claimed.

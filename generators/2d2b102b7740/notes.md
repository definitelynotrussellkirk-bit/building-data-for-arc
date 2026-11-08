# 2d2b102b7740 — current design

## Review update — `review-68eac576afcc440f`

Current generator SHA-256: `47d83413e7bc5176995118cec0d5c98a2ad973651513346ebc74a66d54ec848c`. This review leaves version `2.0.0`, canonical Racket authority, generation distribution, exact controls, and six-profile lesson schedule unchanged. The only selected canonical-source change is strict validation of `seed` and `sample_index`: booleans, floats, strings, and negative values now fail before `GenCtx` instead of entering deterministic generation. Valid calls retain their prior outputs.

A separate proposed prototype under `workspace/parametric/` introduces episode-level `extension_mode in {forward,both}`. `forward` is the canonical default; `both` also extends before the first blue cell. The builder materializes exact Racket per setting, executes every label, checks Python parity and rival disagreement, redacts public queries, and retains two complete source-hashed episodes. It does not change or approve the selected canonical rule.

Current evidence: 73/73 portable task tests; fixed-seed schedule coverage 18/18 lessons and 108/108 rotations; broader census 300/300 lessons and 1,800/1,800 rotations with zero declared-rival ambiguity. The main strict battery is 10/12 because the generic defect linter still flags a lawful short horizontal line and the battery did not attach the required period-six schedule receipt. The same-source supplemental semantic gate passes with that receipt, leaving only the known shared-linter false positive.

The retained predecessor sections below remain design history. Their earlier source hash and test-count statements are superseded by this update; their rule/domain rationale is unchanged.

## Authority and domain

Version `2.0.0`; generator SHA-256
`47d83413e7bc5176995118cec0d5c98a2ad973651513346ebc74a66d54ec848c`.
The canonical Racket rule remains `8db0d36e6e45`. It preserves blue cells and
extends the row-major displacement from the first two, starting beyond the last.
Its 20-step bound reaches the boundary throughout this sampler's dimensions.
The selected base JSON's `racket_target.target_code` now matches canonical source
text exactly; canonical examples, canonical ledger, and archival `raw_code` are
unchanged. Python rivals are diagnostics, never label authority.

Inputs are rectangular integer grids: height 6–18, width 8–20, colors 0/1,
2–5 equally spaced blue cells, `dr` 0–4 and `dc` −4–4. Row-major direction requires
`dr > 0` or `dr == 0 and dc > 0`; at least one red continuation must fit.
Horizontal, vertical, both diagonal signs, knight, steep, and other oblique
directions are lawful. All three canonical 15×15 inputs remain in support.
Difficulty changes size weights, not valid override bounds.

## Exact controls

Geometry is sampled from feasible tuples before placement. Supplied counts,
dimensions, displacements and orientation are realized exactly. Invalid keys,
types and values raise `ValueError`; contradictory valid pins raise
`IncompatibleOverrides` with `incompatible_axes`. No step substitution, dropped
point, implicit zero-step repair, or dimension clipping remains.

`anchor_corner=True` places the first row-major blue at the directional top
corner; `False` excludes that exact point. A true corner pin combined with an
explicit `position_bias` is rejected because the latter cannot move that anchor.
`position_bias` otherwise chooses among feasible starts. `texture` orientation
names agree with `line_orientation`; `two_blues_only` requires count 2 and
`line_at_edge` requires a horizontal top-row line. Conflicting aliases are
rejected. Degenerate singleton/blank/block/identity inputs are mutation fixtures,
not production textures.

## Default lessons: five demonstrations, period six

For each seed, shuffle the non-three counts into `(X,Y,Z)` from `{2,4,5}`.
The six profiles are:

| Index modulo 6 | Geometry | Count |
|---|---|---:|
| 0 | Negative column displacement; witness-rich placement | X |
| 1 | Negative column displacement; witness-rich placement | 3 |
| 2 | Positive column displacement; witness-rich placement | X |
| 3 | Canonical 15×15 positive main diagonal, step 2–4 | 3 |
| 4 | Free feasible direction and placement | Y |
| 5 | Free feasible direction and placement | Z |

Profiles 0–2 reserve one backward step and at least two red continuation cells,
with nonunit lattice spacing. The two opposite-sign pairs, at counts X and 3,
ensure that holding out any one pair leaves at least one complete sign pair.
Count plus sign distinguishes the six inputs, so within-lesson duplicate
rejection cannot skip one of these profiles.

The finite contract declares 14 named rivals: equal row/column step,
absolute column step, extension in both directions, a fixed three-blue prefix,
unit lattice step, one red cell only, and all eight count-to-sign lookups that
assume a positive direction for count 3. `count_sign_000` duplicates the absolute
column-step prediction, so these are not 14 independent hypotheses. Twelve
declared names fit all three canonical pairs;
the last two basic errors already contradict canonical examples. Every five
of the six default pairs refute the declared rivals. Explicit non-null
overrides disable the schedule and carry no universal lesson guarantee.

## Evidence and remaining decision

The current review retains 73 passing task tests; a Racket census of 300 lessons
and 1,800 query rotations (1,037 unique inputs); and all six cyclic starts at
seed 0 across three bands, 18 lessons / 108 rotations. These are finite checks
against declared rivals, not proof against every possible shortcut. Independent
geometry checks add 1,800 exact-control cases and 2,880 holdouts.

The main after battery is 10/12 green: shared defect lint still calls a lawful
four-blue horizontal line a `short_line` impostor, and the main semantic invocation
did not attach the declared period-six schedule receipt. The source-bound
supplemental semantic gate passes with that complete receipt. The reusable probe in
`workspace/probe_minimal_grammar.py` retains validator and actual Racket results;
it does not change lint or approval. A solid 2×2 block is a useful contrast:
Racket executes it, but the line grammar correctly rejects it. The maintainer
must adjudicate the shared lint finding; the domain was not narrowed to hide it.

`counterexamples/shortcut-witness.json` records the exact default negative-slope
input at seed 0, index 1, medium, its Racket output, and every declared canonical
shortcut's predictions. The return's `REVIEW.md`, `DECISIONS.md`, `RESULTS.json`
and `checks/` retain commands, before/intermediate failures, source identities,
the two assigned audits, and the two honest solve episodes.
## Current reviewer considerations

Source SHA-256: `47d83413e7bc5176995118cec0d5c98a2ad973651513346ebc74a66d54ec848c`.

# Decisions for 2d2b102b7740 — review-68eac576afcc440f

## D1 — Reject malformed call scalars at the generator boundary

**Original choice:** `generate` validated `difficulty` and explicit axes, but passed `seed` and `sample_index` directly to `GenCtx`. That accepted Python booleans, several floats and strings, and negative sample indices.

**Decision:** require `type(seed) is int` and `seed >= 0`; require `type(sample_index) is int` and `sample_index >= 0`; keep the existing difficulty domain. Validate before any draw.

**Reason:** these are public call arguments, not semantic grid variation. Accepting malformed values creates unstable provenance and aliases (`True == 1`) while contradicting the strict generator contract. The baseline defect linter reproduced 24 findings across difficulty bands.

**Alternatives rejected:** coercing values with `int(...)` would silently merge distinct calls; validating inside `GenCtx` would be a shared-interface change outside this task; changing generated geometry would not address the bad inputs.

**Probe and result:** focused tests were written first. Nine of twelve cases were accepted before the patch; all twelve are rejected afterward. The complete portable suite passes 73/73 and after-phase defect lint reports zero `strict-scalar` findings.

**Failure mode/limit:** the task continues to depend on the shared `GenCtx` contract for deeper seed handling. This review tests the values used by the shared detector; it does not enumerate arbitrary Python integer magnitudes.

## D2 — Preserve version `2.0.0` and valid-call determinism

**Decision:** do not bump the generator version.

**Reason:** version participates in deterministic draws. Changing it would alter every valid generated example even though the repair only rejects previously invalid public calls. Keeping the version preserves all lawful outputs and source-bound lesson evidence while tightening the boundary.

**Alternative rejected:** a version bump would provide a visible revision marker but unnecessarily invalidate the established distribution and schedule.

**Probe and result:** existing determinism, exact-control, distribution, canonical-support, rule-parity, and lesson tests remain green; only malformed calls change behavior.

## D3 — Do not narrow the lawful arithmetic-line grammar to silence generic lint

**Observed warning:** the generic `selfcheck-minimal-impostor` detector calls a short horizontal line an impostor because the task accepts all six probes of that named shape.

**Decision:** retain the input as lawful and report the warning.

**Reason:** a horizontal line of equally spaced blue cells is an ordinary member of the canonical arithmetic-progression rule. The selected validator, exact Racket execution, and task-local probe agree. Rejecting it would optimize for a detector name rather than the task semantics.

**Alternatives rejected:** adding a fake minimum slope/height or special-case rejection would make the generator narrower and would leave the authority capable of executing inputs the validator denies.

**Evidence:** `tests/test_minimal_grammar_probe.py`, `workspace/probe_minimal_grammar.py`, and the before/after defect-lint logs. A solid 2×2 block remains a genuine rejected contrast.

**Limit:** maintainer adjudication is required because the current shared detector has no task-local lawful-shape exemption.

## D4 — Keep the parametric rule separate from canonical production

**Decision:** add an isolated `workspace/parametric/` prototype with one episode-level enum parameter, `extension_mode={forward,both}`. Do not alter `generate`, `RULE_HASH`, canonical data, catalog metadata, or selected Racket authority.

**Reason:** extending before the first blue is a small, meaningful variation of the same object roles and arithmetic-line reasoning. It is easier to infer and test than unrelated color/direction parameters, and the original setting remains exactly canonical.

**Alternative approaches rejected:** varying colors changes surface presentation rather than rule semantics; varying step or point count is already input distribution, not a hidden rule; adding several independent rule parameters would make demonstration identifiability harder to diagnose.

## D5 — Choose one setting once per episode and make it demonstrably identifiable

**Decision:** choose `extension_mode` from the deterministic episode seed, then use it for all three demonstrations and the query. Every retained input has at least one in-bounds continuation position on each end. Reject an episode unless all demonstrations distinguish the competing setting.

**Reason:** per-pair resampling would leak an incoherent target. Inputs without backward room make `forward` and `both` observationally identical and are poor training evidence.

**Evidence:** the builder executes materialized Racket for every label, checks Python mirror parity, default hash equality, rival outputs, three demonstrations, one query, and public redaction. `summary.json` passes for one `forward` and one `both` episode.

**Limit:** the evidence uses a finite six-scene bank and one declared parameter rival. It is prototype evidence, not universal identifiability or training admission.

## D6 — Require a source-bound schedule receipt rather than weakening the semantic contract

**Observed result:** the main after battery's semantic stage reports all sampled witnesses/lessons passing but exits nonzero because it did not enumerate the declared period-six schedule.

**Decision:** run the prescribed fixed-seed schedule census across all three bands and re-run the strict semantic gate with that receipt.

**Reason:** the six-step teaching schedule is central to rejecting sign/count shortcuts. Removing `LESSON_SCHEDULE_PERIOD` or downgrading the requirement would discard valuable contract information.

**Result:** 18/18 lessons and 108/108 rotations materialize with zero ambiguity/errors/warnings; the source-bound supplemental semantic gate passes. The broader 300-lesson census also has zero declared-rival ambiguity across 1,800 rotations.

## D7 — Compress only the oversized full census, with reversible provenance

**Decision:** gzip the 26.25 MiB full `lesson-census-100.json`, retain its summary plus original/compressed sizes and SHA-256 hashes, and record an exact restoration command.

**Reason:** the return guide caps expanded evidence while asking reviewers to preserve exact instances. Lossless compression retains the full record without dropping failed or successful lesson rows.

**Limit:** consumers must restore it with the documented `gzip -dc` command before treating it as plain JSON.

# Working notes: ef02aedbac38

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `8e58467c2dfcde47f0d091d69ddd0046f7c6a0093a00cbbd94e5eee5faedb1e8`.

# Decisions for `ef02aedbac38`

## D1 — Repair only the malformed-call boundary

**Prior behavior.** `_validate_call` checked difficulty and overrides but did not
validate `seed` or `sample_index`; it also accepted every numeric difficulty in
`0..1`. Consequently `True` aliased integer seed/index values, negative indices
entered the deterministic curriculum schedule, and numeric difficulty values
were silently treated as medium downstream.

**Choice.** Require `type(seed) is int`, require a non-negative
`type(sample_index) is int`, and allow difficulty only as `None`, `"easy"`,
`"medium"`, or `"hard"`. Run this validation before `gen_ctx`.

**Alternatives rejected.** `isinstance(x, int)` still accepts booleans. Coercion
would make malformed calls replay ambiguously. Preserving numeric difficulty
would contradict the strict public contract reported by defect lint.

**Failure modes and probe.** Nineteen focused invalid-scalar tests cover bool,
negative, float, string, `None`, and invalid enum values. The original RED run is
under `checks/tdd-red/`; final task tests are under `checks/task-tests-wrapper-green/`.
The minimal case list is
`generators/ef02aedbac38/counterexamples/invalid-call-contract.json`.

## D2 — Preserve every valid draw and retain version 4.1.0

**Choice.** Keep `VERSION = "4.1.0"`, all RNG namespaces, curriculum residues,
axes, grammar, and output construction unchanged. A pre-repair fixture replays
five representative valid calls byte-for-byte after the patch, including an
explicit 3×25 boundary override and a negative integer seed.

**Rationale.** The defect is input validation, not generated content. Bumping the
version or changing RNG flow would invalidate the strongest non-regression claim
without improving the contract.

**Evidence.** `counterexamples/valid-call-replay.json` is bound to baseline SHA
`ec1715f0...`; final task tests pass it against final SHA `8e58467c...`.

## D3 — Do not change the Racket authority

**Choice.** Preserve `RULE_HASH = "0e568f927b22"`, canonical program text,
canonical labels, and active authority. The final battery's rule smoke,
Racket lint, and authority synchronization stages are green.

**Rationale.** The prior peer finding concerned Python call semantics only. No
label mismatch or rule defect was reproduced.

## D4 — Keep the parametric extension isolated and episode-level

**Choice.** Build a proposed task-local prototype with exactly one parameter,
`selector_role ∈ {five, companion}`. The canonical/default setting selects cells
whose value is 5 and paints them with the companion color. The alternate setting
selects companion-color cells, paints them 5, and writes 0 elsewhere. The setting
is selected once from the episode seed and is not exposed in public material.

**Why this parameter.** It changes one genuine rule decision—the selected color
role—while retaining the family invariants: infer the two input roles, use one as
a mask, paint with the opposite role, zero unselected cells, and preserve shape.
It also yields direct, lawful disagreement on every retained demonstration and
query.

**Alternatives rejected.** Varying only output color would weaken the two-role
relationship; varying grid transforms would create a different spatial family;
varying background color would conflict with canonical zero-background labels.
Adding multiple parameters would make a two-episode proof underdetermined.

**Status and limits.** This is proposed evidence, not a production API or
approval. Exact artifacts are under `workspace/parametric/` and
`checks/parametric/selector-role-v1/`.

## D5 — Execute both prototype settings with complete Racket programs

**Choice.** Store complete Racket programs for both settings, require exact text
equality between the default program and canonical `program_solution`, execute
all retained labels through `RacketBridge`, and independently compare them with a
small Python mirror.

**Revision.** The first evidence run exposed a double-lambda wrapper bug: direct
execution returned a procedure instead of a grid. I added a regression that
executes the complete default program, then changed `_callable_text` to use the
already-callable result of `strip_rule_wrapper` directly. The failed and passing
receipts are retained under `checks/tdd-wrapper-red/` and
`checks/task-tests-wrapper-green/`.

## D6 — Preserve the ordered production curriculum; report rotation ambiguity

**Measured result.** The source-bound 300-lesson census (100 per band, four
ordered demonstrations plus one query) found zero ambiguous production lessons.
Holding out every one of the five positions as an artificial query found 225
ambiguous rotations out of 1,500; each band contributed 75. The surviving rival
is `sparse_or_canonical_lookup` when the held-out item removes the needed density
counterexample.

**Choice.** Do not restructure the generator for arbitrary query permutation in
this repair. The actual assembly is ordered and passed 300/300; the packet does
not claim that queries may be freely rotated. Retain the rotation failure as a
known limitation rather than relabeling it as a pass.

**Alternative rejected.** Adding examples or changing the six-index schedule
would exceed the call-contract scope and could perturb a previously verified
curriculum. A future requirement for arbitrary rotation should be handled as a
separate curriculum design change with `--require-rotations-identifiable`.

## D7 — Treat proposed-rule evidence and canonical repair separately

The call-contract repair is complete and routine. The selector-role prototype is
runnable and evidence-backed but remains explicitly proposed. Acceptance of the
repair must not be interpreted as approval of the alternate rule, and the
rotation limitation applies to the current production lesson schedule rather
than to the two retained prototype episodes.

## D8 — Bind public IDs to the exact visible bytes

**Defect.** Prototype v1.0.0 hashed only the train/test input grids while writing
pretty-printed public JSON. Two public challenges with the same inputs but
materially different visible demonstration outputs therefore shared a filename,
and the filename digest was not the digest of the bytes on disk.

**Choice.** Prototype v1.1.0 projects the public challenge first, serializes it
with `reviewer_support.public_challenge_bytes`, names it with
`public_challenge_id`, and writes those exact bytes. Demonstration outputs and
all visible inputs now affect the ID; hidden setting metadata, seeds, rule text,
and query answers do not. The writer rejects a duplicate public path rather than
overwriting it.

**Evidence.** The RED collision and exact-byte failures are retained under
`checks/tdd-red-public-evidence/`; the focused GREEN run is under
`checks/tdd-green-public-evidence/`.

## D9 — Expose episode counts and retain four distinct queries

**Choice.** Keep one episode-fixed `selector_role`, but expose `demo_count` and
`query_count` through both `write_evidence` and the CLI. The default evidence
shape is three demonstrations plus four queries. Counts are validated before
creating the destination, exactly one seed must select each declared setting,
and every retained episode must have distinct demonstration/query inputs.

**Rationale.** This adds supervision rather than a second hidden semantic axis.
Four independently labelled queries exercise the same inferred rule on varied
inputs while the three demonstrations already distinguish the only declared
rival. Production generation, canonical program text, `RULE_HASH=0e568f927b22`,
and generator version 4.1.0 remain unchanged.

**Limits.** Counts remain bounded to 1..8 demonstrations and 1..4 queries, with
at most 12 total pairs. The finite declared-rival check does not exclude arbitrary
alternative programs, and the prototype remains proposed rather than approved.

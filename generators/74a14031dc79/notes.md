# Working notes: 74a14031dc79

## Current rule and domain

The input is an `h×7` grid with a three-column left panel, a solid one-column
separator, and a three-column right panel. For each aligned panel position,
the output is blue (`2`) when either input cell is nonzero and black (`0`) only
when both are zero. The selected canonical Racket source is unchanged and is
pinned by `RULE_HASH = "582367af483f"`.

Lawful inputs use one distinct nonzero, non-blue color for each panel and the
separator; height is `3..12`. Canonical inputs are lawful even when they do not
show all four Boolean occupancy relations. Generated teaching examples are
stronger: every one contains `00`, left-only `10`, right-only `01`, and overlap
`11`, so left-copy, right-copy, XOR, AND, constant-fill, and input-blue shortcuts
are refuted within an individual example.

## Repaired distribution (version 3.0.0)

The imported 1.2.0 generator used one foreground color for both panels,
advertised density/pattern/target controls that were not recoverable, admitted
weak impostors through `self_check`, and never reached the canonical four-color
profile. Those choices were replaced rather than preserved:

- exact observable axes: `grid_h`, `left_color`, `right_color`, `sep_color`, and
  `relation_profile`;
- distinct panel/separator colors selected from `{1,3,4,5,6,7,8,9}`;
- five exact truth-table count profiles, each retaining all four relations;
- a four-slot schedule: slots 0 and 1 retain canonical height 3, slot 0 also
  anchors role colors `(6,8,4)`, and slots 2 and 3 use difficulty-banded heights;
- structural validation separated from the stronger generated-lesson profile;
- executable rivals, witnesses, canonical shortcuts, and a lesson-identifiability
  hook;
- unknown or incompatible exact overrides fail loudly.

Two height-3 slots are deliberate. A one-slot anchor produced only 10/60 hits in
the official pinned profile-floor census; the two-slot schedule produces 30/60
(11 easy, 8 medium, 11 hard) while every sliding three-example lesson still
contains off-canonical shape and palette evidence.

## Authority synchronization

`shared/data/base/solutions/training/e133d23d__74a14031dc79.json` had an
executable `target_code` using the legacy alias `cell-at`, while the canonical
selected source uses `at`. The task-specific `target_code` is now byte-for-byte
the canonical program. Archived `raw_code` remains unchanged. This is source
synchronization only; the canonical authority and behavior did not change.

## Evidence and limits

- Final generator SHA-256: `67d37e167fe4f56dc5b0c120a5a0466229ba98ffbae486432ac1a3d961c42c9d`.
- Final battery: 12/12 green at `checks/after-final/`.
- Portable task tests: 58/58 green at `checks/task-tests/`.
- Source-bound lesson census: 300/300 production lessons and 1200/1200 query
  rotations unambiguous against declared rivals, 1197 unique inputs, at
  `checks/lesson-census.json`.
- Strongest retained canonical shortcut and Racket-checked counterexample:
  `counterexamples/canonical-shape-palette-shortcut/`.

The finite rival set is not a proof of unique induction against every possible
program. The generator intentionally keeps the fixed 3+separator+3 geometry and
fixed output color 2 because those are task semantics, not nuisance features.
No unresolved selected-task blocker remains in this review.
## Current reviewer considerations

Source SHA-256: `11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3`.

# Decisions for review `review-92eccef38953659a`

## D1 — Preserve the selected distribution and canonical rule

The imported selected generator was already a mature `3.0.0` repair with exact
axes, full occupancy-truth-table teaching support, declared rivals, profile-floor
coverage, and retained shortcut evidence. The current review index points to
`review-c231a5768f77dff2:v0001`; I used that prior return only as a lead, then
remeasured the current source with the assigned battery and a new 300-lesson
census.

The before run found no distribution or rule defect before `defect_lint`; it
found a call-contract defect. I therefore did not rewrite sampling, palette,
shape, semantic rivals, or Racket authority. A broader rewrite would risk
regressing already-measured teaching support without addressing the reproduced
failure.

## D2 — Reject invalid call scalars at the generator boundary

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and
`sample_index >= 0` before creating the generation context.

**Rationale.** Python accepts booleans as integers and downstream scheduling can
coerce floats/strings or let negative indices alias cycle positions. The before
`defect_lint` reproduced 33 warnings across bands. Rejecting at the public call
boundary makes invalidity explicit and keeps schedule semantics one-to-one.

**Alternatives rejected.** Coercing with `int(...)` would keep silent aliases;
validating only inside `schedule_profile` would leave other generation paths
exposed; broad seed range restrictions were not justified by the detector.

**Compatibility decision.** Keep `VERSION = 3.0.0`. Since valid outputs and RNG
choices are unchanged, a version bump would remap every lawful draw for no
semantic benefit. Final source hash is
`11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3`.

## D3 — Put new regression coverage in a separate reviewer test

The packet marks `tests/test_generator_74a14031dc79.py` as a frozen fixture. The
strict-scalar regression therefore lives in `tests/test_review_regressions.py`.
It checks Boolean, float, string, and negative cases with the selected module
loaded through portable `reviewer_support` paths. The inherited fixture was
restored byte-for-byte after the initial exploratory placement.

## D4 — Choose one meaningful parameter: the occupancy predicate

The family naturally supports one small rule parameter without changing object
roles: `occupancy_rule ∈ {or, xor, and}`. Each setting compares the same aligned
left/right panel cells, uses the same separator geometry, outputs the same
three-column shape, and paints with the same color 2. This preserves the original
reasoning structure better than changing panel width, colors, density, or height,
which would alter inputs but not the executed transformation.

The canonical/default `or` source is byte-identical to the pinned authority.
`xor` and `and` are generated by replacing one exact guarded condition in that
source; source guards reject whitespace or unrelated mutations. A target-color
parameter was rejected because color 2 is a visible task semantic and changing
it would create a mostly cosmetic variant. A direction parameter was rejected
because the task has no directional transformation.

## D5 — Select the hidden setting once per episode

`random.Random(seed).choice(("or", "xor", "and"))` chooses one rule for the
whole episode. All three demonstrations and the query use that exact Racket
source. Resampling per pair would turn the lesson into inconsistent supervision
and violate the packet's parametric contract.

Seeds 1, 0, and 5 were retained because together they exercise all settings.
This is bounded evidence, not a claim about seed frequencies.

## D6 — Require complete occupancy support in every prototype input

Every prototype input comes from the selected generator and contains all four
relations `00`, `10`, `01`, and `11`. That makes OR, XOR, and AND pairwise
distinguishable inside every demonstration, so query correctness never depends
on an unseen truth-table branch.

A weaker alternative—letting the three demonstrations collectively cover the
branches—could be valid, but it would require an episode resampling gate and
would create more ambiguous failures. The retained question counterexample at
`checks/question/finite-rival-ambiguity.json` shows why: OR and XOR both fit
three demonstrations lacking `11`, then disagree when the query introduces
`11`.

## D7 — Keep Racket as the only prototype label executor

The prototype materializes exact Racket for every setting and evaluates grids
through one persistent `RacketBridge`. A batch API was added after the initial
evidence-writer test exposed excessive one-grid subprocess round trips. Python
handles source guards, input construction, hashing, and rival bookkeeping but
never implements the output rule.

Public challenges are constructed by an allowlist: training inputs/outputs and
query inputs only. Seeds, selected parameters, Racket text, rule hashes, and
query outputs remain private. Evidence files are source-bound and hashed in
`checks/parametric/occupancy-rule-v1/manifest.json`.

## D8 — Do not integrate the prototype into production

The current runtime has no production parametric-rule API, and this packet does
not grant variant or training approval. The workspace is therefore separate
from `generator.py`; the selected `RULE_HASH`, canonical authority, catalog
status, and ordinary generation path remain fixed. Future integration requires
a separately reviewed API, admission policy, and broader seed/rival evidence.

## D9 — Recheck teaching quality on the final source

Although the scalar fix does not change lawful grids, I ran a current-source
census rather than relying only on prior notes. With three demonstrations per
query, `--per-band 100 --rotate-query` produced 300 lessons, 1,200 pairs, and
1,200 query rotations with zero declared-rival ambiguity and 1,197 unique inputs.
This verifies the actual final bytes against the declared rival set, not all
possible hypotheses.

## D10 — Keep audit targets findings-only

For `09647f283588`, I retained a source-bound reproducer showing the advertised
`overlapping_frames` texture destroys the first frame's shared corners and
leaves only one canonical-valid window. I did not edit that target.

For `a926d2195b22`, bounded inspection found no issue: 185 portable tests passed,
the task probe covered 128 override endpoints and 256 rotated lesson queries,
and 64 generated inputs matched canonical Racket output. This is a clean audit
within those checks, not universal approval.

# Decisions for review `review-e7eb0987eb566cb5`

## D11 — Complete the retained external correction, not a new production rewrite

The selected production generator remains byte-identical at SHA-256
`11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3`.
This review addresses the retained `external_correction_pending` finding for the
separate occupancy-rule prototype: ordinal public names leaked seed order, and
the episode shape was fixed at three demonstrations plus one query. The
canonical rule, generator distribution, `RULE_HASH`, and catalog status were not
changed.

## D12 — Bind public identity to exact visible bytes

The writer now uses `reviewer_support.public_challenge_bytes` and
`public_challenge_id` as its public boundary. Public files are named by the
SHA-256 of the exact bytes written, sorted by public ID, and duplicate visible
payloads are rejected. Seeds, hidden settings, Racket programs, private fields,
and query answers do not contribute to the ID. This removes both the previous
`episode-NNN` order leak and any need for seed-derived collision suffixes.

## D13 — Expose independent counts with explicit finite limits

The default episode now contains three demonstrations and four queries. Callers
may request each count independently in `1..16`. Inputs are sampled
deterministically from the selected generator with duplicate-grid rejection and
a bounded attempt budget; failure is explicit if enough unique lawful inputs
cannot be drawn. Every retained grid still contains all four occupancy relations,
so no requested count weakens the declared OR/XOR/AND identifiability contract.

## D14 — Keep labels and semantic checks Racket-backed

The final prototype and test hashes are:

- prototype: `b5bbe08a4a7faa517c9705aac37859eb10696a6aafdc2bc9dcccc86167f93873`;
- focused tests: `b9741b87574b400935a8f8a0708e5b99e735d2ece3a311c9b146a03bd00b9321`.

The retained evidence uses seeds `1,0,5`, three demonstrations, and four queries
per episode. It exercises all three settings, labels 21 generated pairs through
Racket, replays six canonical pairs, checks nine finite rival/episode
combinations, and reports zero declared-rival ambiguities. All seven inputs in
each episode are distinct. This is finite evidence for the prototype only, not
variant approval or a proof against arbitrary hypotheses.

## D15 — Treat supplementary tickets as bounded support work

The pinned `5cff0d794bdf` audit witness reproduced on its exact source/assets:
ten ignored controls remained baseline-identical, seven advertised valid-range
overrides were rejected, and all 19 Racket outputs matched the independent
mirror. That preserves the existing unresolved audit assessment; it does not
clear it.

The pinned override-reporting tool request also reproduced. Its JSON already
defaults to a 27-root-cause summary, omits all 1,596 case rows, and gates full
rows behind `--full-results`; the remaining accepted work is narrower—make the
human console/aggregate summary foreground category/root-cause totals instead
of 5,332 raw findings and default per-seed witnesses. No shared tooling was
modified in this review.

Current source-bound export inspection: `generators/74a14031dc79/evidence/parametric-public-export-inspection-e7eb0987eb566cb5/manifest.json`. The earlier export/count finding is resolved only for these corrected prototype bytes; all other audits and approval boundaries remain unchanged.

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

Current selected occupancy writer already has independent 1..16 counts, exact visible IDs, duplicate rejection and sorted physical writes. Ported the useful deterministic Racket verifier from the later return without its lower total-count cap, and retained its public-focus workspace separately; actual public query predictions remain unverified.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->

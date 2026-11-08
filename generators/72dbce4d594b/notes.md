# Working notes: 72dbce4d594b

## Review 2026-10-02 — review-1ebfbb9437c3e8aa

Rule authority is unchanged: `RULE_HASH = d291f7b88b55`.
Generator version advances from 2.0.0 to 2.1.0.

The old battery passed all 12 stages, but its lesson rivals were incomplete.
`workspace/baseline_ambiguous_lesson.json` retains seed 0 / start 0 / medium:
identity and 180-degree rotation agree on its first domino demonstration;
changing command 1 to rotation by 180 fits all four demonstrations and changes
its query answer. The old `lesson_identifiable` returned no findings.

The revised lesson check includes all 28 single-command D4 substitutions in
addition to the original seven rivals. This covers the 8^4 factorized command
lookup-table family without enumerating every table. It is not a proof against
all possible wrong programs. The independent matrix-based implementation in
`workspace/instruction_table_probe.py` checks consensus without query labels.

Use **five demonstrations**. Every consecutive five-sample window has one
canonical-scale example and four full-D4-asymmetric teaching examples, one per
command. All three blue candidates in teaching examples are asymmetric, so the
chosen object's asymmetry cannot reveal its rank. Existing `canonical_234`,
`spread_246`, and `wide_358` overrides remain supported. Explicit overrides can
create uninformative lessons; run the lesson gate on the actual exported pairs.
The shared export worker does not enforce EXAMPLES_NEEDED or this gate: pass
`--train 5` explicitly. This patch does not change shared export policy.

Measured probe: 64 seeds, 12 starts, three bands; baseline 1215/2304 ambiguous,
revised 0/2304. Labels there come from the Python mirror. The separate relocated
reference probe checks canonical, retained counterexample, generated and override
pairs against canonical Racket. Full reports accompany the returned review ZIP.
No model was trained; these are data-identifiability results, not measured Qwen
accuracy gains. Existing root-level inherited test has a stale rule-hash literal;
it is outside the packet's permitted edit scope and was left unchanged.
## Current reviewer considerations

Source SHA-256: `a6dba3cfd52647f610cd11abab494e063f8d766dc054f70c0e9ba90ee7e67880`.

# Distribution decisions and rejected alternatives

Task `72dbce4d594b`, assignment `review-1ebfbb9437c3e8aa`.
The baseline is immutable. This file distinguishes rationale visible in the
code from inferred intent; no unrecorded historical motivation is asserted.

## D1. Preserve rule semantics, colors, and object grammar

**Prior state and rationale.** The supplied rule, canonical pairs and generator
agree on three blue four-connected components with distinct areas, red count
for ascending rank, green count for a geometric command, and a cyan bounding-box
anchor for the orange output. These semantics are explicit. Reasons for the
original task author's exact palette are not recorded here.

**Decision.** Preserve the Racket authority, output mirror, allowed palette,
rank range 1..3, command range 1..4, unique target, and output-fit checks. Target
anchoring means bounding-box corner: a shape need not paint the target cell.
Retain existing grid bounds, marker layout options, target zones, and difficulty
interface.

**Rejected alternative.** Reinterpreting a green command or changing target
anchoring would repair a different problem and break canonical equivalence.
Color randomization without a new cue would alter color-specific semantics.

**Probe and limit.** Before/after authority hashes agree; 406 cases agree with
canonical Racket. This is reference-backed sample coverage, not an exhaustive
proof over every valid grid.

## D2. Five demonstrations instead of four

**Prior state and rationale.** `EXAMPLES_NEEDED=4` accompanies four commands. It
is reasonable to infer a desire to demonstrate each command once, but a specific
recorded proof that four examples are sufficient was not supplied. Symmetric
shapes make one occurrence inadequate as a teaching witness.

**Decision.** Reserve one of each five default sample slots for a canonical-scale
anchor, and use the other four as informative command witnesses. Every consecutive
five-index window contains all five phases. Increase `EXAMPLES_NEEDED` to five.
This adds 25% more demonstration pairs than four, not a measured 25% token cost:
shape density and grid dimensions also affect serialization.

**Alternatives.** Four fully asymmetric examples would use fewer pairs but lose
small canonical cases as regular anchors. Five unconstrained random examples can
still miss commands or show symmetric shapes. Arbitrary six-or-more examples add
cost without addressing the construction as directly. A more sophisticated
set-cover episode assembler is promising but belongs in shared code, outside
this task's allowed scope.

**Probe and limit.** 0/2,304 revised five-demo windows are ambiguous under the
finite table family, versus 1,215/2,304 old four-demo windows. This combines a
new schedule, shape policy and demonstration count; no single-factor causal
ablation or model-accuracy gain is claimed. Default stream guarantees do not
cover explicit overrides or filtered/nonconsecutive windows.

## D3. Reach all profiles within each seed

**Prior state and rationale.** Four names distinguish canonical anchors, layout
shifts, size spread, and mixed examples. The old `(seed + 2*i) % 4` index samples
all profiles when seeds are pooled but only two for any one seed. Why a stride
of two was originally chosen is unknown.

**Decision.** Use phase `(seed+i) % 5`, mapped to profile indices
`(0,1,2,3,3)`. The mixed profile occupies two slots so the four teaching slots
fit alongside the anchor. Phase zero is the canonical anchor. Rank keeps its
period-three schedule; transformation assignment gives each teaching phase its
own command. A full 15-index cycle combines all rank values with teaching phases.

**Alternatives.** Merely changing stride two to stride one fixes name coverage
but not teaching ambiguity. Fully random profile/command selection makes
coverage a probability rather than a property of consecutive windows.

**Probe and limit.** Per-seed reachability and sliding-window tests supplement
aggregate profile metrics. The schedule is a synthetic-stream constraint; an
arbitrary shuffled batch is not automatically an identifiable episode. Deterministic
seed/index scheduling should not itself be treated as a learned task cue.

## D4. Informative geometry without a selected-object shortcut

**Prior state and rationale.** Existing size profiles `(2,3,4)`, `(2,4,6)`, and
`(3,5,8)` provide small and more varied objects. Small objects can have exact
symmetries. The baseline attempts to avoid an unchanged selected shape for a
non-identity command, but that does not separate all competing commands, nor
does it disambiguate identity from a wrong transformation.

**Decision.** Add teaching profiles `(4,5,7)` and `(4,6,8)`. Require eight distinct
D4 orientations for **all three** components in teaching slots. Requiring only
the selected object to be asymmetric would make it identifiable without reading
the red rank instruction. Preserve one canonical-scale example per five slots.

**Alternatives.** Forcing every object in every example to be asymmetric removes
small-object coverage. Requiring only that the true transformation change the
shape leaves mirror/rotation and identity confusions. Picking one memorized
asymmetric template per size narrows shape diversity more than bounded random
growth with a fallback.

**Probe and limit.** Tests verify all three teaching candidates, all four
commands, and asymmetry for sizes 4..8. The battery's profile, diversity, grammar
and override stages pass. Larger objects change the distribution, and the effect
on small-model generalization is unmeasured. Canonical-scale cases remain legal
and intentionally can be individually uninformative.

## D5. Bounded generation and explicit overrides

**Prior state and rationale.** The generator already uses bounded placement and
shape growth, keyed axes, and explicit override labels. Existing overrides may
be used by evaluation code, so changing their meanings would be an integration
regression.

**Decision.** Use at most 24 attempts to grow an asymmetric teaching object; then
use a checked unequal-arm L with randomized D4 orientation. Never silently fall
back to a symmetric object when asymmetry was required. Preserve all three old
size-profile strings and exact requested areas. Skip the impossible search for
an object changed by identity. Keep override handling separate from default
teaching policy.

**Alternatives.** An unbounded rejection loop risks hanging on restrictive
inputs. A silent fallback compromises identifiability while reporting success.
Overriding a caller's explicit small size with a larger size violates the axis
contract and conceals test conditions.

**Probe and limit.** Legacy overrides have 36 focused rank/command/profile tests;
the canonical-reference probe covers all five size profiles × three ranks ×
four commands at minimum declared grid dimensions. Explicitly requesting tiny
symmetric objects or a fixed command can still make an episode ambiguous. Call
the lesson gate on the actual assembled lesson rather than treating valid
individual examples as sufficient.

## D6. Query-answer equivalence, not complete rule recovery

**Prior state and rationale.** Seven named wrong rules check important rank,
transform, and anchoring shortcuts. Their intent is visible, but the collection
is not complete for command-table substitutions.

**Decision.** Retain the seven and add all 28 single-command D4 substitutions.
Also supply an independently implemented generic `factorized_gate`: intersect
compatible candidate predictors for each instruction key; then compare survivors'
answers on each query, without reading a query label. Rule ambiguity is allowed
when all remaining rules agree on the query answer. Empty hypothesis sets and
predictor exceptions produce explicit failures, not vacuous passes.

**Why factorization is sufficient within this family.** A full candidate table
assigns a transform to each command independently. Every demonstration constrains
only its observed command. A table that fits all demos but disagrees on a query
has a disagreeing transform at that query's command; substituting only that
transform into the true table supplies a single-command witness. Thus 28 local
alternatives cover 4,096 whole tables, conditional on the fixed component/rank/
anchor interpretation. The original non-table rivals provide additional but
not exhaustive coverage of those other interpretations.

**Alternatives.** Requiring one surviving rule rejects harmless symmetry on both
demos and query. Checking command presence only misses the domino counterexample.
Enumerating all tables repeats work. Arbitrary-program uniqueness is neither
what this finite implementation tests nor a claim made by this review.

**Probe and limit.** The retained baseline case is detected independently; generic
tests cover harmful and harmless ambiguity, inconsistent demonstrations, and
exceptions. Hypothesis-family coverage remains a design choice. A family that
includes interpretations excluded by an explicit task convention can cause a
false positive; a family that omits a plausible shortcut can cause a false
negative. A failed gate is grounds for review or resampling, not grounds to
silently change the reference answer.

## D7. Leave admission policy and unrelated defects visible

**Prior state and rationale.** Shared episode export accepts a requested training
count; it does not enforce `EXAMPLES_NEEDED` or this task's lesson hook. The solve
preparer uses five here but records `lesson_identifiability_checked=false`.

**Decision.** Do not edit shared workers or audit targets in this scoped return.
Provide the runnable gate and explicit `--train 5`/`n_train=5` integration guidance.
Record the stale inherited assertion and shared test fixture failure as remaining
failures rather than skipping tests, modifying evidence, or claiming full green.
Keep training admission false and expose earlier rule knowledge in the solve.

**Alternative rejected.** Fixing shared infrastructure in the same patch could
be worthwhile in a different assignment but would violate this packet's scope
and obstruct independent attribution. Generator metadata alone is not a substitute
for an actual post-assembly admission check.

**Next decision.** A maintainer should enforce a query-consensus gate on exported
lessons after filtering/overrides, then compare held-out model performance under
a fixed training-token budget. No such model experiment was run in this review.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/72dbce4d594b/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

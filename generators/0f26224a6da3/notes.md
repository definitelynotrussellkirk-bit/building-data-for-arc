# Working notes: 0f26224a6da3

Review `review-82548b4b24894693` replaced the baseline lattice curriculum and ineffective override declarations. Final generator SHA256: `24c6043d88d704a80d9649f6b1e965406742cb3c064fc6738f763e3b2dc8aea7`. Original source SHA256: `48b8418aa3263071128e408f5159b3d75b79bdb49f905a0bb07da84885ae251a`. The Racket authority is unchanged.

R1: independent Racket-backed before/after census uses seeds 0..9, indices 0..8, four difficulty settings (360 draws each). Final outputs match Racket on 360/360 draws. For three-demo/one-query consecutive fixed-seed lessons, starts 0..5, the 240 overlapping windows change from 240 with surviving rivals to 0. Final unique inputs are 220/360 versus 269/360 before; do not count repeated difficulty draws as distinct training samples. This measures semantic coverage, not model accuracy.

R2: source controls now have explicit helpful domains and fail loudly. Validators reject invalid colors, unsupported shapes/counts, non-domino inert components, and conflicting expansion fronts. Different-color collision policies are not taught by the canonical data; the chosen helpful distribution excludes those ambiguous fronts rather than modifying Racket. Same-color diagonal overlap is intentionally included.

Final required battery: 12/12 green; task-local tests: 43 passed. Shared Racket-enabled suite: 171 passed, one timeout-progress test failed; no shared change was made. Host diagnostics support an interpreter-startup timing issue, not an established output-capture defect. Evidence lives in the retained return ZIP's checks directory; the workspace tools reproduce it from a packet checkout.

Fresh solve was made from the final generator with prior rule exposure explicitly declared. It passed visible demonstrations but private query correctness remains unknown. Do not label the work log as blind or as a captured model trace. A deliberate post-assembly negative is a separate diagnostic, not an invented natural failure.

The main maintainable extension is the post-assembly lesson gate. Shared admission integration and repairs to audit-only targets remain out of scope. Continue from the workspace README, not a new random assignment. Imported associated notes remain unchanged under evidence/associated_notes.jsonl.
## Current reviewer considerations

Source SHA-256: `24c6043d88d704a80d9649f6b1e965406742cb3c064fc6738f763e3b2dc8aea7`.

# Decisions and rejected alternatives

Task `0f26224a6da3`, assignment `review-82548b4b24894693`.
Before source: `48b8418aa3263071128e408f5159b3d75b79bdb49f905a0bb07da84885ae251a`. Final source: `24c6043d88d704a80d9649f6b1e965406742cb3c064fc6738f763e3b2dc8aea7`. Rule authority unchanged.

## R1: Keep the rule; repair what the inputs teach

The canonical examples and Racket agree on four-neighbor isolation and clipped cardinal expansion. No reference-label defect was reproduced on supported generated inputs. Changing the Racket rule would obscure the actual defect: examples that never distinguish plausible wrong rules. The original narrow placement plausibly made valid singleton generation easy, but its author's rationale is not recorded; that motivation is an inference, not historical fact.

Reject rewriting the rule merely to match the baseline's interior-only data. Keep zero background, integer colors 0..9, original-input isolation, and preserved foreground. Labels remain Racket-derived. The Python mirror exists only to express witnesses and check parity. Evidence: canonical checks, 360/360 final draw agreement, and collision diagnostic in `checks/curriculum-final.json`.

## R1: Remove the coordinate lattice without making placement uncontrolled

Original samples used interior coordinates congruent to 1 modulo 3. Replace this with shuffled eligible coordinates. Other than the deliberate diagonal pair, sources have Manhattan separation at least 3; active sources stay at least 3 from domino cells. Layout uses a bounded 256-attempt search and raises on failure rather than truncating source counts or silently falling back to a lattice.

Reject unrestricted dense random points: they blur the active-source-count contract and introduce competing expansion fronts. Reject retaining the lattice with occasional translation: global modulo structure would still be a shortcut. Final census reaches all nine row/column residue pairs; 359/360 draws have a source off the old lattice. This is finite evidence, not an exhaustive placement guarantee.

## R1: Three-scene coverage instead of independent rare witness sampling

The scene is `(seed + sample_index) % 3`: interior, edge plus domino, diagonal pair plus domino. At fixed seed every three consecutive demonstrations include all scene types, regardless of starting residue. Edge examples teach clipping, dominoes teach non-isolated cells are inert, and diagonal neighbors distinguish four-neighbor from eight-neighbor isolation.

The original distribution did not supply these contrasts. Reject an independent low-probability mixture: a healthy aggregate witness rate does not ensure any particular lesson is informative. Reject relying only on a query counterexample: an unsupported query asks the learner to guess rather than infer. Test all cyclic starts; the census uses starts 0..5 across ten seeds and four bands (240 overlapping windows). Initial local regression tests use a smaller five-seed/all-three-start check.

This schedule is itself a distribution choice, not a general rule property. It guarantees coverage only without scene overrides, with a fixed seed and at least three consecutive demonstrations. Order can correlate with the scene; it must not be mistaken for an output rule. Final assembly should preserve coverage or run R3 after resampling/shuffling. No claim covers all arbitrary lesson assembly policies.

## R1: Compact baseline-compatible scenes plus larger contexts

Helpful dimensions are 7..15. Interior defaults stay 7..9 to retain compact canonical-like examples; other scenes use 7..15. Explicit dimensions are exact within 7..15. Source counts are exactly 2..5, excluding the domino; easy defaults 2..3, medium/unspecified 2..4, hard 3..5.

The original actual defaults were compact and the declared axis surface was broader than the tested support. Narrow the public helpful contract to dimensions and counts exercised at boundaries, rather than pretend to support all historical metadata. Reject tiny grids that make exact placement plus a domino unreliable. Reject much larger grids here: extra empty tokens are not the missing semantic evidence. The tests exercise 7x7, 7x15, 15x7, and 15x15, source counts 2 and 5, and all scenes. This does not exhaust every seed.

`strict_canonical_like` is a semantic subset test: compact interior isolated sources, no distractor, no overlapping expansion fronts. It accepts all three canonical inputs, but is not an exact probability model for the canonical set. Final census: 120/360 canonical-like inputs. One third is a deliberate balancing choice, not an empirically optimized model-training ratio.

## R1/R2: One simple inert component, not arbitrary object clutter

Each non-interior scene includes exactly one cardinal domino, possibly mixed-color. It is small enough to isolate the active/inert distinction. The helpful validator allows no inert component or exactly one two-cell cardinal domino, but need not reconstruct the sampler's exact probability support.

Reject arbitrary large connected shapes in this change: they add layout complexity without being needed to refute expand-everything. More complex distractors are a future breadth experiment, not silently included. A validator's semantic acceptance region can be broader than exact sampling support; these are identified separately in the audit reports.

## R1/R2: Same-color overlaps teach isolation; conflicting overlaps stay diagnostic

A diagonal pair is four-isolated but not eight-isolated. Give its members the same color so their shared expansion targets are unambiguous. The unchanged Racket implementation has a row-major first-writer policy for different-color collisions; the canonical pairs do not teach that policy. Normal helpful generation excludes such collisions and the validator rejects them.

Reject training arbitrary scan-order priority as if it followed from the visible task. Reject forbidding every overlap: that would remove a compact eight-neighbor counterexample. Retain a two-color distance-two collision grid and its actual Racket output in `checks/curriculum-final.json`, explicitly outside the helpful domain. No authority was edited to remove the underlying reference behavior.

## R2: Make a smaller override API truthful

Keep exact grid_h, grid_w, and n_cells; implement palette_kind and its texture alias; expose scene. Palettes are warm (2,4,6,7,9), cool (1,3,5,8), broad (1..9), and primary (1,2,4). Sampling is random from the chosen pool, not the old summary's claimed cyclic sequence. Color 9 is valid and should not be omitted by stale prose.

Remove inert or unprobeable axes rather than implement unrelated controls just to satisfy metadata. Unknown keys, malformed dimensions/counts, invalid enums, and conflicting texture/palette requests now fail loudly. `observe_overrides` reports realized dimensions and active-source count. No exact palette-size guarantee is advertised. Evidence: initial red tests, final override matrix, standalone lint, and task-local tests.

Retain no_cells, full_cells, and full_grid only as explicit diagnostic textures. They are outside HELPFUL_TEXTURES and fail the helpful validator. Diagnostic names conflict with explicit count or scene controls. Reject treating all-zero/no-op or over-dense scenes as ordinary training samples solely because Racket can execute some of them.

## R2: Validators must reject domain defects, not only adjacency

Validate rectangular nonempty structure, true integer colors (not booleans/floats), supported dimensions, exact helpful count range, inert-component shape, and conflicting blank expansion targets. A passing validator is not a substitute for Racket execution. Regression tests first reproduced 24 failures against the baseline; after implementation the 36 contract tests passed. Seven later gate tests initially errored at a fixture asserting the missing implementation and now pass. The combined final task suite has 43 passes.

## R3: Check the final lesson, not just the generator

Build a local JSONL gate over the actual assembled labeled episode. Import the current LESSON_COMPETITORS contract, require current generator identity, reject any wrong rival surviving the demonstrations, and separately report survivors that disagree on queries. Deep-copy probe inputs and report rival exceptions instead of certifying the lesson. A missing rival contract is not a semantic pass.

Reject an expensive model-based gate as the first test: the concrete ambiguity is decidable by cheap declared programs on already-labeled arrays. Reject a claim of universal identifiability: only three declared competitors are tested. Reject integrating into shared admission in this task-scoped patch. The tool is provided and tested, but the maintainer must select its shared call site. It assumes label correctness was checked upstream by Racket.

A legitimate easy lesson may intentionally leave a rival unrefuted, especially when the current query also agrees. The tool reports those separately from immediate query-risk, but strict mode still rejects them. Configure curriculum-tier policy at integration rather than quietly weakening semantic evidence. Source hash checks do not prove every provenance field is authentic.

## Reproducibility, duplicates, and limits

Use the existing keyed generator context rather than introducing global random state. This preserves deterministic replay and localized override effects. The pooled final 360-draw census contains only 220 unique input grids, compared with 269 before; unspecified and medium settings overlap and other bands can coincide. Reject presenting draw counts as unique training examples or independent confidence samples. Hash-deduplicate at data admission before making dataset-size claims; this return does not modify the shared ingestion pipeline.

No Qwen training was run. Improving identifiable semantic contrasts is a training-value hypothesis backed by programmatic measurements, not a measured model-accuracy gain. More competitors and held-out model evaluation could reveal remaining shortcuts.

## Honest negative evidence and scope

The first census exited 1 because its console JSON attempted to encode a Path after saving the report; changing the console field to a string fixed the tool, and a full rerun exited 0. Preserve both runs. The initially existing before-check output directory caused a separate refused invocation; preserve it rather than conflate it with generator defects.

The stress lesson intentionally combines three distinct canonical-like demonstrations with two varied queries from actual Racket-labeled exports. Its rejection is designed, not a spontaneous failed solve. The one fresh solve was recorded after the final generator bytes; prior rule exposure is yes, reference consultation during solve is no, and masked query correctness remains unknown.

A1-A3 are findings-only audits of immutable targets. T1 is an unresolved shared fixture failure. The site-disabled child control supports startup latency as the explanation but does not authorize changing shared test/runtime code inside this assignment. No independent reviewer subagent was available; verification is reviewer-local, with maintainer intake still required.

## Parametric family review — assignment review-11398f0d4b131dda

Preserved the exact canonical `all_isolated` Racket source and added
`rarest_color`, which selects the uniquely rarest color among four-neighbor-
isolated source cells before applying the same clipped cardinal expansion. The
minimum two-example lesson includes boundary clipping, a same-color diagonal
pair that is 4-isolated but not 8-isolated, and inert connected foreground. A
bounded 64-seed audit found no harmful survivor among the named isolation,
selection, fixed-color, and expand-everything rivals. A protected-Racket
counterfactual replacing the selected source set with all isolated sources
changed the output. Owner exact-source acceptance and training admission remain
pending.

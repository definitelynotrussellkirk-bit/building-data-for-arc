# Review notes — 2026-10-02

Assignment: review-638143ea0e678b59. Selected source SHA256:
`724f7b77d479c79be0a88f42f6c7ca6af567d6c49afcbbd884d95c547901565c`.
Original associated_notes.jsonl is empty; undocumented original intentions are
unknown. No selected or archival Racket authority was changed.

The original generator ignored dimension/count overrides and exposed inert
axes. Sparse positive-plus examples also under-tested occupied centers,
diagonal interpretation, and 3+1-color near misses. Canonical-profile support
was absent from medium/hard in the retained baseline census.

Implemented exact observable counts; explicit compatibility failures; strict
input validation; constructive separated placement; a canonical anchor mixture;
contrastive motifs; named witnesses and rival hooks. The task-local quality
probe validates its independent Python oracle against actual Racket outputs.
A separate canonical-rival audit probe implements a sample-based retention gate
without editing the findings-only audit targets.

Failed revisions are preserved in workspace/history. v1 allowed two equal-color
diagonal patterns to create an extra observed diagonal decoy between them.
The v2 repair forbids only that local color coincidence. The next battery caught
free canvases being too small for count overrides: v3 chooses feasible unpinned
dimensions, but preserves pinned dimensions or explicitly rejects conflicts.
The selected 4.0.0 source is that v3 review iteration.

Evidence in the return: checks/before/, checks/after-v2/, checks/after-v3/;
checks/v1-placement-counterexample.json; all red/green test logs; final Racket
census; portability run. Root REVIEW.md and DECISIONS.md index exact claims.

Limitations: 4-cell lattice placement is a detectable construction bias;
no overlapping objects, large-radius crosses, or broad natural clutter; default
background is fixed at zero; anchor repeats are possible; canonical anchors in
hard are intentionally not monotonically hard. Do not manufacture nonzero
background variants or alternate output colors, since that changes this rule.
No GPU training, held-out ARC transfer, or whole-lesson identifiability measured.

Post-solve update (G5): the actual fresh episode has three visible-consistent
candidate programs disagreeing on both query predictions. No query labels were
read. Added workspace/lesson_ambiguity_gate.py with five tests; the selected
generator and completed solver revision are unchanged. This demonstrates a
remaining lesson-assembly issue even though the family-level battery is green.
The gate is not yet integrated into the shared exporter. Total task-local tests:
45; see root reports and checks/lesson-ambiguity-final.json.
## Current reviewer considerations

Source SHA-256: `724f7b77d479c79be0a88f42f6c7ca6af567d6c49afcbbd884d95c547901565c`.

# Decisions and preserved experiments

Assignment `review-638143ea0e678b59`; repair task `f9dd4cf0f344` only.
Final generator SHA256:
`724f7b77d479c79be0a88f42f6c7ca6af567d6c49afcbbd884d95c547901565c`.
Baseline SHA256:
`06d1df7c30eb38aa045847ee59bfe448704b19d94cc9678a3c1f24de78ec2c18`.
The original associated_notes.jsonl is empty, so intentions not explained by
source comments are unknown. This is a review work log, not a captured model
conversation or token-level reasoning trace.

## D1 / G1 — accept exact controls, not decorative metadata

The original dimension/count arguments were swallowed in **overrides while
random dimensions/counts were used. Other AXES described variables that never
influenced the draw. The original rationale is unknown. A downstream curriculum
cannot trust a knob whose accepted value is not observable in the emitted input.

Chosen: retain five real axes, validate types and values before GenCtx's integer
conversion, reject unknown names, and recover realized dimensions/target/decoy
counts from pixels. Remove five inert axes and old inert helpful-texture names,
rather than adding fake randomness or silently retaining aliases. Version 4.0.0
signals the compatibility break. This does NOT assert old callers are already
migrated: callers using the removed names must update.

Rejected: accepting knobs as no-ops; coercing True or 7.9 to dimensions; silently
clamping explicit counts. The battery's 366 override combinations use 30 seeds
per band (32,940 scheduled draws); the final report records 28,080 accepted,
4,860 structured incompatibilities and zero findings/warnings. These are
scheduled invocations, not distinct grids. See checks/after-v3/checks/
f9dd4cf0f344_after_override_results.json.

## D2 / G2 — teach the predicate boundary with positive-plus-negative scenes

The original partial-arm and all-distinct-color decoys did not adequately
challenge majority color, occupied-center overwrite or diagonal confusion.
Chosen: 3+1-color, occupied-center, partial-arm, diagonal-only and 2+2-color
motifs next to genuine positives; expose targeted textures for controlled
curricula; provide named semantic witnesses linked to deliberately wrong rules.
All labels remain supplied by Racket; diagnostic Python rules are not training
label authorities. The original reason for its restricted decoys is unknown.

Rejected: renaming a texture without changing grids; assigning rivals that are
mathematically equivalent to the target. In particular, iterative vs one-pass
filling does not distinguish this predicate: neighboring zero holes prevent
either cell from firing, and every filled hole already had only nonzero
neighbors. Repeated application cannot unlock another hole. Tests check
idempotence on generated examples, but no claim is made that finite tests prove
arbitrary-rule equivalence.

Final and baseline independent censuses use seeds 0..255, sample_index=seed,
256 draws per band; every label is compared against actual Racket. Both have
zero mismatches in 768 comparisons. Before -> final counterexamples per wrong
rule: majority 15 -> 170; occupied overwrite 0 -> 167; diagonal 0 -> 186;
three-arms 459 -> 243. The last change is a real tradeoff: broadening the
negative mixture reduced partial-arm emphasis. Do not report all rivals as
improved. Evidence: checks/probe-baseline-racket.json and
checks/probe-final-v3-racket.json.

## D3 / G3 — retain canonical-style support in all difficulty bands

Chosen: a keyed one-third plain-anchor mixture with small canvases, exactly two
positives, distinct colors and no decoys, independent of difficulty. The other
two-thirds provide larger/diverse/contrastive scenes. The pooled before profile
census hid zero medium/hard support. The final 20 draws per band have envelope
support 10/20, 8/20, 7/20 rather than 3/20, 0/20, 0/20. These are shape/palette
profiles, NOT exact canonical-input reproduction or training accuracy.

Rejected: scaling every hard example to large grids and many objects; defining
"hard" to guarantee a strictly harder conceptual rule; declaring profile
support opt-outs to make a failing gate disappear. The mixture is a deliberate
curriculum choice, not evidence that one-third is optimal. A training ablation
would be required to tune the weight. Exact-profile pooled hits were 1/60
before, 8/60 final; envelope hits 3/60 before, 25/60 final. Seed schedules are
retained in the battery command receipts/reports. Canonical inputs themselves
are all accepted by the final self-check.

## D4 — constructive packing and truthful failure handling

Chosen: separated 3x3 boxes on a randomly phased four-cell lattice. This gives a
simple constructive capacity test, bounded runtime, no rejected-draw fallback,
and observable counts. Motif/color/layout draws use the existing keyed GenCtx.
Zeros retain their semantic background role; foreground colors vary 1..9.

The v1 implementation failed two tests and its 768-draw census found one
exception. Same-color diagonal decoys could create a third observed diagonal
center between them. The exact seed 8/sample 0, 11x15, pluses=2, n_decoys=2,
texture=diagonal counterexample is in checks/v1-placement-counterexample.json.
Chosen v2 repair: forbid only adjacent diagonal motifs having the same color,
not relabel the observer or repeatedly resample scenes. Archived v1 SHA256:
`cc2cc389f509a817a374ed68c1da0abd62062835ace25c37de26d782852147c1`.

v2 passed its then-current 27 tests and 768 Racket comparisons but failed the
next battery's override stage. The broad battery found 5,964 findings among
32,940 scheduled draws: counts could be rejected because unpinned dimensions
happened to be small; free plain texture could conflict with pinned decoys.
Chosen v3 repair: draw a feasible canvas when dimensions are free; exclude
plain for a pinned positive decoy count; reject explicit contradictory modes
with the involved axes. New count-override tests failed before the repair
(7 failed, 28 passed) and passed afterward (35 passed). Never discard the
failed broad battery merely because the narrow tests passed.
Archived v2 SHA256:
`e7c3d736b8879f34e7b65724fcca8d71d46530c6aa9e2836737b8620185c6cfb`.

Limitation: the lattice is a construction shortcut a learner could recognize.
The change does not cover overlapping motifs, arbitrary clutter, radius>1 or
nonzero backgrounds. Broader placement was deferred to a separate measured
ablation; it would complicate the exact-count guarantee. Source defaults are
unchanged between v2 and final v3 for the retained 768-draw schedule, while
explicit override behavior is repaired.

## D5 — explicit lawful identity controls, informative defaults

An all-zero or partial-only scene is a useful counterexample, but it does not
teach an output change alone. Chosen: default self-check requires at least one
actual fire; explicit negative texture metadata or pluses=0 permits identity.
Retain the existing negative-fixture hook and declare those textures lawful.
Rectangularity, integer values, bounds and unknown keys are checked separately.
Rejected: removing negative tests; allowing malformed grids because no target
is detected; treating every identity as globally invalid ARC data.

## D6 — reusable evidence rather than model-performance claims

Built quality_probe.py (source/rule-bound before-after census and Racket
parity), canonical_rival_probe.py (findings-only audit adapters and a runnable
canonical-counterexample retention gate), and portable_probe.py (moved-runtime
execution with no source-tree import leakage). The new task-local tests cover
controls, purity, negative modes, hard counterexamples, and audit/gate fixtures.
No shared tool or audit target changed. Bootstrap failures involving legacy
scripts imports are preserved; the probes now use the repository's supported
runtime stager rather than guessing sys.path.

The gate prototype flags only canonical-refuted rivals wholly unsupported in a
sampled band; it does not demand every canonical motif in every lesson. This
avoids vetoing unestablished/equivalent rival hypotheses. It is finite and
adapter-based, not a full automatic semantic synthesis system. The row audit
reproduces its failure; the green-plus audit has real generated counterexamples
and therefore does not trigger a false universal-shortcut claim.

No Qwen training, GPU run, held-out ARC benchmark or learning-speed comparison
was performed. Known-rival sample coverage is not whole-lesson identifiability.
Current hooks intentionally do not claim `lesson_identifiable` or exhaustive
competitor coverage. Root QUESTION_ANSWER.md proposes the smallest next gate
integration; central framework integration remains outside this assignment.

## D7 / G5 — fresh-lesson ambiguity is an actual remaining defect

After the generator work, the required solve drew three positive-only visible
examples and two queries with occupied/diagonal cases. One authored solver fits
3/3, but two intentional alternative-hypothesis probes also fit 3/3 and disagree
on both query predictions. No query labels were used. This upgrades the earlier
lesson-identifiability limitation from a possibility to measured evidence for
this particular challenge. The episode is finished and retained, not rerolled.

Built a generic public-only lesson gate with a trusted candidate adapter,
source hashes and five tests. It rejects answer-bearing query input, reports
candidate exceptions rather than silently dropping them, and isolates candidate
input mutations. Surviving programs that agree on the actual query do not veto.
This tool was added after the solve; the selected generator and submitted
solver revision remain unchanged. Integration into shared lesson selection is
out of scope and explicitly remains unfinished, rather than mutating the
frozen challenge to hide the failure. The exact counterexample and runnable
gate are the next maintainer's starting point. QUESTION_ANSWER.md now prioritizes
this actual lesson-level issue over a second family-only sampling gate.

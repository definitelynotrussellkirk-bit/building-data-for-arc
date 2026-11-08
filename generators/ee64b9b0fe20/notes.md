# Current generator notes — ee64b9b0fe20

## Intended rule and source identity

Version `3.1.0`; final generator SHA-256
`f416fc7ff7204f8c8fce0862f1a0c56bc6c0dcae0c08dfb28db381ab7760bbd1`.
The canonical Racket authority was not changed: normalized `RULE_HASH=e0863705f64c`,
raw program SHA-256
`f9da660747745e4cd4d51155a2ceeb486685daffe64195f7e65dafd59ef200cd`.

The rule chooses the unique nonzero modal field, extracts monochromatic
four-connected non-field components, discards whole-canvas-bounding-box frames,
sorts remaining objects by cell count, and bottom-packs their bounding boxes
left-to-right. Zero may be an object color. Same-color disconnected components
remain separate. Different colors may touch. Object cell counts are distinct.

## Current decisions

**R1–R6 retained from the prior repair.** Whole scenes retry instead of silently
losing requested objects; valid canvases span 10..18; zero-inclusive objects,
repeated colors, contact, sizes through 12, exact overrides, named semantic rivals,
and copied-runtime Racket checks remain in force. Canonical selected rule copies
stay synchronized; archival raw-code copies remain intentionally untouched.

**R7 reversed — frame coverage is now an episode invariant.** Version 3.0 allowed
a three-demonstration lesson to be entirely frameless while asking framed queries,
so a border-preserving rival fit all demonstrations. Version 3.1 sets default
frame presence by `sample_index % 2`; every adjacent default pair contains one
frameless and one framed example. `rival_preserve_frame` is executable and appears
in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`. The retained baseline measured
33 ambiguous three-demo windows among 540 sampled windows; the final 300-lesson
census found 0 ambiguous production lessons and 0 ambiguous query rotations.
Evidence: `checks/probes/baseline-frame-gap.json` and
`checks/lesson-census-final.summary.json`.

**R8 — public calls are strict.** `seed` and `sample_index` are literal integers,
booleans/floats/strings are rejected, negative sample indices are rejected, and
only `None/easy/medium/hard` are legal difficulties. This replaces inherited
coercion/else-branch behavior exposed by the first full after battery. Focused
matrix regressions cover every rejected scalar class.

**R9 — canonical shortcut evidence is final-source bound.** The strongest declared
canonical rival remains “always treat color 7 as background.” It fits all eight
labeled pair occurrences across the two canonical variants. Final source
`generate(0, 0, difficulty="easy")` has true field color 1 and refutes the rival;
canonical Racket agrees with the local mirror. Evidence:
`checks/question-answer/fixed-background-7-final/probe.json`.

**R10 — parametric work is separate and proposed only.** The task-local prototype
chooses `sort_order` once per episode (`ascending` canonical or `descending`).
Each setting has three demonstrations and one query, and every pair distinguishes
the alternative. Executed program hashes are
`f9da660747745e4cd4d51155a2ceeb486685daffe64195f7e65dafd59ef200cd`
and `7bc914e4dd035184d4baa2608c83e6af3ba1f3fb469b3d850e2996da75bfefad`.
It does not modify production generation or canonical authority.

## Verification snapshot

- Final battery: 12/12 stages green, source hash above.
- Task-local tests: 124 passed in the copied runtime and 124 passed directly.
- Lesson census: 300/300 lessons materialized; 1,200/1,200 unique pair inputs;
  0 ambiguous production lessons; 0/1,200 ambiguous rotations.
- Fresh exposed solve: first revision passed all 3 visible demonstrations; prior
  rule exposure declared yes, reference consulted during solve declared no.

## Known limits

Named-rival checks are finite, not a proof of unrestricted identifiability.
Tied object sizes, arbitrary huge objects, one/no-object production scenes and
unbounded rule parameters remain outside the teaching domain. The deterministic
frame alternation is a curriculum policy, not an IID sampler. No model training,
transfer benchmark or hidden-query score was run. The sort-order extension is a
prototype, not approved canonical behavior.

Audit-only targets `69dbf44065e2` and `ef4af8761400` were inspected but not edited;
findings are in `AUDIT.md` and source-bound evidence under `checks/audit/`.

## Current owner source and evidence limits

Accepted3.1.0 strict seed/index/difficulty call validation and alternating frame presence by sample-index parity. Added executable preserve-frame rival/witness, so each default three-demo lesson and every four-pair holdout retains frame/no-frame evidence; explicit frame overrides opt out of the default promise. Canonical Racket unchanged. Reviewer12/12 battery green and124 portable tests pass,300 production lessons/1200 rotations clean with1200 unique inputs. Profile floor26/60 exact (easy1/20,medium14/20,hard11/20),8 canonical inputs supported. Bounded rivals/samples do not prove universality. sort_order ascending/descending prototype has two3-demo/1-query episodes, exact canonical default and actual Racket labels. Owner moved public challenges out of setting-named directories and assigned visible-content hashes, with actual Racket exports and focused regressions; original source/gallery retained. No production parameter API, variant approval, training admission or owner full battery rerun.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-c88b79a930311a45:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5de9a794b56a8a3b4aafebdea12d3fa826f5bbf1aee8ffde17b4a8d43d08fea2`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current3.1.0 alternating framed/unframed schedule and executable preserve-frame rival directly repair this old query-only branch gap. Reviewer300 lessons/1200 required query rotations clean,124 portable tests;canonical unchanged. Explicit bounded resolution,not generic acceptance or universal uniqueness.

### Assessment or prior finding

## ee64b9b0fe20

**Reproduced lesson-level shortcut gap; target left unchanged.** Generator SHA-256 `5de9a794b56a8a3b4aafebdea12d3fa826f5bbf1aee8ffde17b4a8d43d08fea2`, executed canonical rule hash `e0863705f64c`.

For easy seed 0 starting at sample index 7, the generated four-pair lesson has frame sequence `[false, false, false, true]`: all three demonstrations omit the optional whole-canvas frame, while the query includes one. The following plausible rival survives the demonstrations:

> Apply the intended distinct-cell-count sort and bottom packing, except retain any component whose bounding box spans the whole canvas in its original border cells.

The rival matches the supported Racket output on demo0, demo1, and demo2, then differs on the query (`[true, true, true, false]`). The query passes the target's `self_check` with no findings and was emitted by the documented ordinary generator domain. Exact inputs, authority outputs, rival outputs, seed/index metadata, and hashes are in `checks/audit/ee64b9b0fe20/frame-gap/`; the compact reproducer is `counterexample.json` and the supported apply receipt is `racket.json`.

This finding is notable because the target's complete source-bound battery is 12/12 green (`checks/audit/ee64b9b0fe20/battery/checks/ee64b9b0fe20_after_battery_summary.json`). The battery verifies the declared rivals but does not cover this undeclared frame-preserving competitor or warn that the exact `frame` branch occurs only in the query. No audit-target source was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-c88b79a930311a45-v0001/audit_assets.json), manifest SHA-256 `8345d52fe3555681aaf7f01c105c5833f5546685f7d0e951c66fa51214e30b02`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `f416fc7ff7204f8c8fce0862f1a0c56bc6c0dcae0c08dfb28db381ab7760bbd1`.

# Decisions — review-8ebeb38b6e564998

## D1 / R7 — require frame semantics at episode level

**Prior choice.** Version 3.0 sampled lawful framed and frameless examples but did
not guarantee that demonstrations covered both branches. The post-authoring solve
from the earlier review showed three frameless demonstrations and framed queries.

**New choice.** Default `frame` is `bool(sample_index % 2)`. Every adjacent pair
therefore covers both absent and present frames, and ordinary three-demo windows
cannot hide frame removal. Explicit overrides retain caller control and waive only
the default curriculum guarantee.

**Why.** The baseline probe found 33 ambiguous windows among 540 sampled windows,
including a retained seed-0 counterexample. Randomly increasing frame probability
would lower but not eliminate the episode defect. Rejecting all frames would erase
a real canonical branch. A deterministic short-period schedule is the smallest
falsifiable fix.

**Failure modes / limits.** The schedule introduces correlation with sample index.
It says nothing about arbitrary non-adjacent hand-selected lessons. Tests therefore
cover adjacent windows and the 300-lesson materializer rather than claiming IID
sampling.

## D2 / R7 — promote frame preservation to an executable rival

**Choice.** Add `rival_preserve_frame`, include it in `SEMANTIC_RIVALS` and
`LESSON_COMPETITORS`, and add a semantic witness that compares full outputs.

**Rejected alternatives.** A prose-only warning would not be exercised by the
semantic gate. Testing merely for the presence of a border would not prove the
correct output removes it. The executable rival captures the actual wrong
transformation and is checked on every materialized lesson.

## D3 / R8 — validate public coordinates before generator context creation

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`,
`sample_index >= 0`, and difficulty in `(None, "easy", "medium", "hard")`.

**Why.** The inherited context accepted booleans, floats/strings in some paths,
negative indices and arbitrary difficulty strings. Those values change schedule
semantics or silently fall into an unrelated branch. Exact validation makes
reproduction identities stable.

**Rejected alternatives.** Coercing with `int(...)` aliases distinct caller
inputs. Allowing all `numbers.Integral` would admit booleans. Treating unknown
difficulty as medium hides misspellings.

## D4 / R9 — refresh the canonical-shortcut counterexample on final bytes

**Choice.** Add `workspace/final_shortcut_probe.py`. It dynamically iterates
`CANONICAL_SHORTCUTS`, verifies canonical fit, searches a lawful final-source
counterexample, and binds it to a canonical Racket receipt.

**Why.** The previous retained fixed-background-7 artifact was valid for v3.0 but
reported the old generator hash. Reusing it without a final-source receipt would
make the answer historically true but not replayable against this return.

## D5 / R10 — prototype sort direction, do not change production

**Choice.** Implement `sort_order={ascending,descending}` only under
`workspace/parametric/`. Choose it once per episode; use three demonstrations and
one query; execute distinct Racket programs and require every pair to distinguish
the other setting.

**Why.** Sort direction changes the transformation itself, is easy to state, and
can be held fixed across an episode. Parameters such as background color, frame
presence or canvas size change inputs rather than the underlying rule.

**Rejected alternatives.** A continuous weighting or tie-breaking parameter would
need a larger semantic design and examples with ties. Making descending production
behavior in this repair would alter canonical authority and conflate a prototype
with a defect fix.

## D6 — leave canonical Racket authority and audit targets unchanged

No Racket source, normalized rule hash, catalog approval or training flag changed.
The selected rule copies already have execution parity. The two assigned audit
targets were run through findings-only checks and custom probes; no source fixes
were made because the assignment requests audit evidence, not cross-task repair.

## D7 — evidence retention

The initial blind stub, baseline ambiguity probe, failing scalar tests,
intermediate 11/12 batteries and the interrupted source-bound run are retained.
The decisive reports use separate final paths rather than overwriting failures.
Large disposable copied runtimes and caches are not intended for the return ZIP;
source-bound summaries, logs and exact reproducer files are sufficient for replay.

# Review — `review-5b3cadd507110b61`

Both assigned public-evaluation parents now have complete, source-bound reviewer prototypes.
The default program in each adapter is byte-identical to its root `reference.rkt`.
Every supplied training label and provided test gold was reproduced through protected Racket.
Both families provide matched inputs, 2–6 demonstrations, four distinct stored queries, private presentation order, and masked one-query public views.
Both include a genuine input-dependent A→intermediate→B alternate setting and a protected-Racket counterfactual replay.
No production catalog, canonical authority, approval, shared runtime, or immutable parent record was changed.
Reviewer work is complete; owner registration, native qualification, acceptance, and training admission remain pending.
The final code review was a read-only author self-review because no independent reviewer agent was available.

## `public_eval_b99e7126`

### Result

Implemented periodic macro-pattern completion. A modal separator lattice contains a repeated ordinary 3×3 tile and an anomalous tile introducing one ink color. The anomalous tile’s ink mask encodes the macro positions where the complete anomalous tile must be copied.

Settings:

- `all_ink` — exact canonical rule and default.
- `largest_component` — segment the input-derived ink mask and retain its unique largest four-connected component before macro completion.

The first two demonstrations distinguish the intended rules from clue-only, bounding-box, rotated, transposed, smallest-component, and related executable rivals. The stress query is a real 29×29 lattice with 441 foreground cells spanning 21 active rows and columns.

### Evidence

- Focused copied-runtime tests: **22/22 passed**.
- Protected authoring preflight: **passed**; all supplied labels and test gold executed correctly.
- Bounded audit: **64 episodes**, **640 visible pairs**, **576 prefix checks**, **1,920 declared-rival checks**, **128 cross-setting query disagreements**, **256 public-view checks**, and **80 protected-Racket evaluations**.
- Saved public exports: **16**, each named by the SHA-256 of its exact visible bytes.
- Sequential witness: replacing the selected largest component with the complete ink mask changes **6 final cells** on an exact preflight query; independent protected replay passed.
- Canonical Racket SHA-256: `1f7feec2b03082cc0a6996f9d7d13959ae12634bea6e81e971a1a7cf199e1262`.
- Alternate Racket SHA-256: `0079523d26014bdb780f167ebf6b5d54a5911f024aa9eeb92f13b49c5dccec08`.

## `public_eval_a6f40cea`

### Result

Implemented amodal completion of rectangular wires hidden behind the largest four-connected green rectangular occluder. The rule recovers monochrome or checkerboard wire geometry from the visible perimeter and reconstructs hidden boundary cells inside the green window.

The immutable third training output contains a phase exception for one wide 8/9 striped frame. The canonical implementation records the narrow general extension needed to reproduce every immutable label: wide striped frames flip hidden checkerboard phase, while tall or square striped frames preserve it. This is documented as an extension consistent with the supplied labels, not as a claim that the examples uniquely determine all unseen conventions.

Settings:

- `all_frames` — exact canonical rule and default.
- `largest_frame` — recover the same wire records but render only the unique largest-area frame.

### Evidence

- Focused copied-runtime tests: **23/23 passed**.
- Protected authoring preflight: **passed**; all supplied labels and test gold executed correctly.
- Bounded audit: **36 episodes**, **360 visible pairs**, **324 prefix checks**, **1,620 declared-rival checks**, **72 cross-setting query disagreements**, **144 public-view checks**, and **60 protected-Racket evaluations**.
- Stress inputs are genuine 30×30 scenes; the retained sample spans 28 columns and 22 rows with 454 foreground cells.
- Saved public exports: **16**, each hash-named and independently masked.
- Sequential witness: replacing the unique largest recovered frame with all recovered frames changes **64 final cells** on an exact preflight query; independent protected replay passed.
- Canonical Racket SHA-256: `ca819adf152ff666d3f62fa369ef61401f406355a6edaa61c422f0a9cf576cc8`.
- Alternate Racket SHA-256: `a4bb2c42ef30ab0f19a3ab789694eff97298ff3c452edd4c432ce963bdc9aa47`.

## Defects found and repaired

1. The b99 sampler cached immutable tuple snapshots, while its grid validator accepted only mutable lists. A focused failing test exposed the mismatch; validation now accepts either representation without weakening integer/grid checks.
2. The a6 bounded sampler treated a lawful rejected scene candidate as fatal during later demonstration/query search. A focused failing test exposed the control-flow defect; bounded search now skips rejected candidates consistently.
3. Protected execution of the a6 parent exposed the immutable wide-striped phase exception. The reference and generator now document and exercise the minimal orientation-dependent extension rather than using a grid lookup.

## Limits and owner handoff

The rival audits are finite and demonstrate rejection only for the declared executable alternatives over the recorded seeds. They are not proofs of unique induction over every conceivable rule. The a6 final audit uses 18 seeds because protected evaluation is materially heavier; its exact seed list and limits are retained in `checks/public_eval_a6f40cea/audit/audit.json`.

Both rows are reviewer-reported `ready`, not accepted. The owner must reconcile any overlapping source, register exact provenance, run unchanged native qualification and causal replay, explicitly accept both current source closures, and separately decide training admission.

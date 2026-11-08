# Working notes: f1668de79fa1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-04: version 2.0.0 repair

The selected 1.4.0 baseline was inspected directly. No prior return was used as
a repair lead; the associated-notes file was empty. Its SHA-256 was
`2b6235190f40456c2aceb2c6cda90686702476dba2e19e537ebb36c1543b09c1`.
The before battery failed lint, selfcheck, defect lint, profile floor, and
override checks. The canonical vertically symmetric C template was rejected,
and the exact canonical-profile census had zero hits out of 60 draws.

### Canonical validity

The validator now accepts symmetric templates and partially clipped stamps.
Vertical symmetry does not make horizontal and vertical reflection equivalent:
the canonical C shape is vertically symmetric but changes under horizontal
reflection. Ambiguity belongs to the lesson, not the single-input validator.
Validation now checks rectangular rows, integer role colors, exactly one
marker, one connected template, a 4..9-cell source, and a nonempty visible stamp.
The size and nonempty-output restrictions are explicit sampler choices, not
claims that the Racket rule is undefined outside this domain.

### Honest controls and constructive placement

The old palette/texture/density names either had no effect or only one lawful
value. They are removed rather than presented as tunable controls. Literal
role colors follow the unchanged rule. Dimensions, cell count, and clipping
mode are exact, validated, and recoverable from pixels. All declared joint
combinations are supported. Connected shapes grow on a finite frontier and
placement chooses among complete legal candidate sets, preserving exact counts.
Fallbacks are bounded constructive shapes, not shortened or relabeled outputs.

### Curriculum and measured rivals

The three scheduled profiles are:

1. Core: favors canonical heights 8/9 and widths 13/14 while retaining the
   entire advertised dimension support; arbitrary connected source shapes.
2. Wide: full stamps, at least four template columns, asymmetric interior
   occupancy, all eight D4 transforms distinct, and a true interior source cell.
3. Clipped: at least one source cell survives and at least one falls outside.

Default wide counts are 7..9. Exact counts 4..6 remain supported and may remove
the interior/width teaching witness. Exact clipping-mode overrides may also
remove default lesson witnesses; the production evidence concerns no overrides.
Five demonstrations plus one query give two of each profile in any six
consecutive raw indices. Production duplicates or validation rejections can
change accepted indices, so source-bound production-census evidence is required.

Twelve executable rivals are declared. Three fit every usable canonical pair:
swap only edge columns, shift the destination inward to fit, and mirror only
the template boundary. The baseline seed=1000, easy, start=18 lesson is an
actual teaching counterexample: edge swapping fits demonstration indices
18..21 and fails query 22. The return retains full Racket-labeled evidence.

The rival hooks are authoring diagnostics; only Racket supplies production
labels. A successful finite census establishes coverage against the declared
family, not universal uniqueness over arbitrary programs.

### Continuation

Run the public battery and explicit task-test stage after changing generator
bytes. Use the shared production lesson census with rotations, then the local
cyclic-window probe for exact period coverage. Re-prepare solve episodes after
any generator edit. Preserve source hashes, prior failures, and actual accepted
indices when comparing versions.

### Version 2.0.1: collision merge of review-5f5dffd562b3002e

The accepted 2.0.0 source was
`c76ac07f8667c505af3bdce8de91a140acaba5154bd748e85e7a1d0f2df9e8b7`.
The incoming review independently repaired the same 1.4.0 baseline
`2b6235190f40456c2aceb2c6cda90686702476dba2e19e537ebb36c1543b09c1`,
producing source
`6d932ed0269eb78d33b8c445868e1437e3a8b31d8fd81adc3eed659e57cb0386`.
This maintainer merge retains the accepted lawful domain, exact controls,
clipping, symmetric shapes, wide/interior witnesses and all twelve earlier
rivals. It adds the incoming `rotate_five_else_flip_lr` shortcut to the rival
and canonical-shortcut maps. The new witness additionally requires a full
stamp, so clipping cannot erase its contrast.

Uncontrolled core draws now have five cells and are vertically asymmetric.
Finite-frontier growth still has 128 bounded attempts, followed by the checked
constructive fallback; the incoming random-walk sampler was not adopted.
The three-profile schedule gives two core witnesses in six consecutive raw
pairs, leaving one under every single-query rotation. Explicit controls retain
their exact values and can disable these default teaching guarantees.

Merged generator version: `2.0.1`; SHA-256:
`6567f4bc49395defbfc4190dec4ac1e547b69401a80d4f515c88ed39616f2b54`. Verification:
`PYTHONPATH=shared/runtime python3 -m pytest -q generators/f1668de79fa1/tests`
passed **205/205** in 1.28 seconds. The new teaching test covers 36 raw windows
(three cyclic starts, three seeds, four bands) and all 216 query rotations;
existing canonical shortcut checks cover the added rival. Focused tests also
cover an independently specified rival disagreement, clipped-witness exclusion,
explicit core controls and the deterministic bounded-growth fallback.

The incoming reported 12/12 battery and source-bound solve captures apply only
to its original candidate bytes. This merge has focused task-test verification;
no full battery, production lesson census, private solve replay or fresh solve
was run. Original solve/program provenance remains unchanged. The machine
receipt is `evidence/maintainer-merge-review-5f5dffd562b3002e.json`.

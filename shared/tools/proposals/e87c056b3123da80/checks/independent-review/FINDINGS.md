# Independent review: af840d59f24c baseline

Examined selected source SHA-256
`08d52d130454fad7f5911f32affa1ed215c3666c2f7e99e2d3d6715e3514e8a4`,
rule `dbb5a0b9e901`. Source was loaded with
`reviewer_support.load_selected_generator(..., root=ROOT)`. The exact selected
bytes are retained as `baseline_generator.py`. No generator/reference/runtime
source or assignment was edited by this review.

## Executed evidence

From `/workspace/scratch/b8474c8b9c17/arc_review`:

```sh
python3 review.py run python3 ../checks/independent-review/probe.py > WORK/checks/independent-review/probe.stdout.txt 2> WORK/checks/independent-review/probe.stderr.txt
```

Exit status: **0**. The script deliberately refuses a different selected source
hash so its baseline evidence cannot silently be rebound to later edits.
`baseline_report.json` records each exact seed/index/band/profile, input hash,
actual authoritative output for counterexamples, and every disagreement cell.
The existing `workspace/reference_probe.py` batched 63 inputs through the actual
canonical Racket program in a relocated runtime. All four canonical labels and
all 48 sampled generated labels agree with Racket. No blind or private solve
files were inspected; no full battery or historical return census was run.

## Ranked findings

### 1. Fixed row and frequency templates encode rank across the generated support

Both independent rivals in `probe.py` match **48/48 generated grids**, sampled
with seeds `0, 17, 99173`, every difficulty `None/easy/medium/hard`, and every
explicit profile. Both match **0/4 canonical pairs**. These are distribution
shortcuts, not incorrect authoritative labels.

The first-seen rival assigns ranks using the fixed sparse sequence
`[n,1,n-1,2,...]`, or the dense middle-column-then-reversed sequence. It never
sorts columns horizontally. Starting with `generate(0,0)`, swap rows 0 and 1.
`self_check`, `strict_canonical_like`, and `observe_overrides` still accept the
same `canonical_sparse` profile, but the rival disagrees with Racket at three
cells. Racket produces exactly the corresponding row permutation of the base
output. The full same-profile witness is in
`baseline_report.json/witnesses/swap_rows_0_and_1`.

The frequency rival reads the fixed per-profile frequency signature and uses
horizontal ordering only to resolve equal-count ties. For four-column sparse
grids, counts `(2,4,3,1)` uniquely encode ranks `(1,2,3,4)`; dense counts
`(3,5,2,height,4,6)` uniquely encode every rank. Swapping occupied columns 2 and 3
of the same `generate(0,0)` input preserves all validators and profile identity
but makes this rival disagree at six cells. This witness is in
`baseline_report.json/witnesses/swap_first_two_zero_columns`.

Row shuffling alone cannot change frequency signatures. Minimal repair needs
independent variability in row placement and in the assignment of count vectors
to horizontal ranks, while retaining rejection gates for the meaningful
row-local, ordinary-first-seen, and ordinary-frequency competitors.

### 2. A canonical-fitting nonzero-preservation rival survives allowed rotations

`erase_nonmodal` applies the correct zero-column ranking but replaces every
nonzero cell with the modal nonzero color. It fits **all four canonical pairs**.
It fits every homogeneous generated profile and fails dense mixed-color inputs
at the six decoy cells.

Exact minimal lesson: seed 0, demonstration indices `[0,1,3,4]`, query index `2`.
The declared hook returns `lesson_identifiable(...) == []`, but this rival fits
all demonstrations and changes six query cells against Racket. The full lesson
is retained under `baseline_report.json/rotation_witness`.

Checking all five held-out positions for starts `0,1,2,3` gives **3/20 ambiguous
rotations**: `(start, held_out_offset) = (0,2), (1,1), (3,3)`. This does not refute
the previous narrow claim about the six declared rivals; it reveals a missing,
plausible preservation competitor. The proposed five-profile schedule containing
two dense examples ensures that every five-pair window leaves a dense example
after any one holdout. This is a repair rationale, not post-edit verification.

### 3. The selected source has no strict seed/index call contract

The selected generator accepts seeds `True`, `1.0`, `"1"`, and `None`; it accepts
sample indices `True`, `1.0`, `1.9`, `"1"`, and `-1`. Exact accepted calls and
result hashes are in `baseline_report.json/invalid_scalars`. In particular,
`generate(0,1.9)` schedules the `wide_many` profile by truncating through `int()`
while retaining `1.9` in the randomness key. The retained AST-only scalar
proposal is explicitly unselected and does not establish runtime behavior for
these selected bytes. This independently agrees with the root review's reported
defect-lint finding.

### 4. Validation and the prose domain are wider/narrower in different places

Appending seven background columns to the baseline yields a 10x17 grid;
appending 21 zero-free background rows yields 31x10. Both return `[]` from
`self_check` and `strict_canonical_like`, while `observe_overrides` rejects them
as outside every declared profile. These are direct API observations, not a
Racket mismatch claim. They show that the notes' width-through-16 domain limit
is not a validator constraint. The root review can either narrow that claim or
enforce its intended geometry limit. This has lower priority than actual
generated-distribution and lesson failures.

## Cheap additional Qwen admission gate supported by this evidence

For a candidate solver/trajectory that fits the visible lesson, retain two
controller-only counterfactual query checks with authoritative labels: one
nontrivial row permutation and one reassignment of zero-column count patterns
to horizontal positions, both within the reviewed profile and validator domain.
The concrete three-cell and six-cell witnesses above distinguish the intended
rule from rivals that score 48/48 on ordinary sampled data. Do not admit a
trajectory solely because its original query answer or generator parity passes.

At lesson assembly, also check every permitted query rotation against the
canonical-fitting `erase_nonmodal` competitor. This is cheap finite enumeration:
the baseline uses four starts times five holdouts. Keep the admission labels and
reference program out of the actor-visible challenge. This is a narrow additional
gate grounded in observed failures; it is not a proof against arbitrary rivals.

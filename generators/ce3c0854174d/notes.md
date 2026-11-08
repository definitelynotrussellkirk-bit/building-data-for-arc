# Current decisions: ce3c0854174d

## Rule and supported inputs

Version 3.0.0 retains Racket rule 442270b293a4. Codes 1, 2, 3, and 4 mean
clockwise quarter-turn, half-turn, left-right reflection, and transpose.
Apply them to the previous cropped state; emit the successive states, top-aligned,
with one blank column between frames. The initial state is not an extra frame.
This sampler uses a contiguous left-anchored script, a blank separator row,
and one four-connected monochrome body in color 5..9. Racket's extra codes 5..7
are intentionally outside this sampler's vocabulary.

## Reversals and evidence

- The old identity/rotation-only SUMMARY legend was wrong. Both summaries now
  match the unchanged rule. Four literal rectangular-operation tests and all
  four canonical labels check the executable Python diagnostic.
- Advertised height 7..12, width 10..16, and script length 2..5 now work exactly,
  including all joint combinations and every difficulty. Unknown keys and
  noninteger overrides fail. Keyed draw provenance and pixel observations agree.
  The inherited final override check accepts 10,260/10,260 cases with no finding.
- A blank or disconnected body, script holes, misplaced codes, multiple body
  colors, and invalid color types are rejected. Canonical inputs remain accepted.
  Template placement may reach canvas edges and may lie left of the script;
  the old right-side placement restriction was not required by the rule.
- Independent random scripts did not always teach the legend. The retained
  baseline seed-1 lesson lets code 4 mean anti-transpose while fitting all
  demonstrations and changing the query. All four labels were replayed through
  Racket. See counterexamples/ambiguous_timeline_seed1.json.

## Curriculum and its limits

Even sample indices use a shape with eight distinct D4 orientations and a
default script containing every code. Odd indices retain a canonical size/palette
profile and allow symmetric as well as asymmetric shapes. Three consecutive
default demonstrations contain a full-legend witness. Four consecutive labelled
pairs contain two witnesses, so removing any one pair leaves a full witness.
Order within each script, template orientation, color, and position are randomized.

All original shapes remain in the broad component, with two additional
rectangular shapes. This avoids a global asymmetry filter that would exclude
canonical symmetric cases. The finite shape bank and 50/50 schedule are deliberate
choices, not empirically optimized weights or a claim of complete shape coverage.
Difficulty changes broad dimensions and script length; this does not establish
measured model difficulty.

The 30 declared rivals are all 28 single-code substitutions among eight D4
operations, independent rather than cumulative transforms, and the former
incorrect summary legend. No rival in that list fits all four canonical pairs,
so no CANONICAL_SHORTCUTS claim is made. The lesson hook checks supplied labels;
it does not approve training trajectories.

Final evidence is bound to generator SHA-256
42da7ef9b8d1112303ad4a1645bf5c4b6f87148f724fee63bc78ee5f93a9d5d8.
All 12 after-battery stages pass, including required rotations.
The census uses three demonstrations and one query: 100 pinned lessons per band,
300 total, 1,200 unique inputs, zero production ambiguities and zero ambiguities
in 1,200 single-query rotations. These rotations reuse the same labelled pairs.
The standalone probe additionally predicts every one of those held-out answers
from demonstrations alone within its stated D4 family.

Pinning script_len to 2 or 3 removes the full-legend witness guarantee. The exact
input control still works, but custom lesson assembly must check identifiability;
it must not inherit the default census verdict. Fewer demonstrations, other
hypothesis families, and downstream Qwen training gains remain unmeasured.

## Current audit status and next actions

Prior lead review-0867d19380f40c97:v0001 (baseline
d11a828e9bf06a2cb6089cba2e0c8d101c00454c6e820db5ccab90546323a447)
reported the wrong legend and rejected advertised endpoints. This repair
reproduces and addresses both. The protected evidence/review_index.json remains
unchanged; the maintainer must explicitly resolve that finding after selecting
this repair. Generic acceptance must not silently clear unrelated audits.

Use workspace/transform_legend_probe.py for a new visible challenge and
workspace/validate_legend_probe.py for an existing Racket census. The return's
RESULTS.json contains exact commands, failed iterations, environment recovery,
and fresh-packet replay receipts. The two drawn audit targets were not edited.
## Current reviewer considerations

Source SHA-256: `42da7ef9b8d1112303ad4a1645bf5c4b6f87148f724fee63bc78ee5f93a9d5d8`.

# Decisions for ce3c0854174d

## M1: retain the rule and correct its explanation

The Racket implementation and canonical labels agree. The old summary's
identity/rotation mapping did not describe that implementation. I corrected both
summaries and pinned RULE_HASH `442270b293a4`; no reference rule or canonical data
changed. Four hand-computed, nonsquare operation examples and all four canonical
pairs check the Python diagnostic. Python is used for rival analysis, never as
the replacement label authority.

## M2: honor controls, validate the actual supported domain

The prior axis declaration promised height 7–12, width 10–16 and script length
2–5, but generation drew from narrower per-call ranges. The original reason for
that mismatch is unknown. I retained the advertised domains and made every
joint combination possible in every difficulty. Shrinking the public declaration
would have discarded useful variation and hidden the existing contract defect.

Unknown keys, Boolean/fractional/string integer controls and out-of-range values
now fail explicitly. Every returned axis is both recorded through the keyed draw
API and observable from pixels. The intermediate repair omitted keyed provenance
for default draws; `checks/provenance-before.log` captures that regression and
the final test exercises the real GenCtx record, not a copied implementation.

The validator now requires integer ARC colors, rectangular rows, a left-anchored
contiguous 2–5-code script, blank separator row, and one nonempty, four-connected,
single-color body in colors 5–9. It rejects script holes, misplaced codes,
disconnected/multicolor bodies and invalid types. The restriction that the body
must lie to the right of the script was removed: the unchanged rule crops the
body and does not need that placement cue. Canvas edges are allowed when the
shape fits. The four canonical inputs remain accepted.

The broader Racket interpreter accepts codes 5–7 as well. This repair keeps the
existing 1–4 sampler vocabulary; adding another control vocabulary would be a
separate distribution change requiring new teaching evidence.

## M3: teach the meanings without excluding symmetric cases

Independent random scripts could give correct labels while leaving a control's
meaning unresolved. On the archived baseline, seed 1 with three demos at indices
0–2 and query index 3 lets code 4 mean anti-transpose while fitting every demo.
The saved witness and all four labels were independently replayed through Racket.
An exploratory Python-only sweep of seeds 0–99 found ambiguity in 48/100 lessons
in each band. The old bands were identical; these are the same 100 lessons under
three labels, not 300 independent Racket-labelled observations.

I chose a period-2 schedule. Even indices use a shape with eight distinct D4
orientations and a shuffled script containing all four codes. Odd indices keep
a canonical size/palette profile and permit symmetric shapes. Any three
consecutive default demos contain a full witness. Any four consecutive labelled
pairs contain two witnesses, so any one-pair holdout leaves a witness. Default
scripts vary with difficulty; explicitly setting script_len to 2 or 3 is lawful
input generation but removes this guarantee.

A global asymmetry filter was rejected because it would exclude useful canonical
symmetries. Pure random sampling plus an unsupported assumption of enough demos
was rejected because of the saved counterexample. A permanent five-demo minimum
was unnecessary for this timeline format: a single asymmetric cumulative gallery
can reveal every code, and the interleaving protects the requested three-demo
production lessons and four-pair rotations.

All original shapes remain available in the broad component; two nonsquare
templates were added. The bank still has only seven templates. D4 orientation,
script order, body color and placement vary. Difficulty changes broad dimensions
and script lengths; it is not calibrated by model performance. The 50/50 witness
mixture is a simple sufficient schedule, not a measured optimum.

## Hypotheses and validation scope

There are 28 single-code substitutions among eight D4 operations, plus an
independent-transform rival and the old summary's legend: 30 distinct rivals.
The census reports them in both SEMANTIC_RIVALS and LESSON_COMPETITORS, hence
60 named entries. None fits every canonical pair, so this repair does not claim
any CANONICAL_SHORTCUTS witness. The lesson hook consumes materialized labels.

The final census contains 100 lessons per band, start indices 0–99, three demos
and one query, with retained deterministic seed recipes and 1,200 unique inputs.
Production: 300 checked, zero ambiguities. Rotation: 1,200 holdouts checked,
zero ambiguities. Each band contains both start residues, 50 times each. A
separate fixed-seed check in `checks/schedule/` examines both cyclic starts in
each band and all query positions; its result is reported in RESULTS.json.

The standalone transform_legend_probe further searches combinations of control
meanings consistent with the visible demonstrations. It accepts a nonunique
legend if every surviving mapping predicts the same query output. Its grammar
is specific to cumulative, top-aligned transform galleries; applying that parser
to other ARC families would be an invalid use. Budget exhaustion is incomplete,
not success. All 300 production and 1,200 rotation predictions on the final
census agree with Racket labels. Eight focused probe tests include ambiguity,
symmetry, ignored query labels, inconsistency and incomplete search.

Predictable witness positions are a restriction, but the rotated lessons do not
need the held-out example to occupy a special slot. The finite template bank,
short-script overrides, other hypothesis families, fewer demonstrations and
downstream Qwen3.5-9B training gains remain unmeasured.

## Shared tools, dependencies and extraction

The delta adds two standard-library transform probes and a bounded pytest runner
under the selected task's workspace. The runner uses pytest from its interpreter,
retains per-file JUnit/logs and checkpoints, and deletes only its own completed
temporary directory. It cannot cure a shared executor with no free filesystem
entries; the interrupted run is retained rather than called a pass. No global
runtime or common-tool source is patched by this return.

The environment's initial pytest installation was only in user-site, while task
test subprocesses disable user-site. An independent venv installed pytest 9.1.1
from locally repacked dependency wheels; NumPy 2.3.5 and Pillow 12.3.0 are ordinary
system dependencies. The fresh replay has its own venv and its own unpacked
Racket runtime. Installed environments and executables are not in the delta ZIP.

The fresh packet was verified against every original ZIP member. To avoid
duplicating hundreds of megabytes, byte-identical immutable files use hard links;
the selected editable generator subtree is privately copied. There are no
symlinks, predecessor import paths or borrowed environments. The materialization
receipt and fresh-patch test receipt disclose the exact layout and hashes.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0867d19380f40c97:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d11a828e9bf06a2cb6089cba2e0c8d101c00454c6e820db5ccab90546323a447`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused repair-bound closure of the old d11a828e9bf06a2cb6089cba2e0c8d101c00454c6e820db5ccab90546323a447 legend and rejected-exact-boundary findings against current42da7ef9b8d1112303ad4a1645bf5c4b6f87148f724fee63bc78ee5f93a9d5d8. Owner static inspection confirms SUMMARY now maps1 clockwise quarter-turn,2 half-turn,3 LR reflection, 4 transpose, and _draw_axis validates explicit height7..12,width10..16,script_len2..5 independently of default/difficulty draws. New reviewer current-source Racket audit separately executes [1,1], [2,2],[3,3],[4,4] expected galleries, all four canonical pairs, and joint endpoint cases including (7,10,2),(7,16,5),(12,10,5),(12,16,2), with exact pixel measurements. These directly exercise the prior wrong legend and rejected boundaries. Retained bounded-audit-af8033c6ab6dbbfd evidence is reviewer-reported execution plus owner static source inspection, not a new owner runtime run. This is targeted closure, not automatic clearing from source edits or a generic clean sample; finite templates/vocabulary and short-script teaching limits remain.

### Assessment or prior finding

## ce3c0854174d

**A1 — Reproduced documentation and override-contract defects, not an alleged
Racket-label defect.** Generator version 2.0.1, SHA-256
`d11a828e9bf06a2cb6089cba2e0c8d101c00454c6e820db5ccab90546323a447`;
executed canonical rule hash `442270b293a4`.

The generator's SUMMARY describes the transform legend as 1 identity, 2
clockwise quarter-turn, 3 half-turn, and 4 counterclockwise (with tentative
wording). Canonical Racket instead interprets those codes as clockwise
quarter-turn, half-turn, horizontal reflection and transpose, respectively,
with cumulative composition and a packed gallery. This is a material mapping
contradiction, not a difference in descriptive style.

The retained input is an **actual ordinary generated** draw: seed 4, sample
index 0, easy, no overrides, script [1,1,3]. It passes `self_check` and is within
the documented generator domain. Applying the SUMMARY's alternative mapping
to its template produces a gallery differing from actual Racket at **12 cells**.
`checks/audit/ce3c0854174d/input.json`, `rival.json`, `racket.json` and
`comparison.json` retain the exact input and both outputs; `metadata.json`
records generation provenance. This does not show that the actual generator's
Racket-supplied labels are wrong; it shows that its explanation teaches a wrong
legend. F2 proposes an executable metadata witness.

Three legal advertised boundaries also reject reproducibly at seed 0/index
0 with difficulty omitted: `height=7` rejects against implementation range [8,10], `width=10`
against [11,14], and `script_len=2` against [3,4]. Exact exception texts and the
replay script are retained. These are actual override failures rather than
hypothesized distribution gaps. They are separate from the transform mapping.

Reproduce the saved actual Racket result from packet root:

```sh
python3 run_with_racket.py python3 -m arcpuzzles apply ce3c0854174d --input ../checks/audit/ce3c0854174d/input.json --out ../checks/audit/ce3c0854174d/racket-new.json
```

The wrapper's payload cwd is `repo`; the retained apply report records that
actual absolute cwd, rule text hash, input/output hashes and generator hash.
`checks/audit/build_evidence.py` reconstructs the input/rival and rejected
boundary probes. No population-level error frequency or universal uniqueness
claim is made from this one counterexample.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-0867d19380f40c97-v0001/audit_assets.json), manifest SHA-256 `cdbc17d58467e69c24e51e7ceaf7e0fd1d3dc16dc132b3ac35b6f806123a65f1`.
<!-- arcpuzzles-current-audit-assessment:end -->

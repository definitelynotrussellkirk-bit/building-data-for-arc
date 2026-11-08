# Current notes: 8d7d1364cf11

## Intended rule and authority

The selected canonical Racket rule remains unchanged at normalized hash
`0a9706fafc20`. On background 4 it treats multicolor 8-connected components
larger than one cell as source templates and singleton components as dots. A dot
whose color occurs in a source chooses that template and aligns the matching
source cell to the dot; the whole template is stamped onto a fresh all-4 output.
A dot whose color is absent from every source vanishes.

The production sampler intentionally uses a unique-anchor subdomain: every
productive dot color occurs in exactly one source cell globally. It does not
claim to teach the canonical program's traversal-order tie break for duplicate
same-color anchors.

## Production grammar

Version `3.0.0` constructively emits two or three separated multicolor source
templates, one or two productive dots per source, and one to three absent-color
decoys on 16–24 cell canvases. Six recoverable shape-family schedules, independent
dihedral orientations, moving placements, shared or distinct body colors, and a
canonical-core/broad curriculum vary nuisance structure while preserving the
rule. The exact observable controls are `grid_h`, `grid_w`, `n_shapes`,
`copies_per_shape`, `n_decoy_dots`, `shape_variant`, and `shared_body`.

## 2026-10-19 call-contract repair

The fresh before battery found one concrete defect: `generate()` accepted 45
invalid public scalars across `seed`, `sample_index`, and `difficulty`. The root
cause was a missing validation boundary; exact override validation already
worked. The repair adds one shared fail-closed validator used by `generate()` and
`schedule_profile()`:

- `seed` must have exact type `int` (booleans and numeric/string coercions reject),
- `sample_index` must have exact type `int` and be nonnegative,
- `difficulty` must be `None`, `easy`, `medium`, or `hard`.

The generator version was deliberately not changed because valid generation and
its RNG schedule are unchanged. A source-to-source equivalence probe compared
128 valid calls spanning all four difficulty values and exact overrides: 128/128
outputs were byte-identical to the approved baseline. Fifteen focused regression
cases first failed on the baseline and then passed after the repair. Evidence:
`checks/before/`, `checks/tdd-red/`, `checks/tdd-green/`, and
`checks/contract-equivalence/report.json`.

## Proposed parametric extension

`workspace/parametric/` contains a task-local **prototype**, not a production API
or approval change. Two bounded parameters are selected once per episode:

- `anchor_mode`: canonical `matching_cell` or proposed `template_origin`;
- `canvas_mode`: canonical `clear` or proposed `preserve_input`.

The four exact Racket programs preserve the same source/dot/template reasoning.
Episode construction retains inputs where all four outputs are distinct, so each
of three demonstrations rejects all three alternative settings before the query.
At retained seed `20261019`, 16 complete pairs were checked with 64 bundled-Racket
executions; every Racket result matched the independent Python mirror and all 12
training pairs were pairwise distinguishing. Public artifacts omit hidden
settings, programs, and query answers. Evidence:
`checks/parametric/report.json` and `workspace/parametric/materialized/`.

## Strongest canonical shortcut

All three canonical demonstrations use color 5 only as an absent-color decoy.
The executable rival `ignore_productive_color5` therefore fits 3/3 canonical
pairs. Broad profiles invert the correlation by making 5 a productive accent and
using another absent color as the decoy. The exact generated witness is
`counterexamples/color5-shortcut.json`; the selected Racket output and rival
prediction disagree on six cells.

## Current verification

- Before battery: 11/12 green; only strict-scalar defect lint failed (45 findings).
- After battery: 12/12 green, including authority sync and unchanged rule smoke.
- Portable task suite: 61/61 passed.
- Parametric prototype: 64/64 Racket/Python executions matched; 12/12 training
  pairs distinguish all four settings.
- Valid-call equivalence: 128/128 baseline/new outputs identical.
- Lesson census: 300/300 three-demonstration-plus-one-query lessons materialized
  (100 per difficulty band), with 0 production ambiguities; all 1,200 hold-each-pair-out
  query rotations also had 0 ambiguities under the required rotation policy.
- Mandatory blind solve `a55c1997c5e3`: 6/6 visible examples on final revision.
- Fresh post-repair solve: 3/3 visible demonstrations on one revision, bound to the
  final generator bytes; masked query labels remained unknown.

The current generator SHA-256 is
`45fa66a378159e73b07f50830d273b51cf303ec062481c3a3dcd4eee4e9055e0`.

## Limits and open scope

Finite declared-rival checks do not prove uniqueness against every possible
program. The production generator still excludes duplicate-anchor first-match
cases. The parametric evidence covers four declared settings at one retained
seed and remains proposed, not integrated. Historical v3 notes, the retained
color-5 counterexample, and prior evidence were used as leads; every current
acceptance claim above was remeasured against the pinned source in this packet.
## Current reviewer considerations

Source SHA-256: `45fa66a378159e73b07f50830d273b51cf303ec062481c3a3dcd4eee4e9055e0`.

# Decisions

## D1 — repair the public boundary, not the generator distribution

The before evidence isolated the defect to unvalidated call scalars. I added one shared validator and invoked it from `generate()` and `schedule_profile()`. I rejected a broader rewrite of `gen_ctx`, palette logic, schedule logic, or sampling because none was implicated by the failure and each would risk changing approved valid outputs.

## D2 — retain version `3.0.0` and the selected Racket authority

I did not bump `VERSION`. In this codebase the version participates in deterministic RNG derivation, so a bump would alter every valid sample while fixing only invalid calls. The 128-call equivalence probe confirms that retaining the version preserves the baseline distribution exactly. I also rejected a Racket change: rule smoke, canonical outputs, authority sync, and the task semantics were already green. The normalized selected rule remains `0a9706fafc20`.

## D3 — use exact fail-closed scalar semantics

`seed` and `sample_index` require `type(value) is int`, so booleans do not silently enter integer code paths. `sample_index` must be nonnegative. `difficulty` is a closed set: `None`, `easy`, `medium`, or `hard`. Coercion was rejected because it hides caller errors and was exactly what strict defect lint was designed to expose.

## D4 — keep the parametric family separate and reasoning-preserving

The selected parameters alter two meaningful decisions while retaining the original source/dot/template relation:

1. align the matching source cell to each dot versus align the template origin;
2. stamp onto a cleared canvas versus preserve the input canvas.

I rejected cosmetic parameters such as palette renaming or grid size because they do not alter the rule, and rejected replacing the transformation with unrelated object operations because that would not preserve the original reasoning family. I also rejected wiring the variants into production: the assignment asked for a runnable proposal, not a new selected authority. Each parameter is fixed once per episode, and generated demonstrations are filtered so all four settings are pairwise distinguishable.

## D5 — treat color 5 as the strongest canonical shortcut

Among declared rivals, “ignore every productive color-5 dot” is the strongest canonical-fitting shortcut because it is simple, color-local, fits all 3 canonical demonstrations, and yields a concrete different query label. The broad sampler already contains the right counterfactual: color 5 is sometimes productive while another color is the absent-source decoy. I retained that design rather than adding a second redundant mechanism. The current-source witness and exact canonical Racket output were rechecked in `checks/question/report.json`.

## D6 — require both production-order and arbitrary-query evidence

The final curriculum evidence uses 3 demonstrations plus 1 query. I ran 100 lessons per easy/medium/hard band and required every one of the four pair positions to work as the query while preserving the order of the remaining demonstrations. This supports the intended downstream flexibility more strongly than the small battery smoke test. It remains a finite declared-rival census, not universal proof.

## D7 — preserve audit independence

The two drawn peer targets were inspected and probed but not edited. `61a55c0c7ee8` has a reserved-color role collision; `022240cb671b` has one-sided border coverage. Their strict audit presets also fail because neither declares a semantic contract. These findings belong to their own future repairs and are reported only in `AUDIT.md` and `checks/audit/`.

## D8 — compress only the large exact census artifact

The complete lesson report exceeded 23 MiB. I retained it losslessly as deterministic gzip and added `checks/lesson-census.compression.json` with the original path, byte count, SHA-256, compressed hash, and restoration command. The compact companion remains directly readable. No failure evidence or counterexample was discarded.

## Prior evidence used as leads

I consulted the selected task’s existing `notes.md`, retained `color5-shortcut.json`, and historical review index only to identify hypotheses and prior artifacts. Every acceptance claim in this return—call defect, equivalence, final battery, parametric parity, current shortcut witness, lesson census, and solves—was remeasured against the pinned packet and final source.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ef60e89ef8fcf034:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `45fa66a378159e73b07f50830d273b51cf303ec062481c3a3dcd4eee4e9055e0`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/8d7d1364cf11/generator.py, unchanged SHA256 45fa66a378159e73b07f50830d273b51cf303ec062481c3a3dcd4eee4e9055e0. Explicit no_issue within documented restricted domain. Declared unique-anchor grammar:61 portable tests pass, no advertised-domain failure found. Duplicate color5 source anchors expose first-match vs last-match at3 cells under actualRacket, but self_check rejects multiple source-cell anchors; current notes already acknowledge unique-anchor restriction. These are rejected-domain canonical-semantics diagnostics, not accepted-input/production defects. Do not infer universal coverage or approval from this disposition. Source-bound question retained in generators/8d7d1364cf11/evidence/bounded-domain-ef60e89ef8fcf034/manifest.json. Quoted basenames mean these exact target-local paths: `checks/audit/8d7d1364cf11-task-tests/RUNTIME_MANIFEST.json` `checks/audit/8d7d1364cf11-task-tests/checks/task_tests.xml` `checks/audit/8d7d1364cf11-task-tests/progress.log` `checks/audit/8d7d1364cf11-task-tests/result.json` `checks/audit/8d7d1364cf11/duplicate-anchor-witness.json` `checks/audit/8d7d1364cf11/duplicate_anchor_probe.py`

### Assessment or prior finding

## 8d7d1364cf11

**Domain question / coverage restriction — duplicate-anchor tie breaking is not
taught.** The 61 portable task tests pass, and I found no failure on the
advertised unique-anchor grammar. However, the canonical Racket program flattens
all source cells and takes the first color match when multiple source cells share
a dot's color. Production explicitly rejects that case, so a solver trained only
on generated lessons need not learn the canonical first-match behavior.

`checks/audit/8d7d1364cf11/duplicate-anchor-witness.json` contains an exact
10×12 input with two 2×2 source templates that both use accent color 5, one
color-5 dot, and one absent-color decoy. The selected Racket authority matches a
row-major first-match mirror and differs from a last-match rival at three cells:
`(5,4)`, `(5,5)`, and `(6,4)` (authority color 2 versus rival color 3). The
current `self_check` rejects the input with the expected “multiple source-cell
anchors” diagnostic.

This is not a reproduced runtime defect; it is a deliberate subdomain boundary
already acknowledged in the task notes. A future maintainer should decide
whether canonical tie-break coverage matters enough to add a controlled
duplicate-anchor lesson branch. No audited source was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

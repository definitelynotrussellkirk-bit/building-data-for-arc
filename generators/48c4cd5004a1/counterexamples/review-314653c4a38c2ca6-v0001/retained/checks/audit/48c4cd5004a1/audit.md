## 48c4cd5004a1

**Finding-only audit: reproduced teaching gaps and ignored public controls.**
The assigned target and its rule were left unchanged. Selected source SHA-256:
`1e5ce5de6a78eeac2e88074188db482a0671f2de4433e96d67bd60c29130343f`.
The public Racket receipt binds all 54 executions to that source and canonical
rule hash `113befc8d552`. No reference-label disagreement was found among the
48 generated inputs, four labeled canonical pairs, and two counterfactuals.
The findings concern what the generator teaches and what its public controls
promise, not an incorrect authoritative transformation.

### A48-1 — Vote counting is unnecessary on the sampled production support

The canonical rule detects 3×3 ring/center icons and checkerboard decoys,
excludes both kinds of block when counting dots, selects the most frequent dot
color, then returns the icon touched by that color. The generator places the
majority dots around the answer icon and places every minority dot at least two
cells away from every occupied cell. In the bounded census of **48 inputs**
(easy/medium/hard × seeds 0–3 × sample indices 0–3), **48/48** inputs had exactly
one icon touched by any dot. All passed the target's `self_check`.

An auditor-authored rival that simply returns the first dot-touched icon,
without counting colors, matched **48/48 actual Racket outputs**. It fits only
2/4 canonical pairs, so this rival is explicitly a production-support shortcut,
not a canonical-compatible hypothesis.

**Reproduced counterfactual.** Start from `generate(0, 0, difficulty="easy")`,
a 14×14 input. Change zero-based cell `(1, 9)` from 0 to 1, adding one minority
dot beside an earlier icon. The external dot counts become color 7: 4, color
3: 3, and color 1: 1. The majority is still unique and touches only the intended
icon. The input passes `self_check` and preserves the documented icon/dot and
majority-touch invariants, although it is outside the generator's current
minority-placement restriction.

The actual Racket output remains the icon with ring 5 and center 2:
`[[5,5,5],[5,2,5],[5,5,5]]`. The first-touched rival returns ring 8 and center 9:
`[[8,8,8],[8,9,8],[8,8,8]]`. Its input SHA-256 is
`1a0b2e53d7ca6fa9d467be3c074b08fa851cd64975bb044fd5d2c428d22c8ac9`.
The exact input, seed, edit, outputs and hashes are retained in
`checks/audit/48c4cd5004a1/verification.json`, counterfactual index 52, and the
public receipt `checks/audit/48c4cd5004a1/racket.json`.

**Proposed repair:** allow smaller-count dot colors to touch distractor icons
and require demonstrations to refute the no-counting rival. This makes the
intermediate majority-color calculation necessary before icon selection.

### A48-2 — No generated checkerboard evidence rejects a canonical-compatible rival

All four canonical inputs contain a checkerboard, whereas the 48 generated
inputs contain **zero checkerboards**. A second auditor-authored rival excludes
icon cells but mistakenly counts checkerboard cells as dots. It matches all
four canonical Racket outputs: the checkerboard color frequencies in those
examples do not overturn the true winning dot color. Its agreement on all
sampled generated inputs follows from their complete absence of checkerboards.

**Reproduced counterfactual.** Starting from A48-1's input, insert a 3×3
checkerboard with colors 1 and 2 at zero-based top-left `(0, 1)`. The true
external dot counts remain 7:4, 3:3, 1:1 after the decoy is excluded. The wrong
counter instead includes five extra color-1 cells, causing it to choose the
ring-8/center-9 distractor. Actual Racket still returns the ring-5/center-2 icon.
The input passes `self_check`; it is canonical-family and validator evidence,
not a claim of current generator support. Input SHA-256:
`a2ce0c3e54bfb4f96797e292e404e7a2104d28984ddf9b080ab2a3e92dd7b5fe`.
See counterfactual index 53 in
`checks/audit/48c4cd5004a1/verification.json` and
`checks/audit/48c4cd5004a1/racket.json`.

**Proposed repair:** generate checkerboards whose colors would change the
winning count if the block cells were not removed, with minority colors also
touching genuine distractor icons. This distinguishes block recognition,
dot-only voting, and the later icon selection rather than leaving the decoy
visually present but semantically irrelevant.

### A48-3 — Advertised palette controls are ignored; validator is too permissive

For seed 0, sample index 0, difficulty `medium`, both `palette_size=4` and
`n_distinct_colors=4` return the unchanged baseline input, containing **seven
foreground colors**: 1, 2, 3, 5, 6, 7, 9. The output input SHA-256 in both cases
is `44bfca5ed58fa8c1d6b8ee7b7163b38453859b0bf3d1fad74c786015081535fa`.
The other tested requests, `palette_kind="warm"`, `texture="warm"`, and an
unknown `typo_axis=123`, also return exactly the same input. The five actual
calls and observed colors are recorded in
`checks/audit/48c4cd5004a1/probe.json` under `override_checks`.

The validator also accepts `[[1,2,3]]` with no errors despite its missing
background, icons, and voting scene. This is an observed validation gap, not
evidence that ordinary generation emits such an impostor. No Racket execution
was requested for the malformed semantic scene.

**Proposed repair:** implement or remove the inactive axes, reject unknown
overrides, and validate the icon/dot/majority structure rather than only the
presence of three nonzero colors. This audit did not enumerate every override
combination and makes no exhaustive API-coverage claim.

### Scope, commands, and retained evidence

The target declares no `CANONICAL_SHORTCUTS`; both rivals above are explicitly
auditor-authored finite hypotheses. The source inspection and 48-input census
do not establish all-seed completeness or every possible shortcut. Canonical
inputs use nonzero backgrounds (8, 2, 1, and 4), while generated backgrounds are
always zero; this is an additional observed domain restriction, without a
separate counterexample or repair claim here.

All three actual verification commands ran from `WORK/` and exited 0. Exact
argument arrays and evidence paths are in
`checks/audit/48c4cd5004a1/commands.json`:

```bash
.venv/bin/python run_with_racket.py ../.venv/bin/python ../checks/audit/48c4cd5004a1/probe.py
.venv/bin/python run_with_racket.py ../.venv/bin/python -m arcpuzzles apply 48c4cd5004a1 --input ../checks/audit/48c4cd5004a1/apply-inputs.json --out ../checks/audit/48c4cd5004a1/racket.json
.venv/bin/python run_with_racket.py ../.venv/bin/python ../checks/audit/48c4cd5004a1/verify.py
```

The reusable read-only probe loads the selected module with
`load_selected_generator(TASK, root=find_root(__file__))`, checks the exact
assigned source hash, and retains every input identity. The public receipt
executes the canonical Racket rule and records actual outputs, hashes, command,
and working directory. `verify.py` checks all 54 results, canonical parity, and
both divergent witnesses against the receipt. Full evidence is approximately
265 KB before this narrative. No blanket battery or task-source modification
was performed.

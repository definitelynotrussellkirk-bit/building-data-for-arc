## 92074aefc590

**Reproduced defects; findings only.** Audited generator v3.1.1, SHA-256
`0bcd802c52cd5a30940cc0ee214f37d1804e6b4b8699a9ccd05f9d30c5f13755`.
No generator, reference-rule, shared-tool, or approval changes were made.
Canonical Racket rule hash: `987a0d5039dc`; exact program SHA-256:
`8bd762c78e1428bd0acfb317e8cc3422af8a31ee29ae3f3c97e1341fdf56358a`.
The apply receipt separately hashes its materialized callable as
`07e5cc4e9a544cf5a8f0a21f387738b9b824815aa1d24f52425a1acb1d4d112d`.

### A920-1 — default easy calls can exhaust placement (P1 correctness)

`generators/92074aefc590/generator.py:generate`, lines 112–154, samples all four
quadrants before checking their feasibility. Easy difficulty permits height 10:
top slots have five rows but bottom slots have only four, so both frames must
select the two top slots. The forty-attempt random retry still sometimes misses
that feasible choice and raises instead of returning a grid.

The retained probe examined consecutive seeds **0 through 3637 inclusive**, fixed
sample index **0**, difficulty **easy**, no overrides, stopping at the second
exception: **2 failures / 3638 generation calls**. Seeds **965** and **3637** both
raise `ValueError: could not realize frame-content layout`. These are valid
default calls, not impossible overrides. Successful unique-grid counts were not
computed; this denominator is calls. See `checks/audit/92074aefc590/probe.json`.

Suggested correction: filter slots for minimum feasible frame dimensions before
sampling K of them, or use a deterministic feasible-slot fallback. Regression:
generate both exact failing default calls and require valid returned grids.
This audit does not implement that correction.

### A920-2 — validator accepts a no-frame scene (P2 validator/domain)

`self_check`, lines 60–75, validates rectangularity and at least two nonzero
colors but does not establish any frame/content structure. The retained
`checks/audit/92074aefc590/input.json` is a 3×3 grid with one color-2 cell, one
color-5 cell and seven zeros; it has **zero frames**. `self_check` returns `[]`
without a degenerate texture exemption. Supported canonical Racket application
returns nine zeros, matching the explicitly retained `empty_canvas` rival.

This is an accepted validator counterexample **outside the documented generator
domain** of 2–3 isolated hollow frames with centered distinct-color contents. It
does not demonstrate a bad label for a normally generated scene, nor a defect in
the canonical rule. It demonstrates that validator acceptance alone cannot
certify the advertised domain. See `probe.json` and `racket.json` for input,
actual/reference output, rival output, rule/source hashes and commands.

Suggested correction: recognize and validate frame geometry, frame count,
isolated distinct borders, centered enclosed contents and advertised colors,
with explicit separate behavior for named degenerates. Regression: reject this
exact no-frame grid under ordinary validation while accepting generated scenes.

### A920-3 — declared n override has no effect (P2 axis contract)

AXES declares `n` with valid values 2–5, but `generate` never draws or consumes
that label; medium uses `n_frames` and easy/hard set K directly. At seed 0,
sample index 0, difficulty medium, `n=2` and `n=5` return byte-equivalent input
grids, both accepted by the validator; hashes and arguments are in `probe.json`.
The source inspection establishes the ignored label independently of chance.
Either implement an accurately bounded exact axis or retire this misleading
declaration. No claim is made that five frames should fit the current domain.

### Checks, exact commands and limits

Both commands run from the **outer packet directory**. The wrapper payload cwd
is `WORK/repo`; all evidence belongs to `WORK/checks/audit/92074aefc590/`.

```sh
WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python /workspace/scratch/341195387165/packet/WORK/checks/audit/92074aefc590/probe.py
WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python -m arcpuzzles apply 92074aefc590 --input ../checks/audit/92074aefc590/input.json --out ../checks/audit/92074aefc590/racket.json
```

The final runs of both commands exited **0**. The first command was repeated after Racket apply
to bind the actual Racket receipt into `probe.json`; its deterministic census
counts were unchanged. One intervening probe revision exited 1 because it
incorrectly compared the raw ledger program hash with apply's materialized
callable hash; `check-integration-failure.json` retains that tooling mistake.
The corrected probe binds normalized source hash and records both hashes.
The probe uses public `reviewer_support.find_root`,
`load_selected_generator`, and `canonical_path`, and asserts the assigned source
hash. Racket execution used the public apply command rather than a Python mirror.
No complete battery, broad generated-label census, lesson assembly census,
canonical-shortcut declaration verification, or arbitrary query-rotation check
was run for this target; those verdicts are **unknown**. These findings do not
assert lesson ambiguity or training approval. No blind/private solve material
was inspected.

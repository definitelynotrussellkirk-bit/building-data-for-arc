# Crop-and-repeat parametric prototype

This is a **prototype**, separate from canonical repairs, runtime APIs, and
approval. The default `horizontal, 2` executes the exact current canonical Racket
source. The alternatives change the executed transformation to horizontal three
copies, vertical two copies, or vertical three copies.

## Rule and episode policy

The bounded parameters are `axis ∈ {horizontal, vertical}` and
`copies ∈ {2, 3}`. A SHA-256 mapping selects the pair **once per episode seed**;
every demonstration and query uses that pair. Explicit overrides, when used by
the Python API, also apply once to the whole episode. Color/object identification,
occupied bounding-box extraction, zeros within the crop, and concatenation of
identical copies remain the same reasoning steps.

The selected generator is loaded from the current source tree using portable
`reviewer_support` helpers. Inputs are unchanged generated grids, filtered by
its self-check, distinct-input checks, and bbox sides 2..10. This common bound
makes every parameter rival's output legal within 30×30; alternative output
sizes need not remain smaller than the original canvas. Each four-pair episode
accepts 3×3, variable-bbox, 3×3, variable-bbox in that order. Rejection sampling
is capped at 512 draws and retains actual indices, hashes, and reasons. It does
not assume a generator source hash or particular pixels. If a future selected
generator cannot supply those slots within the bound, it fails explicitly.

The public challenge exposes three labeled demonstrations and one input-only
query. It contains no hidden parameters, program, query output, or private
metadata. Only the private receipt records them. Parameter alternatives are
all scored using the real included Racket bridge in a normally prepared runtime; fixed-3×3 crop shortcuts for
each setting are additional Python diagnostic rivals. Every single-pair holdout
is scored, retaining full predictions and mismatches. Having two variable-bbox
pairs ensures every rotation keeps a demonstration refuting the fixed-size
shortcut. The finite rival set does not prove unrestricted identifiability.

## Run from the extracted packet root

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python generators/b9d1d323c3ed/workspace/parametric/prototype.py --out ../checks/parametric/evidence
WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest generators/b9d1d323c3ed/tests/test_parametric_b9d1d323c3ed.py -q
```

The wrapper selects the included offline Racket and runs the payload from
`WORK/repo/`. Thus payload paths are repository-relative and output paths above
resolve to `WORK/checks/parametric/evidence`. Use a fresh output directory when
retaining evidence for another source version.

The CLI finds deterministic seeds covering all four settings, writes one
complete episode per setting, exact `.rkt` programs and SHA-256 hashes, a lawful
2×2 differing witness, canonical labeled-pair parity, source/runtime bindings,
and all query rotations. Opaque input-hash filenames under `public/` are solver challenges; files
under `private/` are authoring evidence and must not be exposed to solvers.
`private/report.json` states the bounded verdict. Command logs and exit-code
receipts are retained beside the evidence directory by the reviewer.

Focused tests cover real Racket semantics, default canonical parity, bounded
parameter validation, deterministic seed selection, episode consistency,
output limits, public projection, and all parameter/fixed-size rivals under
every query rotation. These tests are prototype coverage, not canonical repair
coverage or an admission gate. Test-first failure is retained in
`WORK/checks/parametric/red.log` (exit 1; prototype file absent).

## Portable execution detail

`prepare_runtime` and `run_process` are public authoring APIs. They provision
the selected task's ordinary execution layout before the worker calls the
public `RacketBridge` and `rule_wrap.wrap_rule`. In an already copied runtime,
the worker reuses that runtime rather than trying to construct a new Catalog.
This is necessary because a bare repository import of `wrap_rule` cannot
resolve its inherited `scripts.comment_solutions` parser dependency. The
initial failure is retained at `WORK/checks/parametric/initial-infrastructure.log`
(exit 1; six failures and one pass). No shared helper was changed.

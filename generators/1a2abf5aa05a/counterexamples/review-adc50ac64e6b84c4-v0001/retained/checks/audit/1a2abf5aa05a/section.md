## 1a2abf5aa05a

**Finding: reproducible control defects.** The source ignores its advertised
`frame_h` and `frame_w` overrides, can silently return fewer frames than an
explicit `n_frames` request, and rejects advertised `n_frames=1` in every tested
difficulty. The checked Racket labels remain correct for the actual generated
inputs. No lesson-ambiguity claim is made.

**Exact source:** generator version `2.0.1`, SHA-256
`ede7336806a39e8c5c04e667731ffcbbd2806a90bc0c5ff2c4df2ad72504bb4a`, matching the
audit draw and public application receipt. Canonical and executed rule hashes
both equal `fa427297c192`. Current notes contain only the placeholder, associated
notes are empty, and this target has no current `evidence/review_index.json`.
No target source, test, rule, or audit status was edited.

### Reproduced witnesses

1. **Both advertised frame-size controls are ignored.** At seed 0, sample index
   0, `difficulty="easy"`, `grid_h=11`, `grid_w=13`, and `n_frames=2`, three calls
   with no size override, `(frame_h, frame_w)=(3,3)`, and `(6,6)` return exactly
   the same 11x13 input. Its two frames are 4x3 and 3x4, so neither explicit
   request is respected. Both requested layouts are geometrically feasible in
   that canvas. The same three-way identity was reproduced for medium and hard
   at seed 0 with feasible larger canvases: nine draws in total. The source
   advertises these axes but obtains `fh` and `fw` directly from `rng.randint`,
   without consuming the overrides.
2. **An explicit count can silently become a smaller count.**
   `generate(1, 0, difficulty="easy", grid_h=9, grid_w=11, n_frames=3)` returns
   only two hollow frames: color 9 at bbox `[0,1,4,4]` and color 7 at
   `[2,6,7,9]`. `self_check` returns `[]`. This was the first shortfall in a
   bounded search that actually exercised seeds 0 and 1. The return condition
   `placed >= max(2, n - 1)` explicitly permits the shortfall. Three 3x3 frames
   with background gaps fit inside the requested 9x11 canvas, so the request
   itself is feasible; the sampled layout can fail to place the third frame.
3. **Advertised count bounds differ from accepted controls.** `AXES.n_frames`
   lists `1..7`, yet seed 0 with `n_frames=1` raises `ValueError` in easy, medium,
   and hard, reporting allowed ranges `[2,3]`, `[3,4]`, and `[4,6]`, respectively.
   The `single_frame` degenerate texture is a different interface and does not
   make the advertised scalar override work.

The compact input grids, exact arguments, observed bounding boxes, and Racket
results for the first two witnesses are retained in
`checks/audit/1a2abf5aa05a/minimal-witnesses.json`.

### Authoritative execution and classification

One public `Catalog.apply(reference="canonical", check_generator_domain=True)`
call executed nine inputs through actual Racket: four canonical labeled pairs,
four generated control witnesses, and one hand-made single-cell domain probe.
All nine returned valid outputs without execution errors. All four canonical
outputs and all four complete-frame geometric expectations matched exactly.
The receipt binds the selected source and verifies the executed rule hash against
the catalog. Thus these are **input/control contract defects**, not reproduced
wrong-label defects.

The separate hand-made input `[[1]]` is not a hollow frame, yet the public domain
check reports `valid`. This records the limited coverage of `self_check`; this
audit did not show the ordinary sampler emitting that input, so it is not
reported as a generated training-poison witness. No episode curriculum or rival
identifiability census was run.

### Reproduction, evidence, and proposed action

Actual command, exit status **0**, from the outer packet directory containing
`review.py`:

```bash
python3 review.py run ../.venv-review/bin/python ../checks/audit/1a2abf5aa05a/reproducer.py --out ../checks/audit/1a2abf5aa05a/run-01
```

The payload runs from `WORK/repo`. The portable reproducer resolves its source
with public `reviewer_support` helpers; it has no sibling-checkout imports. Use a
new `--out` directory on replay. Exact absolute working directories, command,
exit code, source/artifact hashes, and counts are in
`checks/audit/1a2abf5aa05a/execution-receipt.json`.

Retained evidence is `checks/audit/1a2abf5aa05a/run-01/report.json`,
`run-01/catalog-apply.json`, `run-01/generator.snapshot.py`, and `run-01.log`.
The run made nine size-control draws, two count-search draws, three rejected
one-frame requests, and nine public Racket applications; no full battery ran.

Proposed repair: consume and enforce the explicit frame dimensions; satisfy an
explicit frame count or reject it clearly after bounded packing attempts; and
make advertised control bounds agree with accepted values independently of the
default difficulty sampling bands. A stronger frame-domain validator would also
make its advertised geometry meaningful to callers. These remain findings and
repair suggestions for the audited source, with no target modification or status
change made by this audit.

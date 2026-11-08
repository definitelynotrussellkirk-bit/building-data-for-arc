## 09647f283588

**Classification: reproduced construction and teaching defect; findings only, audited source unchanged.** Generator SHA-256: `d11c4c4a10e7beeeb5dbcf1fcf4be7fdb9010d1e8ba10ee10fc11b37a2bc3a69`.

The explicit request `generate(0, 0, difficulty="easy", texture="center_filled", n_frames=2)` silently returns only **one** plain frame and **no center-filled near-miss**. The entire input contains only four nonzero cells, all color 8, at `(3,2), (3,4), (5,2), (5,4)` (zero-based). `self_check` returns `[]`. Repeating with the same parameters except `texture="plain"` returns the identical grid. Thus the requested frame count is not honored, and the advertised center-guard counterexample is absent for this draw.

The cause is directly visible in `repo/generators/09647f283588/generator.py`: active-frame placement stops after 300 random attempts without asserting `placed == target`; near-miss placement similarly stops after 120 attempts without asserting success. The weak self-check asks only for any four equal corners with zero center, so it accepts this underfilled, near-miss-free result. The comment promises “3 demos incl. >=1 near-miss,” but no schedule or lesson-identifiability hook enforces that promise. No callable semantic rivals are declared; the comments alone are not tested competitor declarations.

Fresh canonical Racket execution confirms this is a missing-construction witness, rather than a demonstrated label error: the generated frame gains exactly its four missing border cells. A second hand-made input contains a plain color-4 frame and a separate color-7 frame with nonzero center 3; Racket completes only the color-4 frame and leaves the center-filled near-miss unchanged. Both reference applications succeeded, and executed/catalog rule hashes match `466f3ee55751` (`rule_text_sha256=efb301a8eabefcd3a3125c021b6a2f75b34d952864f081f3abac1c7c6532f622`).

**Minimal recommendation:** backtrack or retry complete layouts until the requested number of frames and requested near-miss exist, or fail visibly. Validate the realized witnesses, rather than merely accepting any active window. If every three-demo lesson must expose a near-miss, implement and test that lesson schedule explicitly. This audit does not change the generator, authority, safety label, or audit disposition.

**Exact reproduction:** from the outer packet directory, run:

```sh
WORK/.venv/bin/python review.py run \
  /workspace/scratch/3d35df884c2e/packet/WORK/.venv/bin/python \
  ../checks/audit/09647f283588/probe.py
```

Payload cwd is `WORK/repo`. Exit status: **0**. Evidence is in `checks/audit/09647f283588/probe.py`, `checks/audit/09647f283588/report.json`, `checks/audit/09647f283588/apply-receipt.json`, `checks/audit/09647f283588/probe.log`, and `checks/audit/09647f283588/receipt.json`. The search was capped at eight seeds and stopped immediately at seed 0: **one center-filled draw, one same-seed plain comparison, two authoritative applications, zero reference errors**. This bounded probe does not estimate prevalence, establish whole-lesson failure rates, or audit every texture/override combination. No prior task-local review index or focused tests were present.

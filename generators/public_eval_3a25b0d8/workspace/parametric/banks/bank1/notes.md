# public_eval_3a25b0d8 — implemented rule and handoff

Canonical interpretation: two 8-connected foreground figures share an outline
color. One is a blank template and the other supplies filled compartments.
Isolate each figure (their bounding boxes can overlap), find its 4-connected
regions enclosed by outline pixels, and match regions by left/center/right
position then vertical order. Fill the blank template with corresponding donor
colors and return the tight template crop. The compartment shapes and areas
need not match. Original training and both test gold outputs are verification
cases only; no stored examples or labels enter either runtime implementation.

Alternative `color_order=reverse_vertical` reverses source colors within each
side lane before transfer. A: extract enclosed regions and their ordered color
lists. B: apply those lists to the distinct target geometry. The alternative
must be taught by colors, not by geometry/settings leakage.

Plan: tests first, standalone sampler + Python mirror, general Racket reference,
native resource-local adapter and public projection, bounded rival/label audit,
protected authoring preflight and wrong-correspondence witness. Source copy
identity and relocated-generator tests prevent hidden workspace dependencies.
No owner qualification, acceptance or training admission is claimed.


## Executed checks and current handoff

The final source is bound by `checks/public_eval_3a25b0d8/preflight-final/preflight.json` and
its sibling execution/original-pair records. Reusable `audit.py` checks the
binding before running protected labels, named shortcut rules and private-field
invariance. `checks/verify_final_witnesses.py` invokes the official schema
validator and replay engine; the invocation is explicitly reviewer-only.

Both settings have matched inputs, independently selected 2–6 demos and 1–4
queries, and a retained four-query controller bank. Public presentation shuffles
that bank with a separate presentation seed and returns one query per view. Never
expose the view list, its length, source indices or private presentation sidecar
to a solver. Saved filenames and emission order derive only from visible content.

The standalone generator declares literal `RULE_public_eval_3a25b0d8_ID = 'ee_3a25b0d8'`. Its source is
copied byte-for-byte into the native resource-local `family.py`; a test enforces
this equality. This intentionally small duplication avoids hidden deployment
imports. Ordinary generator calls support `generate(seed, sample_index)` and
strict keyword difficulty/override validation. Difficulty currently does not
change the generated domain; no effect is claimed for it.

The owner should integrate the task-local delta, preserve/reconcile any parallel
branches, verify originals, register the `ee_` reference, approve source, refresh
the native manifest, and run qualification plus acceptance. The disposable-copy
smoke tool rehearsed unapproved registration, ordinary protected generation and
the official staged tests without changing the actual catalogs. No approvals,
acceptance records or training data are produced by this return.

Final checks: 47/47 staged tests; 4/4 original protected labels; 36 audit episodes,
276 label claims, 61 protected executions, 396 rival checks, 16 saved public
views, zero findings. Separate census: 1,010 unique valid deterministic inputs,
all 1,010 setting-separated. Wrong compartment-color correspondence changes 68
cells on a 30×30 input (30×13 output). Minimal teaching examples stagger center
and side compartments differently between source and target: naive global
reading-order matching fails instead of silently fitting the generated domain.
The provided originals include overlapping figure bounding boxes; isolating
component pixels before cropping is necessary and covered by original-pair tests.

Review limits: self-review by the author, no independent reviewer available.
Finite named rivals and sampled seeds do not prove universal uniqueness or
correctness outside the documented grammar. The complete family test directories
pass together using pytest `--import-mode=importlib`, as the official staged
runner does; default combined collection collides on the shared test basename.

# Native gated-toggle relay family for `b38782448e7b`

**Reviewer status: ready for owner replay; not owner-accepted or training-admitted.**
The selected production generator and canonical authority are unchanged.

The current native adapter exposes one episode-fixed parameter:

| `finish_rule` | Behavior |
| --- | --- |
| `toggle_only` | Exact canonical row-1-gated vertical-toggle program, byte-for-byte. |
| `toggle_then_relay` | Run the canonical toggle, count marker-colored cells in each completed active column, select the unique maximum, and copy that full processed column into the blank lane immediately left of the bottom color-9 cue. |

The alternate rule has a genuine sequential dependency. Stage B must consume the
completed Stage-A column rather than its raw source. The retained protected-
Racket counterfactual preserves the chosen column but relays the raw column,
changing 12 final cells.

`adapter.py` supports 2–6 demonstrations and 1–4 independent, prefix-stable
queries with identical inputs across settings. The four-query schedule is
13×15, 18×20, 24×27, and 30×30; the final case has more than 110 non-background
cells and touches every boundary. Public sequential views reveal only the
visible demonstrations and current query input, with no total-query hint.

Current evidence:

- 64/64 task tests and 20/20 focused native tests.
- 48 finite self-review episodes over seeds 0–7, demo counts 2/3/6, both settings, and four queries; every declared harmful rival is rejected by demonstrations.
- Native qualification for both settings at seeds 0 and 17: four jobs and 32 protected-Racket label evaluations.
- Byte-identical qualification/execution replay, verified public projections, and a source-bound protected-Racket causal witness.

The finite rival list is not a proof against arbitrary programs. Exact-source
owner integration, fresh owner qualification, acceptance replay, and any
training-admission decision remain pending.

The older four-setting gated-XOR prototype remains in this directory as
historical provenance; it is not the current admission candidate.

From the outer packet directory, useful checks are:

```bash
python3 review.py run python3 -m pytest -q \
  generators/b38782448e7b/tests/test_parametric_native_relay.py
python3 review.py run python3 \
  generators/b38782448e7b/workspace/parametric/audit_native.py \
  --out ../checks/b38782448e7b/audit.json
```

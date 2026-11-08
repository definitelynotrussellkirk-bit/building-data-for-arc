# Native beam-finish family for `b91a3b0baac4`

**Reviewer status: ready for owner replay; not owner-accepted or training-admitted.**
The selected production generator and canonical authority are unchanged.

The current native adapter exposes one episode-fixed parameter:

| `finish_rule` | Behavior |
| --- | --- |
| `beam_only` | Exact canonical blocker-aware beam program, byte-for-byte. |
| `beam_then_highlight_longest` | Run the canonical beams, measure each emitter's newly painted blocker-truncated segment, and recolor the unique longest derived segment to color 8. |

The alternate rule has a genuine sequential dependency: the highlighted cells
cannot be selected from the raw input alone because both the winning emitter and
its exact segment are derived from Stage A's completed-grid delta. The retained
protected-Racket counterfactual substitutes the shortest derived segment and
changes 11 final cells.

`adapter.py` supports 2–6 demonstrations and 1–4 independent, prefix-stable
queries with identical inputs across settings. The four-query schedule is
13×15, 18×20, 24×27, and 30×30; the final case has active and irrelevant
blockers and touches every boundary. Public sequential views reveal only the
visible demonstrations and current query input, with no total-query hint.

Current evidence:

- 82/82 task tests and 20/20 focused native tests.
- 48 finite self-review episodes over seeds 0–7, demo counts 2/3/6, both settings, and four queries; every declared harmful rival is rejected by demonstrations.
- Native qualification for both settings at seeds 0 and 17: four jobs and 32 protected-Racket label evaluations.
- Byte-identical qualification/execution replay, verified public projections, and a source-bound protected-Racket causal witness.

The finite rival list is not a proof against arbitrary programs. Exact-source
owner integration, fresh owner qualification, acceptance replay, and any
training-admission decision remain pending.

The older `blocker_mode = {stop, pass}` prototype and its evidence remain in this
directory as historical provenance; it is not the current admission candidate.

From the outer packet directory, useful checks are:

```bash
python3 review.py run python3 -m pytest -q \
  generators/b91a3b0baac4/tests/test_parametric_native.py
python3 review.py run python3 \
  generators/b91a3b0baac4/workspace/parametric/audit_native.py \
  --out ../checks/b91a3b0baac4/audit.json
```

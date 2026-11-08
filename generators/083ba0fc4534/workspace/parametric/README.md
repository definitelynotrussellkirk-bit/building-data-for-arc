# Parametric three-panel agreement family

Status: reviewer-ready proposal; owner exact-source acceptance remains required.
The production generator and canonical rule are unchanged.

Each episode fixes one private `agreement` setting while sharing the same input
sampler across settings:

| setting | aligned nonzero color survives when |
| --- | --- |
| `majority` | at least two of the three panels agree; exact canonical default |
| `unanimous` | all three panels agree |

Every input contains pair-only agreement, all-three agreement, color conflicts,
and singleton distractors. Thus two demonstrations already separate the two
settings without consulting query answers. Demonstrations support counts 2–6;
queries are exactly four distinct inputs with shapes 5×14, 12×20, 21×26, and
30×29. Width 29 is the lawful maximum because equal vertical panels require
`input_width = 3*panel_width + 2`; exact 30×30 cannot preserve that grammar.
The 30×29 query has substantive activity across all boundaries rather than empty
padding.

Sequential dependency: step A discovers the two full-height gray divider
columns. Its input-dependent intermediate `(d1,d2)` determines panel width and
aligned offsets. Step B compares the three cells addressed through those offsets
and applies the episode's agreement threshold. A fixed-divider rival matches a
4-column panel but fails wider inputs; `probe.py` retains the protected-Racket
witness.

Run focused tests from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/083ba0fc4534/tests/test_parametric_consensus.py -q
```

After source changes, refresh the manifest and run native qualification as
documented in `repo/docs/parametric-promotion.md`. Then build the bounded
protected-Racket authoring report and owner-replay causal witness from that exact
qualification:

```bash
python3 review.py run python3 \
  generators/083ba0fc4534/workspace/parametric/probe.py \
  --out generators/083ba0fc4534/workspace/parametric/evidence/current/authoring.json \
  --witness ../checks/083ba0fc4534/causal_witness.json \
  --qualification ../checks/083ba0fc4534/qualification/qualification.json
```

Because `authoring.json` is inventoried evidence, refresh the manifest after this
command. A final qualification should have the same `source_binding`; rerun the
probe against that final receipt and require byte-identical report/witness output.
The probe refuses a non-qualified or wrong-task receipt and emits the exact
`arcpuzzles-sequential-dependency-witness-v1` transport schema. Public projections use
`reviewer_support.public_challenge_bytes`; query outputs, settings and programs
remain private. `public_turn` reveals one query at a time with no count marker or
future-query data.

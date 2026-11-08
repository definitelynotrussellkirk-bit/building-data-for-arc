# Proposed parametric extension: projection depth

This isolated prototype leaves the selected production generator, canonical
`RULE_HASH`, and canonical task labels unchanged. It varies exactly one
meaningful episode-level rule parameter:

- `projection_depth`: allowed values `1` and `2`;
- canonical/default value: `1`;
- the value is chosen once per complete episode and reused across three
  demonstrations and one query;
- depth 1 materializes the canonical Racket program byte-for-byte;
- depth 2 changes only the marker destination offset, painting two cells toward
  the matching colored border instead of one.

Inputs are generated independently of the selected parameter. The retained
probe accepts only grids for which both depths are in bounds, collision-free,
and write only to background cells. Every label is executed from the exact
materialized Racket source through the protected bridge and checked against an
independent Python mirror. The public evidence includes labeled demonstrations
and an unlabeled query only; seeds, parameter choices, source, rivals, and query
answers stay in private evidence.

From the outer extracted packet, run:

```sh
python3 review.py run python3 \
  generators/b19deac47327/workspace/parametric/prototype.py evidence \
  --seeds 0 1 \
  --out ../checks/parametric/projection-depth-v1
```

This is a **proposed, unapproved** extension. The retained two-setting evidence
is not production approval and does not establish identifiability against every
possible rival rule or every valid input.

# Review probe

`review_probe.py` is a source-bound diagnostic for future reviewers.  It prints
component bboxes, symmetry decisions, selected candidate, semantic witnesses,
and every declared rival's output for one generated sample.  `--sweep N`
aggregates schedule coverage, candidate counts, rival disagreements, witness
firings, validation failures, and output diversity.

Run it from a staged repository environment where `puzzle_generators` is on
`PYTHONPATH`, for example:

```bash
python generators/81fdfd815936/workspace/review_probe.py --seed 7 --sample-index 0
python generators/81fdfd815936/workspace/review_probe.py --sweep 100 --difficulty hard
```

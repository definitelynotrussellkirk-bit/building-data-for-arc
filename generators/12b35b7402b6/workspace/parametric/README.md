# 12b35b7402b6 parametric family

`mode=canonical` uses the selected canonical Racket source byte-for-byte.
`mode=linked_payload` is a two-stage rule: apply canonical marker-count
selection, then recompute the largest red 4-component on that intermediate and
use its size to recolor one azure payload yellow.

The generator is setting-neutral.  Every scene contains an original-red key,
a post-Stage-A key, an 8-connectivity decoy, marker-count/span decoys, and
position/rank crossings.  The fourth query is a 30x30 stress case.

Useful commands from `WORK/repo`:

```bash
python generators/12b35b7402b6/workspace/parametric/semantic_sweep.py --count 200
python generators/12b35b7402b6/workspace/parametric/adversarial_probe.py --seeds 0 1 2
python generators/12b35b7402b6/workspace/parametric/prototype.py --mode linked_payload --racket
```

`semantic_sweep.py` is cheap and Python-only. `adversarial_probe.py` executes
both selected rules and every declared wrong rule through protected Racket and
retains exact counterexamples. `skip_stage_a.rkt` is the protected causal
counterfactual used by the sequential-dependency witness.

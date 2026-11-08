# Workspace

`semantic_probe.py` is a reusable, source-bound audit for the selected generator. It imports the generator's actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES` rather than copying rival names.

From the packet root:

```sh
python3 run_with_racket.py python3   generators/c05faa9b2b85/workspace/semantic_probe.py   --out ../checks/semantic-probe-v2.json
```

The probe verifies:

- every declared canonical shortcut against all usable canonical pairs;
- all 27 exact joint override combinations;
- all three cyclic starts of the period-three, three-demo lesson schedule;
- one exact generated witness on which every declared rival disagrees with the Python rule mirror.

The supported Racket output for the retained final witness is separately recorded in `checks/shortcut-witness-v2/racket.json`.

# Review workspace for 3065bdeaa7b0

- `reference_probe.py` is an implementation-independent Python oracle plus four
  named rival rules and a real-Racket parity helper. It does not import private
  helpers from `generator.py`.
- `lesson_probe.py` stages the final source through the public runtime copier,
  builds actual 3-demo/1-query episodes with `runner.run_one`, obtains labels
  from the selected Racket rule, dynamically reads the generator's declared
  rivals/witnesses, and writes a source-hashed finite census.

From the packet root, with the protected runtime installed:

```bash
python3 run_with_racket.py python3 \
  generators/3065bdeaa7b0/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/task_probe/lesson_probe.json \
  --timeout 1800
```

The retained final report covers 100 lessons in each of easy, medium, and hard.
It is finite evidence against the declared competitors, not a proof against all
possible ARC hypotheses.

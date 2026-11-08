# Review workspace: 964b23808a3c

`review_probe.py` is a source-bound authoring check for future reviewers. It uses
an independent Python oracle and the portable canonical-data helpers to verify:

- all canonical labels and canonical-input acceptance;
- exact scheduled `(height, width, palette-count)` coverage in every band;
- that each declared canonical shortcut really fits every canonical pair;
- generated counterexamples for every declared rival; and
- every query rotation in consecutive four-pair curriculum windows.

It reads canonical answers, so keep it closed during solve episodes.

From the repository root/runtime root:

```bash
python3 generators/964b23808a3c/workspace/review_probe.py \
  --seeds 16 --windows 9 --json-out ../checks/review-probe.json
```

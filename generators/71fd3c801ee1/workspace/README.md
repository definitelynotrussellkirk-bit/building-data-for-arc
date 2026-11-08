# 71fd3c801ee1 repair workspace

`feature_probe.py` is an independent analyzer for this task. It reconstructs
4-connected objects, computes `(area, holes, symmetry-class)`, applies the full
rule and four plausible shortcuts, and reports exactly which rivals disagree.
It deliberately does not import `generator.py`.

```bash
python3 feature_probe.py witness.json --out witness-report.json
```

The retained `shortcut-witness.json` is a final-generator sample. Its report
shows that exact-outline, area-only, area+holes, and area+symmetry all disagree
with the complete triple rule.

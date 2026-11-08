# 094e0794786c

One connected blue(1) object and one connected red(2) object are placed separately on a zero background. Each object has 3–7 cells. Crop and top-left-normalize the two objects, then emit cyan(8) exactly on their symmetric difference in a grid sized to the maximum normalized bbox. Every selected-generator sample contains normalized overlap plus exclusive cells from both objects, so union, intersection, and either one-shape shortcut are visibly wrong.

The v3.0.0 sampler uses a finite connected-polyomino bank and finite placement enumeration, honors four observable exact axes, rejects unknown overrides, pins `RULE_HASH=e94c733a8465`, and exposes executable lesson witnesses/rivals. See `workspace/domain_probe.py` for an exhaustive 3,000-case declared-axis probe and `tests/test_generator.py` for portable regression coverage.

Kind: `per_puzzle`. Selected version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.

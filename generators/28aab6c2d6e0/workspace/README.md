# Workspace — 28aab6c2d6e0

The selected implementation is `../generator.py`. Workspace programs are review/probe tools
and are never selected as the generator automatically.

## `semantic_probe.py`

Source-bound lesson stress tool. By default it checks 100 lessons in each of easy, medium,
and hard. It imports the selected generator, iterates its actual canonical-shortcut,
competitor, and witness declarations, verifies that claimed canonical shortcuts fit every
usable canonical pair, and reports:

- generator/rule hashes and exact sampling policy;
- strict-domain failures;
- unique inputs, dimensions, and object counts;
- witness frequencies and per-example rival disagreements;
- rivals that survive complete three-demonstration lesson windows.

The retained final report is `checks/semantic_probe_100.json`. This tool measures the declared
hypotheses under the recorded sampler; it does not prove universal identifiability.

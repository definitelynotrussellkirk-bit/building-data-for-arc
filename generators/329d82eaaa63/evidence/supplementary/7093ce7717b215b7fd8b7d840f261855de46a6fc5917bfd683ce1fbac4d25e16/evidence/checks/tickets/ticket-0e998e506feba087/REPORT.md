# Audit replay — ticket-0e998e506feba087

**Status: reproduced.** The retained no-issue audit witness for `329d82eaaa63`
was replayed against the exact pinned source, audit index, audit record, and asset
manifest. All six identity hashes in `report.json` match their ticket pins;
executed rule hash: `c3b26f3f0fc8`.

The single bounded command completed with exit code 0 in 5.773 seconds. It ran the
retained portable tests (`54 passed in 1.78s`), checked all 2,688 declared axis
Cartesian requests (1,456 exact lawful generations and 1,232 expected structured
incompatibilities, with no unexpected failures), and checked 320 lesson rotations
with zero declared-rival ambiguity.

This is a finite replay of the retained declared axes and rivals. It does **not**
clear the existing audit, establish uniqueness against undeclared hypotheses, or
change source, approval, or training status. Exact command and outputs are in
`command.json`, `report.json`, and `replay.py`.

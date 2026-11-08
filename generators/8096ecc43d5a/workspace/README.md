# Transform-script authoring analysis

`analyze_script_maps.py` enumerates constant command-to-D4-transform mappings
against every normalized, labeled canonical train and test pair for this task.
It imports the selected generator through public `reviewer_support` helpers to
record its source identity, but does not call `generate()` or execute Racket.
The canonical outputs are previously recorded authoring labels.

From the repository directory:

```bash
python generators/8096ecc43d5a/workspace/analyze_script_maps.py \
  --include-pools --out ../checks/script-map-analysis.json
```

In a review packet, the equivalent command from the packet directory is:

```bash
python review.py run python generators/8096ecc43d5a/workspace/analyze_script_maps.py \
  --include-pools --out ../checks/script-map-analysis.json
```

Omit `--include-pools` for only the map census; omit `--out` to print JSON.
`--root PATH` explicitly selects another library or copied runtime. Otherwise
source discovery follows this tool's own tree, independently of the working
directory. Re-run after source changes to refresh the recorded hashes.

## Current result and proof scope

All **4,096** possible constant mappings of four commands to eight D4 transforms
were considered. Exactly **four** fit all four labeled canonical pairs:

| Mapping | Code 1 | Code 2 | Code 3 | Code 4 |
|---|---|---|---|---|
| Intended | Clockwise 90° | Left-right flip | 180° | Up-down flip |
| Alternative A | Clockwise 90° | Up-down flip | Identity | Left-right flip |
| Alternative B | Counterclockwise 90° | Left-right flip | Identity | Left-right flip |
| Alternative C | Counterclockwise 90° | Up-down flip | 180° | Up-down flip |

The optional search finds **320** scripts of length 4–6 that refute the eight
listed script shortcuts and distinguish at least one remaining alternative map.
Its groups contain 14 scripts with mask `011`, 153 with `101`, and 153 with `110`;
the JSON records the mask order and each script's net transform. These claims
require a motif with eight distinct D4 orientations. Leading blank command
padding additionally refutes the stop-at-first-zero shortcut.

This is finite candidate analysis. It does not enumerate every possible solver,
prove that every fresh lesson identifies a unique command mapping, or establish
all-seed correctness, generator approval, or training eligibility. Racket
execution and whole-lesson/query-rotation checks remain separate verification.
The selected generator is `../generator.py`; workspace tools do not replace it.

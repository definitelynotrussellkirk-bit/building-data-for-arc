# Working notes: 6f6c567e365b

## Repair decisions

- The authority is cumulative: each key transforms the prior state. The imported summary incorrectly described independent transforms.
- The original monochrome sampler preserved an “ignore keys” shortcut. Generalized scenes now use asymmetric connected multicolor motifs with directional color cues.
- The nondefault family setting creates a real `input -> executed final state -> cue color -> projected gallery` dependency.
- Minimum-demo audits explicitly test independent transforms, projection by the original first color, and projection by the globally smallest color.
- A bounded audit initially found one seed where the final cue equaled the global minimum. Construction now forbids that coincidence; the repaired audit has zero surviving named rivals.
- The canonical program file is pinned to the unique catalog-selected program SHA-256 `33361398d469a728c0dc9cf6e18334879d3ed11c694bc04ca6e5d1f1a061e87c`.

Imported historical notes remain in `evidence/associated_notes.jsonl`.

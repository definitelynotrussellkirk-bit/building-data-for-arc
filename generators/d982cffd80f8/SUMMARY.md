# d982cffd80f8 — single-cell hole fill

Fill an original zero cell only when all eight original neighbors have the same
nonzero color. Preserve everything else, including incomplete borders, inert
singleton pixels and already nonzero centers. Labels use the unchanged canonical
Racket rule `58201e67a052`.

Version **3.0.0** samples one to six positive hollow 3-by-3 borders on zero
backgrounds, with exact dimensions and foreground color counts when requested.
Borders may touch. Default examples add a near-ring and a differently colored
nonzero center to distinguish plausible shortcuts. Difficulty changes sampling
preferences; it does not invalidate otherwise lawful center counts.

Normal lesson assembly: three demonstrations and one query. Four declared rivals
are tested, with all query rotations required in the reported final checks.
The sampler uses a bounded tile grammar; small or fully pinned manual overrides
may omit contrasts or be explicitly unsupported. See `notes.md` for limits.

Kind: `per_puzzle`. Approval is derived separately by the catalog from current
source and retained evidence; review success alone does not approve training use.

# 3a0af56db83e

A 12xW zero-background input is four stacked 3-row monochrome masks. Project the four bands onto one 3xW frame and choose the first nonzero cell in priority order band 0, then band 1, then band 3, then band 2; emit 0 only when all four projected cells are 0. Band colors are distinct within a scene and may be reassigned across bands, so color identity is not a substitute for band priority. Every generated scene contains projected overlap arities 0 through 4 and all six pairwise priority witnesses; non-witness cells mix neighboring arities while preserving the exact sparse/canonical/dense foreground-count contract. Palette scheduling excludes the single numeric ordering that would make “choose the largest color” agree with the physical priority rule.

Kind: `per_puzzle`. Imported version: `3.1.1`.
Approval is derived by the catalog from current code and retained evidence.

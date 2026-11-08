# 13d89a533e59

Find every isolated 2x2 color-2 block and its four distinct diagonal markers. Rotate the marker values one corner forward around the block (TL->TR->BR->BL->TL), then extend each new corner value outward along its diagonal through cells that were 0 in the input. Stop at the edge or any nonzero input cell. A canonical near-block exception suppresses a candidate zero beside a color-2 cell when exactly one further diagonal zero remains before the following cell/edge; that ray stops without painting the candidate.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.

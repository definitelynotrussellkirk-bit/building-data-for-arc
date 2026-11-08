# Final source-patch replay

The replay used the packet's declared runtime dependency closure: 333 files were
extracted from an 85,117-file original manifest. The official validator still
checked the complete original manifest, full return contract and complete patch
inventory before applying `patches/source.patch`.

The replayed source patch SHA-256 is
`74248574e990d9f16f1d4d8c17d4da4f8b0250f57e55a2e54ab64bc7ec3c6906`.
The applied generator SHA-256 is
`cbcf3f9249c0f98cdc8bb021e7e16156d5a1e277d7b65abca53ac57ab308bd24`.
After replay, the focused task-local suite passed 27/27. The final deliverable
must retain the same source-patch hash; top-level evidence/RESULTS rebinding does
not alter that patch.

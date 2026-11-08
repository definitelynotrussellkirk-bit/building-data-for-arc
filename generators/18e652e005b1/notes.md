# Working notes: 18e652e005b1

## Current decision

Keep the frozen gapped motif broadcast as the exact default. The nearby variant crops the same motif and places ordered command-colored copies at `motif_width - 1` stride; only cells with multiple real copy contributors become color 8.

All constructed motifs occupy matching rows on both crop edges, so every adjacent-copy boundary contains genuine overlap. The retained first-copy-wins program uses the same geometry but discards contributor multiplicity and changes six final cells. The inherited canonical test now uses the staged-runtime portable `reviewer_support` data API instead of a fixed repository depth.

Status: reviewer-ready authoring preflight only. Owner exact-source qualification/acceptance and any training admission remain pending.

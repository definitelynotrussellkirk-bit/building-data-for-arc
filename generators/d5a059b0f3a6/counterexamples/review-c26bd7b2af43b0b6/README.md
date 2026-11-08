# Retained teaching defect and repair

The inherited source (`sha256 98868b9812ca1ffbabafd8f96585dea2eee34145e12e6ff9d09eec52f96eb5d2`) allowed seed 109, medium, sample indices 0–2 to be three `horizontal_frames` demonstrations while index 3 was a `mixed_axes` query. The plausible rival “remove external blue cells but always mirror left-right” matched every demonstration and differed on the query.

The repaired generator uses a 16-slot deterministic curriculum that preserves the former 25% profile proportions while placing two mixed-axis witnesses in every four consecutive slots. `workspace/check_schedule.py` exhaustively checks every cyclic start, difficulty call, and one-query rotation against all declared competitors. The original source-bound audit artifacts remain under `counterexamples/review-f4cb9d0b248a69e5-v0001/`; repaired evidence is written to `WORK/checks/schedule/verification.json` by the review wrapper.

This closes the specific declared-rival teaching defect. It does not prove uniqueness against every conceivable rule.

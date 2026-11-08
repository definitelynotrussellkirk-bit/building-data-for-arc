# F1: Biggest avoidable friction: legacy staged-test imports are easy to invoke incorrectly

Raw `pytest` does not create the legacy `puzzle_generators.per_puzzle` runtime namespace, so a final direct run can fail during collection even when the staged task suite is healthy. Make `review.py duties` print the exact `review.py task-tests TASK --phase after --out ...` command next to the task, or migrate remaining task tests to `reviewer_support.load_selected_generator` so ordinary pytest is portable.

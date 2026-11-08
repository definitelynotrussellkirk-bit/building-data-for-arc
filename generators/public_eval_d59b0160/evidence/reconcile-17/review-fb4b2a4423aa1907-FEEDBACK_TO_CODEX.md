## F1: Biggest avoidable friction: verbose task-test stdout

Task-test commands print a large source-binding object even though it is already retained in source-binding.json. Default stdout to status, test counts and evidence paths, keeping the full binding in the saved receipt.

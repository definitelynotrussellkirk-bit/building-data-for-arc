# Feedback to Codex

## F1: Start protected replay before retaining bulk export payloads
Starting the protected Racket worker only after hundreds of public projections had accumulated caused avoidable stalls. Run protected replay before bulk export retention, or isolate each replay in a bounded child process with progress output and a hard timeout.

# Biggest avoidable friction: public preview/export for unregistered families

F1: Public-creation preflight has no direct source-bound one-query preview/export command for an unregistered family, so checker-ready public views required an ad hoc exporter. Add a preflight-aware export/verify subcommand that consumes `execution.json` plus `adapter.public_view`, emits public-only files, and records one binding receipt.

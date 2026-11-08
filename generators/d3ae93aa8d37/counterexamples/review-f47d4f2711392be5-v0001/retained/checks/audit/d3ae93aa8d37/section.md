## d3ae93aa8d37

**Reproduced in-domain wrong-query teaching defect; findings only, source unchanged.**

Audited generator SHA-256: `8a8e643a90a7902abb45493d2c58de3527e620c00a1411c3e5c29e85dccc661c` (version `1.2.0`). Executed canonical rule hash: `01f433c4866f`; exact rule text SHA-256: `e69bc96ead8154c2c9af7831fbdb217740e74ca42e60f9a31d623eaa511fb8c8`.

The production generator's comments promise a wall-forced detour in each four-demonstration lesson, but it places walls independently and declares no lesson-level schedule or rival check. Using the supported production command with seed **8**, difficulty **easy**, requested start **1**, four demonstrations and one query emitted accepted sample indices **[1, 2, 3, 4, 5]**, with **zero rejections**. Every input passed the selected generator's `self_check`.

The rival **“paint every cell strictly between the same-row red and green endpoints cyan, ignoring walls”** agrees with all four Racket-labelled demonstrations, then predicts a different answer for query sample **5**. Its query input SHA-256 is `648477eb76e5b5fd996ed20c72b2809abef6196dee571db6bb0497736b47273a`. In this 8×9 input, red is at `(1,0)`, green at `(1,4)`, and a gray wall blocks `(1,1)` (zero-based coordinates). The authoritative BFS output preserves that wall and paints a detour through `(0,0)`, `(0,1)` and `(0,2)`. The rival omits those three cells and overwrites `(1,1)` with cyan. Both outputs otherwise agree.

This freshly verified ordinary production lesson strengthens the two existing source-bound unresolved findings (`review-a2c266162772fd6b:v0001` and `review-87a228b0ec50cd83:v0001`). Their seed-8/start-0 lesson had the rival agree on demonstrations **and** query; that inherited observation did not establish a wrong-query lesson. Moving the production start to 1 now gives a direct differing query under the same unchanged source. The rival fits only one of this task's five canonical pairs, so this finding concerns insufficient generated teaching support rather than a shortcut fitting the complete canonical task.

**Recommendation:** retain this exact failing lesson, schedule or enforce a wall-forced detour demonstration within every declared four-demo production window, and declare the obstacle-blind rival in the lesson-identifiability contract. If arbitrary query rotations are supported, also ensure a second detour witness remains when either one is held out. No source, authority or approval changes were made during this audit.

Exact production episode and all Racket/rival outputs: `checks/audit/d3ae93aa8d37/wrong-query-episode.jsonl` and `checks/audit/d3ae93aa8d37/wrong-query-evidence.json`. A second supported Racket application to the exact query is retained in `checks/audit/d3ae93aa8d37/query-racket.json`; `verification.json` binds and compares those two execution results. Commands, working directories and exit codes are in `checks/audit/d3ae93aa8d37/commands.json`; scripts and logs are retained beside them.

**Scope and limits:** one deterministic production counterexample, not a measured prevalence; no full battery or full repository suite was run, and no universal BFS/canonical correctness claim is made. Existing unsafe/unapproved status and unresolved audit dispositions remain unchanged.

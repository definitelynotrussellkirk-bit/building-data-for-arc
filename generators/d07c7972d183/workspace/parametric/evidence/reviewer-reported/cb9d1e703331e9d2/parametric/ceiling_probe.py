from arc_repl.racket_bridge import RacketBridge
import json
with RacketBridge() as bridge:
    expressions = ["(/ 7 3)", "(ceiling (/ 7 3))", "(quotient (+ 7 2) 3)", "(/ 9 2)", "(ceiling (/ 9 2))", "(quotient (+ 9 1) 2)"]
    print(json.dumps({expression: bridge.eval_text(expression) for expression in expressions}, sort_keys=True))


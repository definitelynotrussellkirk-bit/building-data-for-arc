"""One rectangular CCW call through the supplied native Racket bridge."""
import hashlib
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
runtime=HERE.parents[1]/'repo/shared/runtime'
sys.path.insert(0,str(runtime))
from arc_repl.racket_bridge import RacketBridge
import arc_repl.racket_bridge as module
program='(rule! rotate-ccw)'
grid=[[1,2,3],[4,5,6]]
with RacketBridge() as bridge:
    bridge.eval_text('(define (rule! f) f)')
    bridge.eval_text('(define authority-calibration-rule '+program+')')
    bridge.define_grid('authority-calibration-input',grid)
    output=bridge.eval_text('(authority-calibration-rule authority-calibration-input)')
expected=[[3,6],[2,5],[1,4]]
assert output==expected,(output,expected)
bridge_path=Path(module.__file__).resolve()
prelude=bridge_path.parent/'racket_prelude/arc-prelude.rkt'
receipt={'schema':'callable-authority-native-probe-v1','program':program,'input':grid,'output':output,
         'racket_calls':1,'expected_ccw':expected,'matches':True,
         'bridge_sha256':hashlib.sha256(bridge_path.read_bytes()).hexdigest(),
         'prelude_sha256':hashlib.sha256(prelude.read_bytes()).hexdigest()}
(HERE/'racket-probe.json').write_text(json.dumps(receipt,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(receipt,sort_keys=True))

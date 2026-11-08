"""Finite Python rival audit; does not replace protected reference execution."""
import argparse
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_packing_audit_adapter',BASE/'adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
C=A.CORE
RIVALS=('original','first_placed_piece','source_first','source_last','largest_piece','smallest_piece','last_placed_piece','first_pixel','global_piece_mode','mirror_whole','unfilled','source_order_greedy')


def predictions(grid):
    bg,frame,board,pieces=C.parse(grid)
    packed,records=C.pack(board,pieces,bg,True)
    def painted(color):
        return [[color if board[r][c]==frame else v for c,v in enumerate(row)] for r,row in enumerate(packed)]
    modal=lambda p:C.mode(v for row in p for v in row)
    result={'original':packed,'first_placed_piece':painted(modal(records[0][2])),
        'source_first':painted(modal(pieces[0])),'source_last':painted(modal(pieces[-1])),
        'largest_piece':painted(modal(max(pieces,key=lambda p:len(p)*len(p[0])))),
        'smallest_piece':painted(modal(min(pieces,key=lambda p:len(p)*len(p[0])))),
        'last_placed_piece':painted(modal(records[-1][2])),'first_pixel':painted(records[0][2][0][0]),
        'global_piece_mode':painted(C.mode(v for p in pieces for row in p for v in row)),
        'mirror_whole':[row[::-1] for row in packed],'unfilled':board}
    # Greedy source order never revisits a placement and is a total predictor.
    out=[row[:] for row in board];inventory=list(pieces)
    while inventory:
        holes={(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v==bg}
        if not holes:break
        r,c=min(holes);chosen=None
        for i,p in enumerate(inventory):
            if all((r+a,c+b) in holes for a in range(len(p)) for b in range(len(p[0]))):
                chosen=i;break
        if chosen is None:break
        p=inventory.pop(chosen)
        for a,row in enumerate(p):out[r+a][c:c+len(row)]=row
    result['source_order_greedy']=out
    return result


def audit(seeds=range(16),demo_counts=(2,3,6)):
    seeds=list(seeds);harmful=[];equivalent=[];episodes=0;pairs=0;boundary=0
    for seed in seeds:
        bank=A.generate(seed,{'frame_policy':'original'},6,4)
        pred_train=[predictions(p['input']) for p in bank['train']]
        pred_test=[predictions(p['input']) for p in bank['test']]
        for demos in demo_counts:
            for chosen in ('original','first_placed_piece','last_placed_piece'):
                episodes+=1;pairs+=demos+4
                survives=[name for name in RIVALS if all(p[name]==p[chosen] for p in pred_train[:demos])]
                for name in survives:
                    if name==chosen:continue
                    rec={'seed':seed,'demos':demos,'setting':chosen,'rival':name}
                    if any(p[name]!=p[chosen] for p in pred_test):harmful.append(rec)
                    else:equivalent.append(rec)
                boundary+=int(len(bank['test'][3]['input'])==30 and len(bank['test'][3]['input'][0])==30)
    return {'schema':'arcpuzzles-finite-teaching-audit-v1','status':'passed' if not harmful else 'failed','episodes':episodes,'labeled_pairs':pairs,'seeds':seeds,'demo_counts':list(demo_counts),'rivals':list(RIVALS),'harmful_survivors':harmful,'finite_equivalent_survivors':equivalent,'substantive_30x30_episodes':boundary,'label_backend':'independent Python claims; protected Racket in separate preflight/boundary receipts','limits':'Finite named rivals and seeds; no universal rule uniqueness or owner acceptance.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    report=audit(range(args.seeds));args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','harmful_survivors')}))
    raise SystemExit(report['status']!='passed')

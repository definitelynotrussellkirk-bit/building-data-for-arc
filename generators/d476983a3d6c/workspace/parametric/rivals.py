"""Independent semantics and finite executable rivals; no prototype imports."""
from __future__ import annotations
from functools import lru_cache, partial
from typing import Callable
MODES = ('command', 'avoid_painted')
_COMMON = ('noop','restore_command','clear_command','drop_singletons','drop_nonpairs','always_hv','always_vh','color_count_parity_command','paired_count_parity_command','profile_command','numeric_color_order','descending_color_order','reverse_color_order','first_pair_only','first_two_pairs','first_four_pairs','last_pair_only','skip_aligned','skip_edge_endpoints','protect_input_markers','paint_background_only','at_least_two_markers','first_last_markers','current_canvas_markers','first_leg_only','second_leg_only')
_COMMAND = ('swap_command','avoid_painted_setting')
_AVOID = ('command_setting','original_canvas_costs','previous_canvas_costs','only_new_paint_costs','any_collision_cost','distinct_colors_cost','maximum_collision_cost','tie_always_hv','tie_always_vh','tie_opposite_command','flip_if_command_collides','avoid_first_two_only','ignore_nonpairs','first_pair_command','positive_tie_hv','positive_tie_vh','cap_two_cost')
EQUIVALENCES = {
 'command:reverse_endpoints':'command:swap_command',
 'avoid_painted:reverse_endpoints':'avoid_painted:tie_opposite_command',
 'endpoint_cost_inclusion':'Both candidates contain the same endpoints; their contribution cancels.',
 'maximum_empty_cells':'Equivalent to minimum occupied cells because both L candidates have equal distinct-cell length.',
}

def _mode(mode):
 if mode not in MODES: raise ValueError('mode must be command or avoid_painted')
 return mode

def _grid(grid):
 if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30
     or any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
  raise ValueError('grid must be a rectangular exact-int ARC list in 1..30')
 command=grid[0][0]
 if command not in (1,2) or sum(v==command for row in grid for v in row)!=1:
  raise ValueError('top-left command must be unique and equal to 1 or 2')
 return [row[:] for row in grid]

def _positions(grid,color):
 return [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color]

def _palette(grid):
 return list(dict.fromkeys(v for r,row in enumerate(grid) for c,v in enumerate(row) if (r,c)!=(0,0) and v))

def _legs(a,b,command):
 ar,ac=a;br,bc=b
 rs=range(ar,br+(1 if br>=ar else -1),1 if br>=ar else -1)
 cs=range(ac,bc+(1 if bc>=ac else -1),1 if bc>=ac else -1)
 if command==1:return [(ar,c) for c in cs],[(r,bc) for r in rs]
 return [(r,ac) for r in rs],[(br,c) for c in cs]

def _path(a,b,command):
 x,y=_legs(a,b,command)
 return list(dict.fromkeys(x+y))

def _predict(grid,mode,variant=None,*,trace=False):
 _mode(mode);original=_grid(grid)
 if variant is not None and variant not in RIVAL_NAMES(mode) and variant!='reverse_endpoints':raise ValueError(f'unknown rival {mode}/{variant}')
 if variant=='noop':return (original,[]) if trace else original
 actual_mode='avoid_painted' if variant=='avoid_painted_setting' else 'command' if variant=='command_setting' else mode
 palette=_palette(original)
 if variant=='numeric_color_order':palette.sort()
 elif variant=='descending_color_order':palette.sort(reverse=True)
 elif variant=='reverse_color_order':palette.reverse()
 counts={v:len(_positions(original,v)) for v in palette};pair_count=sum(n==2 for n in counts.values())
 command=original[0][0]
 if variant=='color_count_parity_command':command=1 if len(palette)%2 else 2
 if variant=='paired_count_parity_command':command=1 if pair_count%2 else 2
 if variant=='profile_command':command=2 if pair_count==6 or sum(n==1 for n in counts.values())==2 else 1
 if variant=='swap_command':command=3-command
 out=[row[:] for row in original];previous=[row[:] for row in original];records=[];index=0
 for color in palette:
  cells=_positions(original,color)
  eligible=len(cells)>=2 if variant in ('at_least_two_markers','first_last_markers') else len(cells)==2
  if not eligible:continue
  ix=index;index+=1
  if variant=='current_canvas_markers':
   cells=_positions(out,color)
   if len(cells)!=2:continue
  a,b=(cells[0],cells[-1]) if variant=='first_last_markers' else (cells[0],cells[1])
  if variant=='reverse_endpoints':a,b=b,a
  if variant=='first_pair_only' and ix>=1:continue
  if variant=='first_two_pairs' and ix>=2:continue
  if variant=='first_four_pairs' and ix>=4:continue
  if variant=='last_pair_only' and ix!=pair_count-1:continue
  if variant=='skip_aligned' and (a[0]==b[0] or a[1]==b[1]):continue
  if variant=='skip_edge_endpoints' and any(r in (0,len(out)-1) or c in (0,len(out[0])-1) for r,c in (a,b)):continue
  hv=_path(a,b,1);vh=_path(a,b,2)
  canvas=original if variant=='original_canvas_costs' else previous if variant=='previous_canvas_costs' else out
  def cost(path):
   vals=[canvas[r][c] for r,c in path if canvas[r][c] not in (0,color) and (variant!='only_new_paint_costs' or canvas[r][c]!=original[r][c]) and (variant!='ignore_nonpairs' or counts.get(canvas[r][c],0)==2)]
   if variant=='any_collision_cost':return int(bool(vals))
   if variant=='cap_two_cost':return min(2,len(vals))
   if variant=='distinct_colors_cost':return len(set(vals))
   return len(vals)
  hc,vc=cost(hv),cost(vh)
  tie=1 if variant=='tie_always_hv' else 2 if variant=='tie_always_vh' else 3-command if variant=='tie_opposite_command' else command
  if variant=='positive_tie_hv' and hc>0:tie=1
  if variant=='positive_tie_vh' and hc>0:tie=2
  chosen=command
  if actual_mode=='avoid_painted' and not (variant=='avoid_first_two_only' and ix>=2) and not (variant=='first_pair_command' and ix==0):
   if hc==vc:chosen=tie
   elif variant=='maximum_collision_cost':chosen=1 if hc>vc else 2
   else:chosen=1 if hc<vc else 2
   if variant=='flip_if_command_collides':chosen=3-command if (hc if command==1 else vc) else command
  if variant=='always_hv':chosen=1
  if variant=='always_vh':chosen=2
  path=hv if chosen==1 else vh
  if variant in ('first_leg_only','second_leg_only'):path=_legs(a,b,chosen)[variant=='second_leg_only']
  before=[row[:] for row in out];previous=[row[:] for row in original]
  for r,c in path:
   if variant=='protect_input_markers' and original[r][c] not in (0,color):continue
   if variant=='paint_background_only' and out[r][c]!=0:continue
   out[r][c]=color;previous[r][c]=color
  if trace:records.append({'color':color,'index':ix,'endpoints':[list(a),list(b)],'hv_cost':hc,'vh_cost':vc,'chosen':chosen,'changed_cells':sum(x!=y for row0,row1 in zip(before,out) for x,y in zip(row0,row1)),'input_costs':[sum(original[r][c] not in (0,color) for r,c in p) for p in (hv,vh)]})
 if variant in ('drop_singletons','drop_nonpairs'):
  for color in palette:
   if (counts[color]==1 if variant=='drop_singletons' else counts[color]!=2):
    for r,c in _positions(original,color):out[r][c]=0
 if variant=='clear_command':out[0][0]=0
 if variant=='restore_command':out[0][0]=original[0][0]
 return (out,records) if trace else out

def intended(grid,mode):return _predict(grid,mode)
def RIVAL_NAMES(mode):return _COMMON+(_COMMAND if _mode(mode)=='command' else _AVOID)
def bank(mode)->dict[str,Callable]:return {name:partial(_predict,mode=_mode(mode),variant=name) for name in RIVAL_NAMES(mode)}

def feature_summary(grid,mode):
 output,routes=_predict(grid,mode,trace=True)
 return {'height':len(grid),'width':len(grid[0]),'command':grid[0][0],'nonzero_input':sum(v!=0 for row in grid for v in row),'nonzero_output':sum(v!=0 for row in output for v in row),'changed_cells':sum(a!=b for ra,rb in zip(grid,output) for a,b in zip(ra,rb)),'pair_count':len(routes),'routes':routes}

def fixtures():
 def make(h,w,command,markers):
  g=[[0]*w for _ in range(h)];g[0][0]=command
  for color,cells in markers.items():
   for r,c in cells:g[r][c]=color
  return g
 first=make(5,5,1,{3:[(1,1),(3,3)],4:[(2,1),(4,4)]})
 second=[list(row) for row in zip(*first)];second[0][0]=2
 return {'single':[[1]],'sequential_cmd1':first,'sequential_cmd2':second,
 'marker_overwrite':make(7,7,1,{8:[(1,1),(5,5)],3:[(1,3),(6,4)],6:[(2,1),(6,2)],9:[(3,6)]}),
 'clutter':make(8,9,2,{8:[(0,2),(6,7)],3:[(1,3),(6,3)],6:[(2,8),(7,1)],4:[(3,2),(3,3),(3,4)],9:[(7,8)]}),
 'counts_and_order':make(10,11,1,{8:[(0,5),(8,2)],3:[(1,8),(7,1)],9:[(2,2),(9,9)],4:[(3,7),(8,8)],7:[(4,0),(4,10)],2:[(5,4),(7,4)],6:[(6,6)],5:[(0,9),(0,10),(9,0)]}),
 'edge_alignment':make(6,8,2,{7:[(0,3),(5,3)],3:[(1,7),(5,0)],8:[(2,0),(2,6)],9:[(3,1),(5,6)],4:[(4,2)]})}

@lru_cache(maxsize=None)
def racket(mode,name=None):
 """Independent full executable program; source is never copied from prototype."""
 _mode(mode)
 if name is not None and name not in RIVAL_NAMES(mode) and name!='reverse_endpoints':raise ValueError(f'unknown rival {mode}/{name}')
 mode='avoid_painted' if name=='avoid_painted_setting' else 'command' if name=='command_setting' else mode
 def yes(*names):return '#t' if name in names else '#f'
 order='(sort colors <)' if name=='numeric_color_order' else '(sort colors >)' if name=='descending_color_order' else '(reverse colors)' if name=='reverse_color_order' else 'colors'
 cmd='(if (odd? (length colors)) 1 2)' if name=='color_count_parity_command' else '(if (odd? pair-count) 1 2)' if name=='paired_count_parity_command' else '(if (or (= pair-count 6) (= (length (filter (lambda (v) (= (length (find-color g v)) 1)) colors)) 2)) 2 1)' if name=='profile_command' else '(- 3 (at g 0 0))' if name=='swap_command' else '(at g 0 0)'
 tie='1' if name=='tie_always_hv' else '2' if name=='tie_always_vh' else '(- 3 command)' if name=='tie_opposite_command' else '(if (> hc 0) 1 command)' if name=='positive_tie_hv' else '(if (> hc 0) 2 command)' if name=='positive_tie_vh' else 'command'
 canvas='g' if name=='original_canvas_costs' else 'previous' if name=='previous_canvas_costs' else 'out'
 count='(if (empty? vals) 0 1)' if name=='any_collision_cost' else '(length (remove-duplicates vals))' if name=='distinct_colors_cost' else '(min 2 (length vals))' if name=='cap_two_cost' else '(length vals)'
 if name=='noop':return '(rule! (lambda (input) input))'
 return f'''(rule!
(let ()
 (define cleared (set-cell g 0 0 0))
 (define colors
  (remove-duplicates
   (filter (lambda (v) (not (= v 0)))
    (map (lambda (p) (at cleared (first p) (second p))) (grid-positions g)))))
 (define ordered {order})
 (define pair-count (length (filter (lambda (v) (= (length (find-color g v)) 2)) colors)))
 (define command {cmd})
 (define (legs a b orientation)
  (let* ((ar (first a)) (ac (second a)) (br (first b)) (bc (second b))
         (rs (if (>= br ar) 1 -1)) (cs (if (>= bc ac) 1 -1)))
   (if (= orientation 1)
    (list (for/list ((c (in-range ac (+ bc cs) cs))) (list ar c))
          (for/list ((r (in-range ar (+ br rs) rs))) (list r bc)))
    (list (for/list ((r (in-range ar (+ br rs) rs))) (list r ac))
          (for/list ((c (in-range ac (+ bc cs) cs))) (list br c))))))
 (define (path a b orientation)
  (let ((parts (legs a b orientation)))
   (remove-duplicates (append (first parts) (second parts)))))
 (define (cost canvas cells color)
  (let ((vals
   (for/list ((p (in-list cells)) #:when
    (and (not (= (at canvas (first p) (second p)) 0))
         (not (= (at canvas (first p) (second p)) color))
         (or (not {yes('ignore_nonpairs')}) (= (length (find-color g (at canvas (first p) (second p)))) 2))
         (or (not {yes('only_new_paint_costs')})
             (not (= (at canvas (first p) (second p)) (at g (first p) (second p)))))))
    (at canvas (first p) (second p)))))
   {count}))
 (define (eligible cells)
  (if {yes('at_least_two_markers','first_last_markers')} (>= (length cells) 2) (= (length cells) 2)))
 (define (edge p)
  (or (= (first p) 0) (= (second p) 0)
      (= (first p) (- (length g) 1)) (= (second p) (- (length (first g)) 1))))
 (define (can-paint before p color)
  (not (or
   (and {yes('protect_input_markers')} (not (= (at g (first p) (second p)) 0)) (not (= (at g (first p) (second p)) color)))
   (and {yes('paint_background_only')} (not (= (at before (first p) (second p)) 0))))))
 (define (paint canvas before cells color)
  (for/fold ((result canvas)) ((p (in-list cells)))
   (if (can-paint before p color) (set-cell result (first p) (second p) color) result)))
 (define after
  (for/fold ((state (list g 0 g))) ((color (in-list ordered)))
   (let* ((out (first state)) (index (second state)) (previous (third state))
          (orig (find-color g color)))
    (if (not (eligible orig)) state
     (let* ((cells (if {yes('current_canvas_markers')} (find-color out color) orig))
            (next-index (+ index 1)) (skipped (list out next-index previous)))
      (if (< (length cells) 2) skipped
       (let* ((aa (first cells)) (bb (if {yes('first_last_markers')} (last cells) (second cells)))
              (a (if {yes('reverse_endpoints')} bb aa)) (b (if {yes('reverse_endpoints')} aa bb)))
        (if (or
             (and {yes('first_pair_only')} (>= index 1))
             (and {yes('first_two_pairs')} (>= index 2))
             (and {yes('first_four_pairs')} (>= index 4))
             (and {yes('last_pair_only')} (not (= index (- pair-count 1))))
             (and {yes('skip_aligned')} (or (= (first a) (first b)) (= (second a) (second b))))
             (and {yes('skip_edge_endpoints')} (or (edge a) (edge b))))
         skipped
         (let* ((hv (path a b 1)) (vh (path a b 2))
                (hc (cost {canvas} hv color)) (vc (cost {canvas} vh color))
                (picked
                 (if (and {'#t' if mode=='avoid_painted' else '#f'}
                          (not (and {yes('avoid_first_two_only')} (>= index 2)))
                          (not (and {yes('first_pair_command')} (= index 0))))
                  (if (= hc vc) {tie}
                   (if {yes('maximum_collision_cost')} (if (> hc vc) 1 2) (if (< hc vc) 1 2)))
                  command))
                (flipped
                 (if {yes('flip_if_command_collides')}
                  (if (> (if (= command 1) hc vc) 0) (- 3 command) command) picked))
                (chosen (if {yes('always_hv')} 1 (if {yes('always_vh')} 2 flipped)))
                (full (if (= chosen 1) hv vh)) (parts (legs a b chosen))
                (route (if {yes('first_leg_only')} (first parts) (if {yes('second_leg_only')} (second parts) full))))
          (list (paint out out route color) next-index (paint g out route color)))))))))))
 (define drawn (first after))
 (define cleaned
  (if {yes('drop_singletons','drop_nonpairs')}
   (for/fold ((out drawn)) ((color (in-list colors)))
    (let ((cells (find-color g color)))
     (if (if {yes('drop_singletons')} (= (length cells) 1) (not (= (length cells) 2)))
      (for/fold ((result out)) ((p (in-list cells)))
       (set-cell result (first p) (second p) 0)) out))) drawn))
 (if {yes('restore_command')} (set-cell cleaned 0 0 (at g 0 0))
  (if {yes('clear_command')} (set-cell cleaned 0 0 0) cleaned))))'''

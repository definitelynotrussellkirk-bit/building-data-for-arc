"""Finite semantic competitors: direction, collision state, and processing order."""
from pathlib import Path
BASE=Path(__file__).resolve().parent

def patch(text,old,new):
    if text.count(old)!=1:raise ValueError(f'Rival patch mismatch: {old}')
    return text.replace(old,new)

FRONT='''(if (= (second a) (second b)) (< (first a) (first b))
      (if left? (< (second a) (second b)) (> (second a) (second b))))'''
TOP='''(if (= (first a) (first b))
      (if left? (< (second a) (second b)) (> (second a) (second b)))
      (< (first a) (first b)))'''
BACK='''(if (= (second a) (second b)) (< (first a) (first b))
      (if left? (> (second a) (second b)) (< (second a) (second b))))'''
BOTTOM=TOP.replace('(< (first a) (first b))','(> (first a) (first b))')
SIZE='''(if (= (* (third a) (fourth a)) (* (third b) (fourth b)))
      (if left? (< (second a) (second b)) (> (second a) (second b)))
      (> (* (third a) (fourth a)) (* (third b) (fourth b))))'''

def programs(mode):
    if mode not in ('front_first','top_first'):raise ValueError('Unknown setting')
    front=(BASE/'canonical.rkt').read_text();top=(BASE/'top_first.rkt').read_text()
    chosen,order=(front,FRONT) if mode=='front_first' else (top,TOP)
    edge='''(define placed
     (map (lambda (b) (list (first b)
          (if (= (list-ref b 4) 8) 0 (- (cols g) (fourth b)))
          (third b) (fourth b) (list-ref b 4) (list-ref b 5) (second b))) boxes))'''
    return {
       'other_declared_order':top if mode=='front_first' else front,
       'back_first':patch(chosen,order,BACK),
       'bottom_first':patch(chosen,order,BOTTOM),
       'largest_area_first':patch(chosen,order,SIZE),
       'raw_obstacles':patch(chosen,'(define (settled-col o) (second o))','(define (settled-col o) (list-ref o 6))'),
       'edge_only':patch(chosen,'(define placed (append (pack 8 #t) (pack 2 #f)))',edge),
       'swap_sides':patch(chosen,'(append (pack 8 #t) (pack 2 #f))','(append (pack 8 #f) (pack 2 #t))'),
       'all_left':patch(chosen,'(pack 2 #f)','(pack 2 #t)'),
       'touching_rows_overlap':patch(patch(chosen,'(< (first b) (+ (first p) (third p)))','(<= (first b) (+ (first p) (third p)))'),
                  '(< (first p) (+ (first b) (third b)))','(<= (first p) (+ (first b) (third b)))'),
       'always_5x5':patch(chosen,'(list r c (+ 1 (- rr r)) (+ 1 (- cc c)) (at g r c) (at g (+ r 1) (+ c 1)) c)',
                  '(list r c 5 5 (at g r c) (at g (+ r 1) (+ c 1)) c)'),
    }

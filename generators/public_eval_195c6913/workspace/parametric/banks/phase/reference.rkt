(rule!
 ;; Ordered 2x2 chips in the upper legend define a periodic color cycle.
 ;; The distinct lower chip gives the collision-mark color. Erase both legends.
 ;; Each left-edge start travels right through the dominant nonbackground terrain,
 ;; marking the first in-bounds obstruction, then alternates up and right.
 ;; A blocked prospective turn ends that trail; an edge exit has no collision mark.
 ;; Trace on immutable input. Each start begins at phase zero, corners count once,
 ;; and the cycle is continuous across turns. Independent trails are drawn top-first.
 (lambda (g)
  (let ()
   (define restart? #f)
   (define turn-tax 0)
   (define bg (at g 0 0))
   (define terrain (mode g bg))
   (define obs (objects g bg))
   (define chips (filter (lambda (o) (and (not (= (obj-color o) terrain))
                          (= (obj-size o) 4) (= (obj-h o) 2) (= (obj-w o) 2))) obs))
   (define top (apply min (map obj-r1 chips)))
   (define ordered (sort (filter (lambda (o) (= (obj-r1 o) top)) chips)
                         (lambda (a b) (< (obj-c1 a) (obj-c1 b)))))
   (define cycle (map obj-color ordered))
   (define stop-color (obj-color (first (filter (lambda (o) (> (obj-r1 o) top)) chips))))
   (define starts (sort (filter (lambda (o) (and (= (obj-size o) 1) (= (obj-c1 o) 0)
                                          (= (obj-color o) (first cycle)))) obs)
                        (lambda (a b) (< (obj-r1 a) (obj-r1 b)))))
   (define (inside r c) (and (<= 0 r) (< r (rows g)) (<= 0 c) (< c (cols g))))
   (define (passable r c) (and (inside r c) (= (at g r c) terrain)))
   ;; A: events contain kind, row, column, global step, post-turn segment step.
   (define (trace r c direction total local)
    (define current (list 0 r c total local))
    (define nr (+ r (if (= direction 0) 0 -1)))
    (define nc (+ c (if (= direction 0) 1 0)))
    (cond
     ((not (inside nr nc)) (list current))
     ((passable nr nc) (cons current (trace nr nc direction (+ total 1) (+ local 1))))
     (else
      (define marker (list 1 nr nc total local))
      (define next-dir (- 1 direction))
      (define tr (+ r (if (= next-dir 0) 0 -1)))
      (define tc (+ c (if (= next-dir 0) 1 0)))
      (if (passable tr tc)
          (append (list current marker) (trace tr tc next-dir (+ total 1 turn-tax) 0))
          (list current marker)))))
   (define paths (map (lambda (o) (trace (obj-r1 o) 0 0 0 0)) starts))
   (define cleaned (for/fold ((out g)) ((o chips)) (recolor-cells out (obj-cells o) bg)))
   ;; B: the geometry-derived indices select the cyclic colors, not grid coordinates.
   (for*/fold ((out cleaned)) ((path paths) (e path))
    (set-cell out (second e) (third e)
     (if (= (first e) 1) stop-color
         (list-ref cycle (modulo (list-ref e (if restart? 4 3)) (length cycle)))))))))

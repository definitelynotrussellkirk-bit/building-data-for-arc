(rule!
 ;; Two colored bars frame an interior picture. Match each bar to the outer
 ;; canvas side carrying its color, then rotate or reflect the whole picture.
 ;; The two adjacent markers specify orientation, including handedness.
 ;; Remove only the bars; preserve black notches and all picture colors.
 ;; Outer edges may be irregular: use their marker-color counts, not a corner.
 (lambda (g)
  (let ()
   (define swap-markers? #f)
   (define height (rows g))
   (define width (cols g))
   (define binary (map-grid g (lambda (r c v) (if (= v 0) 0 1))))
   (define interior
    (first (filter
     (lambda (o) (and (> (obj-r1 o) 0) (> (obj-c1 o) 0)
                      (< (obj-r2 o) (- height 1)) (< (obj-c2 o) (- width 1))))
     (objects binary 0))))
   (define rlo (obj-r1 interior))
   (define clo (obj-c1 interior))
   (define rhi (obj-r2 interior))
   (define chi (obj-c2 interior))
   (define (edge side)
    (cond
     [(= side 0) (for/list ([c (range 1 (- width 1))]) (at g 0 c))]
     [(= side 1) (for/list ([r (range 1 (- height 1))]) (at g r (- width 1)))]
     [(= side 2) (for/list ([c (range 1 (- width 1))]) (at g (- height 1) c))]
     [else (for/list ([r (range 1 (- height 1))]) (at g r 0))]))
   (define border-values (append (edge 0) (edge 1) (edge 2) (edge 3)))
   (define marker-colors
    (for/list ([color (range 1 10)]
     #:when (and (member color border-values)
                 (for*/or ([r (range rlo (+ rhi 1))] [c (range clo (+ chi 1))])
                  (= (at g r c) color)))) color))
   (define (inner-side color)
    (define cells
     (for*/list ([r (range rlo (+ rhi 1))] [c (range clo (+ chi 1))]
      #:when (= (at g r c) color)) (list r c)))
    (cond
     [(andmap (lambda (p) (= (first p) rlo)) cells) 0]
     [(andmap (lambda (p) (= (second p) chi)) cells) 1]
     [(andmap (lambda (p) (= (first p) rhi)) cells) 2]
     [else 3]))
   (define inner-sides (map inner-side marker-colors))
   (define (outer-side color)
    (pick-max (range 0 4)
     (lambda (side) (count (lambda (v) (= v color)) (edge side)))))
   (define outer-sides (map outer-side marker-colors))
   (define target-sides (if swap-markers? (reverse outer-sides) outer-sides))
   (define picture
    (subgrid g (+ rlo (if (member 0 inner-sides) 1 0))
               (+ clo (if (member 3 inner-sides) 1 0))
               (- rhi (if (member 2 inner-sides) 1 0))
               (- chi (if (member 1 inner-sides) 1 0))))
   (define side-maps
    '((0 1 2 3) (1 2 3 0) (2 3 0 1) (3 0 1 2)
      (0 3 2 1) (2 1 0 3) (3 2 1 0) (1 0 3 2)))
   (define chosen-transform
    (for/first ([k (range 0 8)]
     #:when (equal? (map (lambda (side) (list-ref (list-ref side-maps k) side)) inner-sides)
                    target-sides)) k))
   (define oriented (cond
    [(= chosen-transform 0) picture]
    [(= chosen-transform 1) (rotate-cw picture)]
    [(= chosen-transform 2) (rotate-180 picture)]
    [(= chosen-transform 3) (rotate-ccw picture)]
    [(= chosen-transform 4) (flip-lr picture)]
    [(= chosen-transform 5) (flip-ud picture)]
    [(= chosen-transform 6) (transpose picture)]
    [else (rotate-180 (transpose picture))]))
   (define fill (mode oriented 0))
   (for/fold ((out oriented)) ((o (in-list (objects oriented -1))) #:when (and (= (obj-color o) 0) (= (obj-r1 o) 0)))
    (paint-cells out (obj-cells o) fill)))))

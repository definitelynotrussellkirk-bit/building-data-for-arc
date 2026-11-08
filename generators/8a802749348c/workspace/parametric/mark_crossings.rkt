(rule!
  (let ()
    (define (has-cell? cells r c)
      (member? (list r c) cells))
    (define (paint-ray out color r c dr dc)
      (let loop ([acc out] [rr (+ r dr)] [cc (+ c dc)])
        (if (in-bounds? rr cc (rows g) (cols g))
            (loop (set-cell acc rr cc color) (+ rr dr) (+ cc dc))
            acc)))
    (define (paint-l out obj)
      (let* ([cells (obj-cells obj)]
             [bb (obj-bbox obj)]
             [r0 (first bb)]
             [c0 (second bb)]
             [color (obj-color obj)]
             [misses
              (filter (lambda (p) (not (has-cell? cells (first p) (second p))))
                      (list (list r0 c0)
                            (list r0 (+ c0 1))
                            (list (+ r0 1) c0)
                            (list (+ r0 1) (+ c0 1))))])
        (if (empty? misses)
            out
            (let* ([m (first misses)]
                   [mr (first m)]
                   [mc (second m)]
                   [corner-r (if (= mr r0) (+ r0 1) r0)]
                   [corner-c (if (= mc c0) (+ c0 1) c0)]
                   [dr (- mr corner-r)]
                   [dc (- mc corner-c)])
              (paint-ray out color mr mc dr dc)))))
    (define stage
      (for/fold ([out g])
                ([obj (in-list (filter (lambda (o) (= (obj-size o) 3))
                                       (objects g 0)))])
        (paint-l out obj)))
    (define (crossing? r c)
      (let ([v (at stage r c)])
        (and (= (at g r c) 0)
             (not (= v 0))
             (not (= v 9))
             (= (at stage (- r 1) (- c 1)) v)
             (= (at stage (- r 1) (+ c 1)) v)
             (= (at stage (+ r 1) (- c 1)) v)
             (= (at stage (+ r 1) (+ c 1)) v))))
    (for*/fold ([out stage])
               ([r (in-range 1 (- (rows g) 1))]
                [c (in-range 1 (- (cols g) 1))])
      (if (crossing? r c)
          (let* ([o1 (set-cell out r c 9)]
                 [o2 (set-cell o1 (- r 1) c 9)]
                 [o3 (set-cell o2 (+ r 1) c 9)]
                 [o4 (set-cell o3 r (- c 1) 9)])
            (set-cell o4 r (+ c 1) 9))
          out))))

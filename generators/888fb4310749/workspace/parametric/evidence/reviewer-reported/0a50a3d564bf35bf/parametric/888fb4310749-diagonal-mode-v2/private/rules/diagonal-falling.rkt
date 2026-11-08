(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define cells (positions-of g (lambda (v) (!= v 0))))
             (define r0 (min-of first cells))
             (define r1 (max-of first cells))
             (define c0 (min-of second cells))
             (define c1 (max-of second cells))
             (define bh (+ 1 (- r1 r0)))
             (define bw (+ 1 (- c1 c0)))
             (define step (+ bh bw))
             (define color (at g r0 c0))
             (define alt (- 9 color))
             (define (intersects? rr cc hh ww)
               (and
                 (<= rr (- h 1))
                 (>= (+ rr hh -1) 0)
                 (<= cc (- w 1))
                 (>= (+ cc ww -1) 0)))
             (define (stamp-rect out rr cc hh ww v)
               (for*/fold ((acc out))
                          ((r (range rr (+ rr hh))) (c (range cc (+ cc ww)))
                            #:when
                            (in-bounds? r c h w))
                          (set-cell acc r c v)))
             (define same-anchors
               (remove-duplicates (filter identity
                                          (flatmap (lambda (k)
                                                     (map (lambda (sgn)
                                                            (let ((rr (+ r0 (* k step)))
                                                                  (cc (+ c0
                                                                         (* sgn k step))))
                                                              (and
                                                                (intersects? rr
                                                                             cc
                                                                             bh
                                                                             bw)
                                                                (list rr cc))))
                                                          (list 1)))
                                                   (range -40 41)))))
             (define with-rotated
               (for*/fold ((out g))
                          ((k (range -40 41)) (sgn (list 1)))
                          (let* ((rr (+ r0 (* k step)))
                                 (cc (+ c0 (* sgn k step)))
                                 (ar (+ rr bh))
                                 (ac (+ cc (if (= sgn 1) bw (- bh)))))
                            (if (intersects? ar ac bw bh)
                                (stamp-rect out ar ac bw bh alt)
                                out))))
             (for/fold ((out with-rotated))
               ((p same-anchors))
               (stamp-rect out (first p) (second p) bh bw color))))))
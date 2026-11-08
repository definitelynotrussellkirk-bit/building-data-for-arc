(rule!
 ;; Discover maximal consecutive bands of fully uniform rows, irrespective
 ;; of the colors used in adjacent rows. Keep every longest band, including
 ;; ties, in gray. All other rows become black. An all-mixed grid is black.
 (lambda (g)
   (let ()
     (define mask
       (for/list ((r (range 0 (rows g))))
         (= 1 (length (unique (row-at g r))))))
     (define (walk r step)
       (if (and (>= r 0) (< r (rows g)) (list-ref mask r))
           (+ 1 (walk (+ r step) step))
           0))
     (define lengths
       (for/list ((r (range 0 (rows g))))
         (if (list-ref mask r)
             (- (+ (walk r -1) (walk r 1)) 1)
             0)))
     (define longest (apply max lengths))
     (cellmap g (r c v)
       (if (and (> longest 0) (= (list-ref lengths r) longest)) 5 0)))))

(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define square-center
               (find-first (lambda (p)
                             (let* ((r (first p))
                                    (c (second p))
                                    (v (at g r c)))
                               (and
                                 (!= v 0)
                                 (!= v 4)
                                 (!= v 5)
                                 (for*/and ((dr (list -1 0 1)) (dc (list -1 0 1))
                                             #:when
                                             (not (and (zero? dr) (zero? dc))))
                                           (= (safe-at g (+ r dr) (+ c dc) -1) 4)))))
                           (grid-positions g)))
             (define sr (first square-center))
             (define sc (second square-center))
             (define color (at g sr sc))
             (define indicator
               (find-first (lambda (p) (not (equal? p square-center)))
                           (positions-of g (lambda (v) (= v color)))))
             (define square-border
               (filter (lambda (p) (not (and (= (first p) sr) (= (second p) sc))))
                       (positions-in-rect (- sr 1) (- sc 1) (+ sr 1) (+ sc 1))))
             (define extra4
               (find-first (lambda (p) (not (member p square-border)))
                           (positions-of g (lambda (v) (= v 4)))))
             (define dr (- (first extra4) (first indicator)))
             (define dc (- (second extra4) (second indicator)))
             (define nr (+ sr (* 1 (- dc))))
             (define nc (+ sc (* 1 dr)))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (= r nr) (= c nc)) color)
                        ((and
                           (>= r (- nr 1))
                           (<= r (+ nr 1))
                           (>= c (- nc 1))
                           (<= c (+ nc 1))) 4)
                        ((or (= (- r c) (- nr nc)) (= (+ r c) (+ nr nc))) 4)
                        (else color)))))))
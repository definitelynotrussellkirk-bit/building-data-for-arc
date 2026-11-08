(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define (rect-cells r c) (positions-in-rect r c (+ r 2) (+ c 2)))
             (define (all-2-or-5? cells)
               (for/and ((p cells))
                        (let ((v (at g (first p) (second p)))) (or (= v 2) (= v 5)))))
             (define candidates
               (sort (filter identity
                             (for*/list ((r (range 0 (- h 2))) (c (range 0 (- w 2))))
                               (let* ((cells (rect-cells r c))
                                      (covered-twos (filter (lambda (p)
                                                              (= (at g
                                                                     (first p)
                                                                     (second p))
                                                                 2))
                                                            cells)))
                                 (and
                                   (and
                                     (>= (length covered-twos) 2)
                                     (= (at g (+ r 1) (+ c 1)) 5)
                                     (all-2-or-5? cells))
                                   (list r c cells covered-twos (length covered-twos))))))
                     (lambda (a b)
                       (let ((ca (fifth a))
                             (cb (fifth b)))
                         (or
                           (> ca cb)
                           (and
                             (= ca cb)
                             (or
                               (< (first a) (first b))
                               (and (= (first a) (first b)) (< (second a) (second b))))))))))
             (define selected
               (let loop
                    ((cs candidates) (covered (list)) (sel (list)))
                    (if (empty? cs)
                        (reverse sel)
                        (let* ((cand (first cs))
                               (ctwos (fourth cand))
                               (overlap? (for/or ((p ctwos)) (member p covered))))
                          (if overlap?
                              (loop (rest cs) covered sel)
                              (loop (rest cs) (append covered ctwos) (cons cand sel)))))))
             (define (hit-cand r c)
               (find-first (lambda (cand) (member (list r c) (third cand))) selected))
             (cellmap g
                      (r c v)
                      (let ((cand (hit-cand r c)))
                        (if (and cand (= v 5))
                            (if (and (= r (+ (first cand) 1)) (= c (+ (second cand) 1)))
                                4
                                7)
                            v)))))))
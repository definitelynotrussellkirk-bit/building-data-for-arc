(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define (zero-rect? r0 c0 r1 c1)
               (all? (lambda (r)
                       (all? (lambda (c) (zero? (at g r c))) (range c0 (+ c1 1))))
                     (range r0 (+ r1 1))))
             (define rects
               (filter (lambda (x)
                         (zero-rect? (second x) (third x) (fourth x) (fifth x)))
                       (flatmap (lambda (r0)
                                  (flatmap (lambda (c0)
                                             (flatmap (lambda (r1)
                                                        (map (lambda (c1)
                                                               (list (* (+ 1 (- r1 r0))
                                                                        (+ 1 (- c1 c0)))
                                                                     r0
                                                                     c0
                                                                     r1
                                                                     c1))
                                                             (range (+ c0 2) w)))
                                                      (range (+ r0 2) h)))
                                           (range 0 w)))
                                (range 0 h))))
             (if (null? rects)
                 g
                 (let* ((best (first (sort rects
                                           (lambda (a b)
                                             (or
                                               (> (first a) (first b))
                                               (and
                                                 (= (first a) (first b))
                                                 (< (second a) (second b)))
                                               (and
                                                 (= (first a) (first b))
                                                 (= (second a) (second b))
                                                 (< (third a) (third b))))))))
                        (r0 (second best))
                        (c0 (third best))
                        (r1 (fourth best))
                        (c1 (fifth best)))
                   (reduce (lambda (acc r)
                             (reduce (lambda (a c) (set-cell a r c 8))
                                     acc
                                     (range (+ c0 1) c1)))
                           g
                           (range (+ r0 1) r1))))))))
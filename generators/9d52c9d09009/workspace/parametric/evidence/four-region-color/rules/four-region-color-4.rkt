(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define (hole-count obj)
               (define r1 (obj-r1 obj))
               (define r2 (obj-r2 obj))
               (define c1 (obj-c1 obj))
               (define c2 (obj-c2 obj))
               (define zeros
                 (for*/list ((r (range r1 (+ r2 1))) (c (range c1 (+ c2 1)))
                     #:when
                     (zero? (at g r c)))
                   (list r c)))
               (define visited (make-hash))
               (for/fold ((n 0))
                 ((p zeros))
                 (if (hash-has-key? visited p)
                     n
                     (begin
                       (for ((q (connected-region g
                                               (first p)
                                               (second p)
                                               (lambda (rr cc v)
                                                 (and
                                                   (zero? v)
                                                   (>= rr r1)
                                                   (<= rr r2)
                                                   (>= cc c1)
                                                   (<= cc c2)))
                                               4)))
                         (hash-set! visited q #t))
                       (+ n 1)))))
             (define (map-color n) (if (= n 4) 4 n))
             (for/fold ((out g))
               ((obj (filter (lambda (o) (= (obj-color o) 8)) (objects g 0))))
               (recolor-cells out (obj-cells obj) (map-color (hole-count obj))))))))
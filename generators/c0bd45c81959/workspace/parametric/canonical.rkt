(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((mode-block (lambda (r1 c1)
                               (let ((freq (make-hash))
                                     (best 0)
                                     (best-count -1))
                                 (for* ((r (range r1 (+ r1 3))) (c (range c1 (+ c1 2))))
                                       (let ((v (at g r c)))
                                         (when
                                           (!= v 0)
                                           (hash-set! freq v (+ 1 (hash-ref freq v 0))))))
                                 (hash-for-each freq
                                                (lambda (k v)
                                                  (when
                                                    (> v best-count)
                                                    (set! best k)
                                                    (set! best-count v))))
                                 best))))
             (build-grid 4
                         5
                         (r c)
                         (cond
                           ((or (zero? r) (= r 3) (zero? c) (= c 4)) 0)
                           (else (let* ((br (- r 1))
                                        (bc (- c 1))
                                        (block-r1 (+ 1 (* br 4)))
                                        (block-c1 (+ 1 (* bc 3))))
                                   (mode-block block-r1 block-c1)))))))))
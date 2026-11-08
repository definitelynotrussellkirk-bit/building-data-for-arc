(rule!
  (lambda (g)
    (let* ((h (rows g))
           (w (cols g))
           (three-objs
            (filter (lambda (o) (= (obj-color o) 3)) (objects g 0)))
           (interior-2s
            (apply append
                   (map
                    (lambda (o)
                      (with-bbox o (r1 c1 r2 c2)
                        (let ((valid
                               (for/and ((r (range r1 (+ r2 1))))
                                 (for/and ((c (range c1 (+ c2 1))))
                                   (let ((v (at g r c)))
                                     (or (= v 3) (= v 2)))))))
                          (if valid
                              (for*/list ((r (range r1 (+ r2 1)))
                                          (c (range c1 (+ c2 1)))
                                          #:when (= (at g r c) 2))
                                (list r c))
                              '()))))
                    three-objs)))
           (interior-set (make-hash))
           (_1 (for ((p interior-2s))
                  (hash-set! interior-set (list (first p) (second p)) #t)))
           ;; Stage A: execute the canonical halo transform.
           (intermediate
            (for/fold ((out g)) ((p interior-2s))
              (let ((pr (first p)) (pc (second p)))
                (for*/fold ((gg out))
                           ((dr (in-list '(-1 0 1)))
                            (dc (in-list '(-1 0 1))))
                  (let ((r (+ pr dr)) (c (+ pc dc)))
                    (cond ((or (< r 0) (>= r h) (< c 0) (>= c w)) gg)
                          ((hash-has-key? interior-set (list r c)) gg)
                          (else (set-cell gg r c 1))))))))
           ;; Stage B: component eligibility and size exist only in Stage A's output.
           (blue-objs
            (filter (lambda (o) (= (obj-color o) 1))
                    (objects intermediate 0)))
           (selected (pick-max blue-objs obj-size)))
      (if selected
          (recolor-cells intermediate (obj-cells selected) 8)
          intermediate))))

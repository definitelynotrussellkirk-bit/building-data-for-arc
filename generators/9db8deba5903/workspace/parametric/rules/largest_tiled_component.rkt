(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((n (rows g))
                  (mosaic
                   (build-grid (* n 2)
                               (* n 2)
                               (r c)
                               (let ((qr (/ r n))
                                     (qc (/ c n))
                                     (lr (mod r n))
                                     (lc (mod c n)))
                                 (cond
                                   ((and (zero? qr) (zero? qc))
                                    (at g lr lc))
                                   ((and (zero? qr) (= qc 1))
                                    (at g lc (- (- n 1) lr)))
                                   ((and (= qr 1) (zero? qc))
                                    (at g (- (- n 1) lr) (- (- n 1) lc)))
                                   (else
                                    (at g (- (- n 1) lc) lr))))))
                  (targets
                   (filter (lambda (obj) (= (obj-color obj) 1))
                           (objects mosaic 0)))
                  (largest
                   (first
                    (sort targets
                          (lambda (a b) (> (obj-size a) (obj-size b)))))))
             (paint-cells mosaic (obj-cells largest) 9)))))
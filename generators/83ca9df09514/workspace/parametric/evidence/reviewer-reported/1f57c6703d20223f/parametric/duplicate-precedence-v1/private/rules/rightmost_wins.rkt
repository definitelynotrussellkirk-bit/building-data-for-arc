(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((template-row (let loop
                                     ((r 0) (best-r 0) (best-cnt 0))
                                     (cond
                                       ((>= r h) best-r)
                                       (else (let ((cnt (count-if (lambda (c)
                                                                    (!= (at g r c) 0))
                                                                  (range 0 w))))
                                               (if (> cnt best-cnt)
                                                   (loop (+ r 1) r cnt)
                                                   (loop (+ r 1) best-r best-cnt)))))))
                  (template (for/list ((c (range 0 w))) (at g template-row c))))
             (cellmap g
                      (r c __cm_v)
                      (cond
                        ((= r template-row) __cm_v)
                        (else (let ((row-cells (for/list ((cc (range 0 w))) (at g r cc))))
                                (cond
                                  ((for/and ((v row-cells)) (zero? v)) 0)
                                  (else (let ((mapping (make-hash)))
                                          (for ((cc (range 0 w)))
                                            (when
                                              (!= (at g r cc) 0)
                                              (hash-set! mapping
                                                         (list-ref template cc)
                                                         (at g r cc))))
                                          (hash-ref mapping (list-ref template c) 0))))))))))))
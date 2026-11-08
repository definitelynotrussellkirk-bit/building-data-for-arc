(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((all-objs (objects g 0))
                  (frame (let loop
                              ((objs all-objs))
                              (cond
                                ((null? objs) #f)
                                (else (let* ((o (car objs)))
                                        (with-bbox o
                                                   (r1 c1 r2 c2)
                                                   (let* ((cells (obj-cells o))
                                                          (cell-set (make-hash))
                                                          (_1 (for ((c cells))
                                                                (hash-set! cell-set
                                                                           (list (first c)
                                                                                 (second c))
                                                                           #t)))
                                                          (is-frame (and
                                                                      (> (- r2 r1) 2)
                                                                      (> (- c2 c1) 2)
                                                                      (for*/and ((r (range r1
                                                                                           (+ r2
                                                                                              1))) (c (range c1
                                                                                            (+ c2
                                                                                               1)))
                                                                                  #:when
                                                                                  (or
                                                                                    (= r
                                                                                       r1)
                                                                                    (= r
                                                                                       r2)
                                                                                    (= c
                                                                                       c1)
                                                                                    (= c
                                                                                       c2)))
                                                                                (hash-has-key? cell-set
                                                                                               (list r
                                                                                                     c))))))
                                                     (cond
                                                       (is-frame o)
                                                       (else (loop (cdr objs)))))))))))
                  (frame-color (obj-color frame)))
             (with-bbox frame
                        (fr1 fc1 fr2 fc2)
                        (let* ((frame-h (+ 1 (- fr2 fr1)))
                               (frame-w (+ 1 (- fc2 fc1)))
                               (interior-h (- frame-h 2))
                               (interior-w (- frame-w 2))
                               (all-marker-cells (for*/list ((r (range 0 h)) (c (range 0 w))
                                                     #:when
                                                     (and
                                                       (!= (at g r c) 0)
                                                       (!= (at g r c) frame-color)))
                                                   (list r c (at g r c))))
                               (marker-color (third (first all-marker-cells)))
                               (mr1 (min-of first all-marker-cells))
                               (mr2 (max-of first all-marker-cells))
                               (mc1 (min-of second all-marker-cells))
                               (mc2 (max-of second all-marker-cells))
                               (marker-h (+ 1 (- mr2 mr1)))
                               (marker-w (+ 1 (- mc2 mc1)))
                               (marker-set (make-hash))
                               (_2 (for ((c all-marker-cells))
                                     (hash-set! marker-set
                                                (list (- (first c) mr1)
                                                      (- (second c) mc1))
                                                #t)))
                               (scale-h (quotient interior-h marker-h))
                               (scale-w (quotient interior-w marker-w))
                               (base (build-grid frame-h frame-w (r c) 0))
                               (g1 (for/fold ((out base))
                                     ((cell (obj-cells frame)))
                                     (set-cell out
                                               (- (first cell) fr1)
                                               (- (second cell) fc1)
                                               frame-color))))
                          (for*/fold ((out g1))
                                     ((ir (range 0 interior-h)) (ic (range 0 interior-w)))
                                     (let* ((mr (quotient ir scale-h))
                                            (mc (quotient ic scale-w)))
                                       (cond
                                         ((hash-has-key? marker-set (list (- marker-h 1 mr) mc)) (set-cell out (+ 1 ir) (+ 1 ic) marker-color))
                                         (else out))))))))))
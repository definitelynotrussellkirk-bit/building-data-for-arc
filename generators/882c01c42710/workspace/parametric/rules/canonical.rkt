(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (row-counts (make-hash))
                  (col-counts (make-hash))
                  (dummy (for* ((r (range 0 hh)) (c (range 0 ww)))
                               (when
                                 (!= (at g r c) 0)
                                 (hash-set! row-counts
                                            r
                                            (+ 1 (hash-ref row-counts r 0)))
                                 (hash-set! col-counts
                                            c
                                            (+ 1 (hash-ref col-counts c 0))))))
                  (center-row #f)
                  (center-col #f)
                  (max-r 0)
                  (max-c 0)
                  (dummy2 (hash-for-each row-counts
                                         (lambda (k v)
                                           (when
                                             (> v max-r)
                                             (set! max-r v)
                                             (set! center-row k)))))
                  (dummy3 (hash-for-each col-counts
                                         (lambda (k v)
                                           (when
                                             (> v max-c)
                                             (set! max-c v)
                                             (set! center-col k)))))
                  (v-seq (for/list ((r (range 0 hh)) #:when (!= (at g r center-col) 0))
                           (at g r center-col)))
                  (v-start (let loop
                                ((r 0))
                                (if (!= (at g r center-col) 0) r (loop (+ r 1)))))
                  (v-period (length v-seq))
                  (h-seq (for/list ((c (range 0 ww)) #:when (!= (at g center-row c) 0))
                           (at g center-row c)))
                  (h-start (let loop
                                ((c 0))
                                (if (!= (at g center-row c) 0) c (loop (+ c 1)))))
                  (h-period (length h-seq))
                  (result (make-hash)))
             (for* ((r (range 0 hh)) (c (range 0 ww)))
                   (hash-set! result (list r c) (at g r c)))
             (for ((r (range 0 hh)))
               (hash-set! result
                          (list r center-col)
                          (list-ref v-seq
                                    (remainder (+ v-period
                                                  (remainder (- r v-start) v-period))
                                               v-period))))
             (for ((c (range 0 ww)))
               (hash-set! result
                          (list center-row c)
                          (list-ref h-seq
                                    (remainder (+ h-period
                                                  (remainder (- c h-start) h-period))
                                               h-period))))
             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))
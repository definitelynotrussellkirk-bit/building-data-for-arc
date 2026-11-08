(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define pts (filter (lambda (cell) (!= (third cell) 0)) (grid-cells g)))
             (define (put gg r c v) (if (in-bounds? r c h w) (set-cell gg r c v) gg))
             (define vsegments
               (filter identity
                       (map (lambda (p)
                              (let ((r (first p))
                                    (c (second p))
                                    (v (third p)))
                                (cond
                                  ((= v 6) (list c (- r 6) r))
                                  ((= v 3) (list c r (+ r 3)))
                                  (else #f))))
                            pts)))
             (define after-vertical
               (for/fold ((out g))
                 ((seg vsegments))
                 (let ((c (first seg))
                       (top (second seg))
                       (bot (third seg)))
                   (for/fold ((gg out))
                     ((rr (range top (+ bot 1))))
                     (put gg
                          rr
                          c
                          (if (or (= rr top) (= rr bot)) (if (= (- bot top) 6) 6 3) 5))))))
             (define after-one
               (for/fold ((out after-vertical))
                 ((p pts))
                 (let ((r (first p))
                       (c (second p))
                       (v (third p)))
                   (if (= v 1)
                       (put (put (put (put out (- r 1) (+ c 2) 1) r c 1) r (+ c 1) 5)
                            r
                            (+ c 2)
                            5)
                       out))))
             (define (segment-at c)
               (find-first (lambda (seg) (= (first seg) c)) vsegments))
             (define expanded
               (for/fold ((out after-one))
                 ((p pts))
                 (let ((r (first p))
                       (c (second p))
                       (v (third p)))
                   (if (!= v 2)
                       out
                       (let* ((left-cols (map second
                                              (filter (lambda (q)
                                                        (and
                                                          (!= (third q) 2)
                                                          (< (second q) c)))
                                                      pts)))
                              (center (if (null? left-cols) (- c 1) (max-list left-cols)))
                              (seg (segment-at center))
                              (horiz (for/fold ((gg out))
                                       ((cc (range (- center 2) (+ center 3))))
                                       (put gg
                                            r
                                            cc
                                            (if (or
                                                  (= cc (- center 2))
                                                  (= cc (+ center 2)))
                                                2
                                                5)))))
                         (if (and seg (< (second seg) r) (< r (third seg)))
                             (for/fold ((gg horiz))
                               ((k (range 0 (max h w))))
                               (put gg (+ r k) (- center k) 4))
                             horiz))))))
             (define yellows
               (filter (lambda (cell) (= (third cell) 4)) (grid-cells expanded)))
             (define (payload-color cell)
               (find-first (lambda (value) (or (= value 7) (= value 9)))
                           (neighbors-8 expanded (first cell) (second cell) -1)))
             (define hit (find-first (lambda (cell) (payload-color cell)) yellows))
             (define target (if hit (payload-color hit) #f))
             (if target
                 (for/fold ((out expanded))
                   ((cell (grid-cells expanded)))
                   (if (= (third cell) target)
                       (set-cell out (first cell) (second cell) 8)
                       out))
                 expanded)))))

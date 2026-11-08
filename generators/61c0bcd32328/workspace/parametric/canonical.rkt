(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg (mode g 0))
                  (comps (objects g bg))
                  (corner-shapes (filter (lambda (x) x)
                                         (map (lambda (o)
                                                (with-bbox o
                                                           (r1 c1 r2 c2)
                                                           (let* ((corner (cond
                                                                            ((and
                                                                               (zero? r1)
                                                                               (zero? c1)) 'tl)
                                                                            ((and
                                                                               (zero? r1)
                                                                               (= c2
                                                                                  (- w
                                                                                     1))) 'tr)
                                                                            ((and
                                                                               (= r2
                                                                                  (- h
                                                                                     1))
                                                                               (= c2
                                                                                  (- w
                                                                                     1))) 'br)
                                                                            ((and
                                                                               (= r2
                                                                                  (- h
                                                                                     1))
                                                                               (zero? c1)) 'bl)
                                                                            (else #f))))
                                                             (cond
                                                               (corner (list corner o))
                                                               (else #f)))))
                                              comps)))
                  (new-cells (apply append
                                    (map (lambda (cs)
                                           (let* ((corner (first cs))
                                                  (o (second cs))
                                                  (cells (obj-cells o))
                                                  (col (obj-color o)))
                                             (with-bbox o
                                                        (r1 c1 r2 c2)
                                                        (let* ((dr (cond
                                                                     ((eq? corner 'tl) 0)
                                                                     ((eq? corner 'tr) (- h 1 r2))
                                                                     ((eq? corner 'br) 0)
                                                                     ((eq? corner 'bl) (- 0 r1))))
                                                               (dc (cond
                                                                     ((eq? corner 'tl) (- w 1 c2))
                                                                     ((eq? corner 'tr) 0)
                                                                     ((eq? corner 'br) (- 0 c1))
                                                                     ((eq? corner 'bl) 0))))
                                                          (map (lambda (cell)
                                                                 (list (+ (first cell)
                                                                          dr)
                                                                       (+ (second cell)
                                                                          dc)
                                                                       col))
                                                               cells)))))
                                         corner-shapes))))
             (for/fold ((out g))
               ((nc new-cells))
               (let ((r (first nc))
                     (c (second nc))
                     (col (third nc)))
                 (cond
                   ((or (< r 0) (>= r h) (< c 0) (>= c w)) out)
                   (else (set-cell out r c col)))))))))
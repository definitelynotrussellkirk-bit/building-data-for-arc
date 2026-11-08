(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (filled
           (cellmap g
                    (r c v)
                    (let ((nz (filter (lambda (x) (!= x 5))
                                      (map (lambda (cc) (at g r cc))
                                           (range 0 w)))))
                      (if (and (= 5 v) (not (null? nz)))
                          (first nz)
                          v)))))
    (cellmap filled
             (r c v)
             (if (= v 0)
                 (let* ((signal-rows
                          (filter
                            (lambda (rr)
                              (let ((x (at filled rr c)))
                                (and (!= x 0) (!= x 5))))
                            (range 0 h)))
                        (signal-values
                          (remove-duplicates
                            (map (lambda (rr) (at filled rr c))
                                 signal-rows))))
                   (if (and (>= (length signal-rows) 2)
                            (= (length signal-values) 1)
                            (> r (first signal-rows))
                            (< r (last signal-rows)))
                       (first signal-values)
                       v))
                 v)))))

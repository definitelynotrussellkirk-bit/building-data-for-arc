(rule! (lambda (g)
  (let* ((stage-a ((lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((yellows (find-color g 4))
                  (rs (sort (remove-duplicates (map first yellows)) <))
                  (cs (sort (remove-duplicates (map second yellows)) <))
                  (rectangles (filter (lambda (rec) rec)
                                      (flatmap (lambda (r1)
                                                 (flatmap (lambda (r2)
                                                            (flatmap (lambda (c1)
                                                                       (map (lambda (c2)
                                                                              (and
                                                                                (and
                                                                                  (< r1
                                                                                     r2)
                                                                                  (< c1
                                                                                     c2)
                                                                                  (member (list r1
                                                                                                c1)
                                                                                          yellows)
                                                                                  (member (list r1
                                                                                                c2)
                                                                                          yellows)
                                                                                  (member (list r2
                                                                                                c1)
                                                                                          yellows)
                                                                                  (member (list r2
                                                                                                c2)
                                                                                          yellows))
                                                                                (list r1
                                                                                      c1
                                                                                      r2
                                                                                      c2)))
                                                                            cs))
                                                                     cs))
                                                          rs))
                                               rs))))
             (foldl (lambda (rec acc)
                      (let ((r1 (first rec))
                            (c1 (second rec))
                            (r2 (third rec))
                            (c2 (fourth rec)))
                        (cellmap g
                                 (r c v)
                                 (cond
                                   ((and (> r r1) (< r r2) (> c c1) (< c c2)) 2)
                                   (else (at acc r c))))))
                    g
                    rectangles)))) g))
         (cue (first (find-color stage-a 3)))
         (reds (filter (lambda (obj) (= (obj-color obj) 2))
                       (objects stage-a 0)))
         (target
          (first
           (filter
            (lambda (obj)
              (any? (lambda (cell)
                      (= (+ (abs (- (first cell) (first cue)))
                            (abs (- (second cell) (second cue))))
                         1))
                    (obj-cells obj)))
            reds))))
    (paint-cells stage-a (obj-cells target) 8))))
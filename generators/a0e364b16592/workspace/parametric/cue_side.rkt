(rule!
 (let* ((cue-cells
         (filter (lambda (p) (= (at g (first p) (second p)) 9))
                 (grid-positions g)))
        (cue (first cue-cells))
        (up? (= (first cue) 0)))
   (define (fixed? value) (or (= value 5) (= value 9)))
   (for/fold ((out (empty-grid (rows g) (cols g) 0)))
             ((c (in-range (cols g))))
     (let col-loop ((start 0) (acc out))
       (if (>= start (rows g))
           acc
           (let find-stop ((r start))
             (if (or (>= r (rows g)) (fixed? (at g r c)))
                 (let* ((stop r)
                        (vals
                         (for/list ((rr (in-range start stop))
                                    #:when (not (= (at g rr c) 0)))
                           (at g rr c)))
                        (base (if up? start (- stop (length vals))))
                        (packed
                         (for/fold ((a acc))
                                   ((v (in-list vals))
                                    (rr (in-range base (+ base (length vals)))))
                           (set-cell a rr c v)))
                        (with-fixed
                         (if (< stop (rows g))
                             (set-cell packed stop c (at g stop c))
                             packed)))
                   (col-loop (+ stop 1) with-fixed))
                 (find-stop (+ r 1)))))))))

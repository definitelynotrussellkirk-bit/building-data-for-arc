(rule!
 (let* ((a
         (let ((dummy 0))
           (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                     ((obj (in-list (objects g 0))))
             (let* ((cells (obj-cells obj))
                    (halo
                     (filter
                      (lambda (p)
                        (and (= (at g (first p) (second p)) 0)
                             (not (member? p cells))))
                      (remove-duplicates
                       (apply append
                              (map (lambda (cell)
                                     (map (lambda (d)
                                            (list (+ (first cell) (first d))
                                                  (+ (second cell) (second d))))
                                          cardinal-deltas))
                                   cells))))))
               (paint-cells
                out
                (filter (lambda (p)
                          (in-bounds? (first p) (second p) (rows g) (cols g)))
                        halo)
                (obj-color obj))))))
        (best
         (for/fold ((best (list 1 -1))) ((color (in-range 1 10)))
           (let ((count
                  (for*/fold ((n 0))
                             ((r (in-range (rows a)))
                              (c (in-range (cols a))))
                    (if (= (at a r c) color) (+ n 1) n))))
             (if (> count (second best)) (list color count) best))))
        (selected (first best)))
   (for*/fold ((out a))
              ((r (in-range (rows a)))
               (c (in-range (cols a))))
     (if (= (at a r c) selected)
         (for/fold ((next out)) ((d (in-list cardinal-deltas)))
           (let ((rr (+ r (first d)))
                 (cc (+ c (second d))))
             (if (and (in-bounds? rr cc (rows a) (cols a))
                      (= (at a rr cc) 0))
                 (set-cell next rr cc selected)
                 next)))
         out))))

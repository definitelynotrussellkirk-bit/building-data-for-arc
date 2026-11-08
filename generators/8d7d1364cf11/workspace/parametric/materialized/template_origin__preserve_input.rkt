(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g))
               (bg 4))
           (let ((comps (objects-multicolor g bg)))
             (let ((shapes (filter (lambda (o) (> (obj-size o) 1)) comps))
                   (dots (filter (lambda (o) (= (obj-size o) 1)) comps)))
               (let ((shape-cells (flatmap (lambda (s)
                                             (map (lambda (cell) (list s cell))
                                                  (obj-cells s)))
                                           shapes)))
                 (reduce (lambda (acc dot)
                           (let ((dp (fst (obj-cells dot)))
                                 (dc (at g
                                         (fst (fst (obj-cells dot)))
                                         (snd (fst (obj-cells dot))))))
                             (let ((matches (filter (lambda (m)
                                                      (= (at g
                                                             (fst (snd m))
                                                             (snd (snd m)))
                                                         dc))
                                                    shape-cells)))
                               (if (empty? matches)
                                   acc
                                   (let ((tmpl (fst (first matches)))
                                         (anchor (let ((bb (obj-bbox (fst (first matches)))))
                                         (list (first bb) (second bb)))))
                                     (let ((dr (- (fst dp) (fst anchor)))
                                           (dcc (- (snd dp) (snd anchor))))
                                       (reduce (lambda (a cell)
                                                 (let ((nr (+ (fst cell) dr))
                                                       (nc (+ (snd cell) dcc)))
                                                   (if (in-bounds? nr nc h w)
                                                       (set-cell a
                                                                 nr
                                                                 nc
                                                                 (at g
                                                                     (fst cell)
                                                                     (snd cell)))
                                                       a)))
                                               acc
                                               (obj-cells tmpl))))))))
                         g
                         dots)))))))

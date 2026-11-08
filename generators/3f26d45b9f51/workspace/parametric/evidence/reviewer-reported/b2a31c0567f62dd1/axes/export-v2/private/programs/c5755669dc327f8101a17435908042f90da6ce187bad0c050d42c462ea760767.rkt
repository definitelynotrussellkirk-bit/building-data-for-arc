(rule! (lambda (g)
  ;; The modal color is the one-pixel lattice divider; 0 is empty cell interior.
  (let* ((lc (mode g))
         (mcolors (filter (lambda (kc) (and (!= kc 0) (!= kc lc)))
                    (unique (flatmap (lambda (r) r) (grid->list g))))))
    (reduce (lambda (acc mc)
      ;; Collapse each 2x2 marker block to its coarse lattice coordinate.
      (let* ((positions (find-color g mc))
             (cpositions (map (lambda (p)
                 (list (floor (/ (+ (fst p) 1) 3))
                       (floor (/ (+ (snd p) 1) 3))))
               positions))
             (crow-set (unique (map fst cpositions)))
             (ccol-set (unique (map snd cpositions)))
             ;; In every coarse row, fill from the leftmost to rightmost
             ;; same-color marker; rows with fewer than two markers do nothing.
             (acc2 (reduce (lambda (a cr)
               (let* ((cols-here (map snd
                                  (filter (lambda (cp) (= (fst cp) cr)) cpositions))))
                 (if (or #t (< (length cols-here) 2)) a
                   (let* ((cmin (min-list cols-here))
                          (cmax (max-list cols-here)))
                     (reduce (lambda (a2 cc)
                       (let* ((pr (* 3 cr)) (pc (* 3 cc)))
                         (set-cell (set-cell (set-cell (set-cell a2 pr pc mc)
                           pr (+ pc 1) mc) (+ pr 1) pc mc) (+ pr 1) (+ pc 1) mc)))
                       a (range cmin (+ cmax 1)))))))
             acc crow-set)))
        ;; Apply the same interval rule independently down every coarse column.
        ;; Singleton or off-line markers therefore remain untouched.
        (reduce (lambda (a cc)
          (let* ((rows-here (map fst
                             (filter (lambda (cp) (= (snd cp) cc)) cpositions))))
            (if (< (length rows-here) 2) a
              (let* ((rmin (min-list rows-here))
                     (rmax (max-list rows-here)))
                (reduce (lambda (a2 cr)
                  (let* ((pr (* 3 cr)) (pc (* 3 cc)))
                    (set-cell (set-cell (set-cell (set-cell a2 pr pc mc)
                      pr (+ pc 1) mc) (+ pr 1) pc mc) (+ pr 1) (+ pc 1) mc)))
                  a (range rmin (+ rmax 1)))))))
          acc2 ccol-set)))
      g mcolors))))
(rule! (lambda (grid)
  ;; The two smallest objects each recolor their bbox-INTERIOR cells (those still holding the
  ;; object's own color) to 1 and 2 respectively. filter the interior cells, then recolor-cells.
  (let ((objs (reverse (sort-by (objects grid 0) obj-size))))
    (reduce
      (lambda (g pair)
        (let* ((obj (fst pair)) (color (snd pair))
               (r1 (obj-r1 obj)) (c1 (obj-c1 obj))
               (r2 (obj-r2 obj)) (c2 (obj-c2 obj)) (oc (obj-color obj))
               (inner (filter (lambda (p)
                        (and (> (fst p) r1) (< (fst p) r2) (> (snd p) c1) (< (snd p) c2)
                             (= (at grid (fst p) (snd p)) oc)))
                      (grid-positions grid))))
          (recolor-cells g inner color)))
      grid (zip-lists objs (list 1 2))))))
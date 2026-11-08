(rule!
 (lambda (grid)
   ;; Treat each 4-connected zero component independently.
   (reduce
    (lambda (out region)
      (let* ((cell (first region))
             (size (length region))
             (fill-color
              (cond
               ((<= size 8) 8)
               ((<= size 24) 4)
               (else 3))))
        ;; Border-connected zero is exterior; recolor only enclosed regions.
        (if (enclosed? grid (first cell) (second cell))
            (recolor-cells out region fill-color)
            out)))
    grid
    (find-0-regions grid))))
(rule!
 (lambda (grid)
   (let* ((regions
           (filter
            (lambda (region)
              (let ((cell (first region)))
                (enclosed? grid (first cell) (second cell))))
            (find-0-regions grid)))
          ;; A: the largest enclosed component is derived anew from this input.
          (largest (reduce (lambda (best region) (max best (length region))) 1 regions)))
     ;; B: the area supplied by A chooses both inclusive thresholds.
     (reduce
      (lambda (out region)
        (let* ((size (length region))
               (fill-color
                (cond
                 ((<= (* 4 size) largest) 8)
                 ((<= (* 2 size) largest) 4)
                 (else 3))))
          (recolor-cells out region fill-color)))
      grid regions))))

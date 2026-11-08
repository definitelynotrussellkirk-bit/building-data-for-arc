(rule!
  (foldl
    (lambda (obj acc)
      (if (= (obj-color obj) 7)
          (let* ((bb (obj-bbox obj))
                 (r0 (first bb))
                 (c0 (second bb))
                 (r1 (third bb))
                 (c1 (fourth bb))
                 (cells (obj-cells obj))
                 (interior (if (and (< (+ r0 1) r1) (< (+ c0 1) c1))
                               (positions-in-rect (+ r0 1) (+ c0 1) (- r1 1) (- c1 1))
                               (list)))
                 (hollow
                   (any?
                     (lambda (p)
                       (and (= (cell-at g (fst p) (snd p)) 0)
                            (not (member p cells))))
                     interior)))
            (paint-cells acc cells (if hollow 4 2)))
          acc))
    g
    (objects g 0)))
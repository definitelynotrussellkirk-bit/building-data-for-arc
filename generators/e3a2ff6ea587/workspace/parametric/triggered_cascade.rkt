(rule!
 ;; Stage A is the canonical exact-corner rectangle fill.  Stage B consumes
 ;; that painted intermediate: every two-cell color whose endpoints land on
 ;; exactly one cell still showing the first qualifying rectangle's color
 ;; paints its own bounding box over Stage A.
 (let* ((colors (remove-duplicates
                 (map third (filter (lambda (cell) (!= (third cell) 0))
                                    (grid-cells g)))))
        (qualifying?
         (lambda (color)
           (let* ((cells (find-color g color))
                  (bb (bbox-of-cells cells))
                  (corners (list (list (first bb) (second bb))
                                 (list (first bb) (fourth bb))
                                 (list (third bb) (second bb))
                                 (list (third bb) (fourth bb)))))
             (and (= (length cells) 4)
                  (all? (lambda (p) (member? p corners)) cells)))))
        (qualifiers (filter qualifying? colors))
        (stage
         (for/fold ((out (empty-grid h w 0))) ((color (in-list colors)))
           (if (qualifying? color)
               (let ((bb (bbox-of-cells (find-color g color))))
                 (paint-cells out
                              (positions-in-rect (first bb) (second bb)
                                                 (third bb) (fourth bb))
                              color))
               out))))
   (if (empty? qualifiers)
       stage
       (let ((anchor (first qualifiers)))
         (for/fold ((out stage)) ((color (in-list colors)))
           (let ((cells (find-color g color)))
             (if (= (length cells) 2)
                 (let* ((bb (bbox-of-cells cells))
                        (anchor-hits
                         (count-if
                          (lambda (p)
                            (= (at stage (first p) (second p)) anchor))
                          cells)))
                   (if (= anchor-hits 1)
                       (paint-cells out
                                    (positions-in-rect (first bb) (second bb)
                                                       (third bb) (fourth bb))
                                    color)
                       out))
                 out)))))))

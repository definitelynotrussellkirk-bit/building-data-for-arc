(rule!
  (let* ((row-filled
           (let ((dummy 0))
             (for*/fold ((out (empty-grid (rows g) (cols g) 0)))
                        ((r (in-range (rows g)))
                         (color (in-list (grid-colors g 0))))
               (let ((cols-list
                      (map second
                           (filter (lambda (p) (= (first p) r))
                                   (find-color g color)))))
                 (if (= (length cols-list) 2)
                     (for/fold ((acc out))
                               ((c (in-range (apply min cols-list)
                                             (+ (apply max cols-list) 1))))
                       (set-cell acc r c color))
                     out)))))
         (colors (grid-colors row-filled 0)))
    (for*/fold ((out row-filled))
               ((c (in-range (cols row-filled)))
                (color (in-list colors)))
      (let ((rows-list
             (map first
                  (filter (lambda (p) (= (second p) c))
                          (find-color row-filled color)))))
        (if (= (length rows-list) 2)
            (for/fold ((acc out))
                      ((r (in-range (apply min rows-list)
                                    (+ (apply max rows-list) 1))))
              (if (= (at acc r c) 0)
                  (set-cell acc r c color)
                  acc))
            out)))))

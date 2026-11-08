(rule!
  (let ((colors (grid-colors g 0)))
    (for*/fold ((out g))
               ((c (in-range (cols g)))
                (color (in-list colors)))
      (let ((rows-list
             (map first
                  (filter (lambda (p) (= (second p) c))
                          (find-color g color)))))
        (if (= (length rows-list) 2)
            (for/fold ((acc out))
                      ((r (in-range (apply min rows-list)
                                    (+ (apply max rows-list) 1))))
              (if (= (at acc r c) 0)
                  (set-cell acc r c color)
                  acc))
            out)))))

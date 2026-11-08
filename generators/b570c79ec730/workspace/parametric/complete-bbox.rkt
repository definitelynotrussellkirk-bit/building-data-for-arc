(rule! (lambda (g)
  (let* ((objs (objects g 0)))
    (reduce (lambda (acc obj)
      (with-bbox obj
        (r1 c1 r2 c2)
        (let* ((cleared
          (reduce (lambda (a cell)
            (let* ((r (fst cell))
                   (c (snd cell)))
              (if (and (> r r1) (< r r2) (> c c1) (< c c2))
                  (set-cell a r c 0)
                  a)))
            acc
            (obj-cells obj))))
          (grid-from-fn (rows cleared) (cols cleared)
            (lambda (r c)
              (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2)
                       (or (= r r1) (= r r2) (= c c1) (= c c2)))
                  (obj-color obj)
                  (cell-at cleared r c)))))))
      g
      objs))))
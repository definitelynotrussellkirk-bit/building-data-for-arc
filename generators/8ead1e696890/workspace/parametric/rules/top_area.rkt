(rule!
  (let* ((objs (objects g 0))
         (ref (find-first
                (lambda (obj)
                  (any? (lambda (p) (= (first p) 0)) (obj-cells obj)))
                objs))
         (target-area (if ref (length (obj-cells ref)) -1)))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((obj (in-list objs)))
      (if (= (length (obj-cells obj)) target-area)
          (paint-cells out (obj-cells obj) (obj-color obj))
          out))))
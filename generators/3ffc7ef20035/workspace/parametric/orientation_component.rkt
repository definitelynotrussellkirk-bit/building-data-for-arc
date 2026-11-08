(rule!
  ;; A: read the non-blue straight bar's orientation.
  ;; Intermediate: horizontal selects the first row-major blue object;
  ;; vertical selects the second. B: fill that selected object's tight bbox.
  (let* ((blue-objs
          (sort-by
           (filter (lambda (o) (= (obj-color o) 1))
                   (objects-8 g 0))
           (lambda (o) (+ (* 32 (obj-r1 o)) (obj-c1 o)))))
         (selector
          (first
           (filter (lambda (o) (not (= (obj-color o) 1)))
                   (objects g 0))))
         (chosen
          (if (> (obj-w selector) (obj-h selector))
              (first blue-objs)
              (second blue-objs)))
         (bb (obj-bbox chosen)))
    (paint-cells g
                 (positions-in-rect
                  (first bb) (second bb) (third bb) (fourth bb))
                 8)))

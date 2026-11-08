(rule!
  (lambda (g)
    ;; Counterfactual: skip Stage A and attempt Stage B on the original input.
    ;; Lawful inputs contain no blue component, so no component can be selected.
    (let* ((blue-objs
            (filter (lambda (o) (= (obj-color o) 1)) (objects g 0)))
           (selected (if (null? blue-objs) #f (pick-max blue-objs obj-size))))
      (if selected
          (recolor-cells g (obj-cells selected) 8)
          g))))

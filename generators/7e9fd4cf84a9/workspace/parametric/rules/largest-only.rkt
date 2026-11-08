(rule!
  (let* ((green-objs
           (filter (lambda (obj) (= (obj-color obj) 3)) (objects g 0)))
         (largest-size
           (if (null? green-objs) 0 (max-list (map obj-size green-objs))))
         (selected
           (filter (lambda (obj) (= (obj-size obj) largest-size)) green-objs)))
    (reduce (lambda (out obj)
      (let* ((bb (obj-bbox obj))
             (r0 (first bb))
             (c0 (second bb))
             (r1 (third bb))
             (c1 (fourth bb)))
        (reduce (lambda (acc r)
          (reduce (lambda (acc2 c)
            (if (= (cell-at g r c) 0)
              (set-cell acc2 r c 8)
              acc2))
            acc (range c0 (+ c1 1))))
          out (range r0 (+ r1 1)))))
      g selected)))
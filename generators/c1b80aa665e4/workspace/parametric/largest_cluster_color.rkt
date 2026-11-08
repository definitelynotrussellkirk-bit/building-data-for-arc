(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (clusters (filter (lambda (o) (> (obj-size o) 1)) objs))
         (largest (first (sort-by clusters (lambda (o) (* -1 (obj-size o))))))
         (anchor-color (obj-color largest)))
    (paint-objects-by g objs
      (lambda (o)
        (if (and (= (obj-size o) 1) (= (obj-color o) anchor-color))
            9
            #f))))))

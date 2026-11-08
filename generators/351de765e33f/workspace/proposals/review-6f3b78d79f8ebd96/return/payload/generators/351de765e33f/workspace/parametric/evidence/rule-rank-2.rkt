(rule!
  (let ((objs (sort (objects g 0)
                    (lambda (a b)
                      (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                            [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                            [else (< (obj-c1 a) (obj-c1 b))])))))
    (if (empty? objs)
        g
        (paint-cells g (obj-cells (if (>= (length objs) 2) (second objs) (first objs))) 8))))

(rule!
  (lambda (g)
    (let* ([objs (objects g 0)]
           [anchor (if (empty? objs) #f (argmax obj-size objs))]
           [rh (if anchor (obj-h anchor) 1)]
           [rw (if anchor (obj-w anchor) 1)])
      (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list objs)])
        (let* ([left (* (obj-h obj) rw)]
               [right (* (obj-w obj) rh)]
               [color (cond [(> left right) 2] [(< left right) 3] [else 4])])
          (paint-cells out (obj-cells obj) color))))))

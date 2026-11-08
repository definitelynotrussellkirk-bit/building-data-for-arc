(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list (objects g 0))])
    (let* ((h (obj-h obj))
           (w (obj-w obj))
           (color (cond [(> h w) 2] [(> w h) 3] [else 4])))
      (paint-cells out (obj-cells obj) color))))
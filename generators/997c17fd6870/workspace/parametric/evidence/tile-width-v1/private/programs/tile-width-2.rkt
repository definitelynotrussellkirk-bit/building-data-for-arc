(lambda (g)
  (let* ([w (cols g)])
    (cellmap g
             (r c v)
             (let* ([tile-start (- c (remainder c 2))]
                    [offset (remainder c 2)]
                    [source-start (- (- w 2) tile-start)])
               (at g r (+ source-start offset))))))

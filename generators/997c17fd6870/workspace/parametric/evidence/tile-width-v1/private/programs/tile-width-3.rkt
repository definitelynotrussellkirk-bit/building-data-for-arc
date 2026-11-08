(lambda (g)
  (let* ([w (cols g)])
    (cellmap g
             (r c v)
             (let* ([tile-start (- c (remainder c 3))]
                    [offset (remainder c 3)]
                    [source-start (- (- w 3) tile-start)])
               (at g r (+ source-start offset))))))

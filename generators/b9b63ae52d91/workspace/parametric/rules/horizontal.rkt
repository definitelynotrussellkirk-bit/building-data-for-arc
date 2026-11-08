(rule!
  (let ((w (cols g)))
    (cellmap g (r c v)
      (if (= v 8)
          (if (= (at g r (- (- w 1) c)) 8) 2 5)
          0))))

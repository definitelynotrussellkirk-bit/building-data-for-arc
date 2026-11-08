(rule!
  (let ((h (rows g)))
    (cellmap g (r c v)
      (if (= v 8)
          (if (= (at g (- (- h 1) r) c) 8) 2 5)
          0))))

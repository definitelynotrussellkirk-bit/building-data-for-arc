(rule!
  (let ((out-h (- (rows g) 1))
        (out-w (- (cols g) 1)))
    (grid-from-fn out-h out-w
      (lambda (r c)
        (let ((rv (at g (+ r 1) 0))
              (cv (at g 0 (+ c 1))))
          (if (= rv cv) rv 0))))))
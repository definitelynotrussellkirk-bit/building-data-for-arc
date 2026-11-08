(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Column 0 is the instruction strip. Its red row is the amount
         ;; by which the payload rows rotate downward.
         (red-row (find (lambda (r) (= (at g r 0) 2)) (range 0 h)))
         (down-shift (remainder (- h red-row) h)))
    ;; Remove the instruction strip and read output row r from payload row
    ;; r - red-row (mod h), which is exactly a downward cyclic rotation.
    (build-grid h (- w 1) (r c)
      (at g (remainder (+ r down-shift) h) (+ c 1))))))

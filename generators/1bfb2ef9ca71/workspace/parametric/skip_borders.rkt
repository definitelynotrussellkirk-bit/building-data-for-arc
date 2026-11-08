(rule!
  (let* ((base (empty-grid (rows g) (cols g) 0))
         (frames (objects base 0))
         (winner
           (select-object-by
             frames
             (lambda (obj) (length (bbox-interior-cells obj)))
             'max)))
    (if winner
        (fill-object-interior base winner (obj-color winner) 0)
        base)))

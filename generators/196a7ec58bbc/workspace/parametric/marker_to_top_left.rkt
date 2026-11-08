(rule!
  (let* ((h (rows g))
         (w (cols g))
         (last-r (- h 1))
         (last-c (- w 1))
         (normalized
           (cond
             ((= (at g 0 0) 9) g)
             ((= (at g 0 last-c) 9) (rotate-ccw g))
             ((= (at g last-r last-c) 9) (rotate-180 g))
             ((= (at g last-r 0) 9) (rotate-cw g))
             (else g))))
    (stack-grids 'vertical
      (list
        (stack-grids 'horizontal (list normalized (rotate-cw normalized)))
        (stack-grids 'horizontal (list (rotate-ccw normalized) (rotate-180 normalized)))))))
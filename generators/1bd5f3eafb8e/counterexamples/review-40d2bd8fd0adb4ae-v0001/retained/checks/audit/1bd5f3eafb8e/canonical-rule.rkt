(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fives (find-color g 5))
                  (fr (fst (first fives)))
                  (fc (snd (first fives)))
                  (horiz (= (snd (first fives)) (snd (second fives))))
                  (top-half (and horiz (< fr (/ h 2))))
                  (left-half (and (not horiz) (< fc (/ w 2)))))
             (recolor (if horiz
                          (if top-half
                              (subgrid g 0 0 (- (/ h 2) 1) (- w 1))
                              (subgrid g (/ h 2) 0 (- h 1) (- w 1)))
                          (if left-half
                              (subgrid g 0 0 (- h 1) (- (/ w 2) 1))
                              (subgrid g 0 (/ w 2) (- h 1) (- w 1))))
                      5
                      8)))))

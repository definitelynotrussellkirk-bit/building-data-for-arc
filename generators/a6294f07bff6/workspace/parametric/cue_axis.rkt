(rule!
 (let* ((cue-cells
         (filter (lambda (p) (= (at g (first p) (second p)) 9))
                 (grid-positions g)))
        (cue (first cue-cells))
        (r (first cue))
        (c (second cue))
        (vertical? (or (= r 0) (= r (- (rows g) 1)))))
   (if vertical? (flip-ud g) (flip-lr g))))

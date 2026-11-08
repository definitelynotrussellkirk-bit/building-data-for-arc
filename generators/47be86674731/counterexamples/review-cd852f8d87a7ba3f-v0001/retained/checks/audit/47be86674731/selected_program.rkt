; Select the only completely filled 3x3 block that uses three colors.
; The other filled 3x3 blocks are two-color distractors.
(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (starts (filter (lambda (p)
           (let ((r (fst p)) (c (snd p)))
             (and (<= (+ r 2) (- h 1)) (<= (+ c 2) (- w 1))
                  (for*/and ((dr (range 0 3)) (dc (range 0 3)))
                    (!= 0 (at g (+ r dr) (+ c dc))))
                  (= 3 (length (unique
                    (for*/list ((dr (range 0 3)) (dc (range 0 3)))
                      (at g (+ r dr) (+ c dc)))))))))
           (positions-in-rect 0 0 (- h 1) (- w 1)))))
    (let ((p (first starts)))
      (crop g (fst p) (snd p) (+ (fst p) 2) (+ (snd p) 2))))))

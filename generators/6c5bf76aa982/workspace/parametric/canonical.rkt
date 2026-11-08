(rule!
  (reduce (lambda (out obj)
    (if (not (= (obj-color obj) 7)) out
      (let* ((cells (obj-cells obj))
             (top (any? (lambda (p) (= (fst p) 0)) cells))
             (bottom (any? (lambda (p) (= (fst p) (- h 1))) cells))
             (left (any? (lambda (p) (= (snd p) 0)) cells))
             (right (any? (lambda (p) (= (snd p) (- w 1))) cells))
             (touch-count (+ (if top 1 0) (if bottom 1 0) (if left 1 0) (if right 1 0))))
        (if (= touch-count 1)
          (recolor-cells out cells 3)
          out))))
    g (objects g 0)))
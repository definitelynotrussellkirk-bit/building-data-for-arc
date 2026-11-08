(rule!
  (let ((dummy 0))
    (define cue (first (find-color g 2)))
    (define controls
      (filter (lambda (obj)
                (and (= (obj-color obj) 4)
                     (= (obj-h obj) 1)
                     (or (= (obj-size obj) 4) (= (obj-size obj) 5))))
              (objects g 0)))
    (define (distance obj)
      (+ (abs (- (first cue) (obj-r1 obj)))
         (cond [(< (second cue) (obj-c1 obj)) (- (obj-c1 obj) (second cue))]
               [(> (second cue) (obj-c2 obj)) (- (second cue) (obj-c2 obj))]
               [else 0])))
    (define selected
      (first (sort controls (lambda (a b) (< (distance a) (distance b))))))
    (define left? (= (obj-size selected) 4))
    (grid-from-fn h w
      (lambda (r c)
        (let ((v (cell-at g r c)))
          (if (and (= v 0)
                   (if left?
                       (and (< (+ c 3) w)
                            (= (cell-at g r (+ c 1)) 4)
                            (= (cell-at g r (+ c 2)) 4)
                            (= (cell-at g r (+ c 3)) 4)
                            (or (= (+ c 4) w)
                                (not (= (cell-at g r (+ c 4)) 4))))
                       (and (>= (- c 3) 0)
                            (= (cell-at g r (- c 1)) 4)
                            (= (cell-at g r (- c 2)) 4)
                            (= (cell-at g r (- c 3)) 4)
                            (or (< (- c 4) 0)
                                (not (= (cell-at g r (- c 4)) 4))))))
              6
              v))))))

(rule!
  (let* ((stage-a (fill-all-enclosed g 8 0))
         (holes (filter (lambda (o) (= (obj-color o) 8)) (objects stage-a 0))))
    (if (null? holes)
        stage-a
        (let* ((chosen (pick-max holes (lambda (o) (obj-size o))))
               (p (obj-center chosen))
               (r (first p))
               (c (second p))
               (top r)
               (left c)
               (bottom (- (rows stage-a) 1 r))
               (right (- (cols stage-a) 1 c))
               (distance (min top left bottom right))
               (target (cond
                         [(= distance top) (list 0 c)]
                         [(= distance left) (list r 0)]
                         [(= distance bottom) (list (- (rows stage-a) 1) c)]
                         [else (list r (- (cols stage-a) 1))])))
          (paint-line stage-a p target 8)))))

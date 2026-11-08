(rule!
 (let ((dummy 0))
  (define (neighbors4 r c)
   (list (list (- r 1) c) (list (+ r 1) c) (list r (- c 1)) (list r (+ c 1))))
  (let ((obj
         (for*/list ((r (in-range (rows g)))
                     (c (in-range (cols g)))
                     #:when (not (member? (at g r c) (list 0 7))))
          (list r c (at g r c)))))
   (if (empty? obj)
       g
       (let* ((source-color (third (first obj)))
              (maxc (apply max (map second obj)))
              (stage-a
               (for*/fold ((out g))
                          ((shift (in-range 1 (- (cols g) maxc)))
                           (p (in-list obj)))
                (set-cell out (first p) (+ (second p) shift) (third p))))
              (cues
               (for*/list ((r (in-range (rows g)))
                           (c (in-range (cols g)))
                           #:when
                           (and (= (at g r c) 7)
                                (not (and (= r 0) (= c 0)))
                                (any? (lambda (p)
                                       (and (in-bounds? (first p) (second p) (rows stage-a) (cols stage-a))
                                            (= (at stage-a (first p) (second p)) source-color)))
                                      (neighbors4 r c))))
                (list r c))))
        (if (empty? cues)
            stage-a
            (let ((cue (first cues)))
             (for/fold ((out stage-a)) ((r (in-range (first cue) (rows stage-a))))
              (set-cell out r (second cue) source-color)))))))))

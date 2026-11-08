(rule!
 (lambda (g)
  (let* ([n (- (rows g) 1)]
         [side (* 2 n)]
         [colors (for/list ([r (range n)]) (at g r 0))])
   (build-grid side side (r c)
    (list-ref colors
     (min r c (- side 1 r) (- side 1 c)))))))

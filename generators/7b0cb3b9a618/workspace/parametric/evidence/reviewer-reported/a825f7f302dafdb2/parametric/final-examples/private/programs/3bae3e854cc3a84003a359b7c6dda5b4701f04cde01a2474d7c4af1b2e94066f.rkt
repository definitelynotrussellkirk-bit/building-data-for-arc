(rule!
 (lambda (g)
   (let* ([height (rows g)]
          [width (cols g)]
          [colors (sort (filter (lambda (c) (not (= c 0)))
                                (remove-duplicates (apply append g))) <)]
          [cells (lambda (color)
                   (for*/list ([r (range 0 height)] [c (range 0 width)]
                               #:when (= (at g r c) color))
                     (list r c)))]
          [horizontal? (lambda (color)
                         (let* ([positions (cells color)]
                                [rs (map first positions)]
                                [cs (map second positions)])
                           (> (- (apply max cs) (apply min cs))
                              (- (apply max rs) (apply min rs)))))]
          [hs (filter horizontal? colors)]
          [vs (filter (lambda (color) (not (horizontal? color))) colors)]
          [covered-colors
           (remove-duplicates
            (for*/list ([h hs] [v vs]
                        [r (remove-duplicates (map first (cells h)))]
                        [c (remove-duplicates (map second (cells v)))])
              (at g r c)))]
          [bottom (filter (lambda (color) (not (member color covered-colors))) colors)])
     (if (= (length bottom) 1)
         (list (list (first bottom)))
         (error 'back-layer "expected one band below every crossing")))))

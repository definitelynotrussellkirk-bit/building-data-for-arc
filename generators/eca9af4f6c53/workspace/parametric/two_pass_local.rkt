(rule!
  (let ()
    (define (window-write scene r0 c0)
      (let* ([positions (positions-in-rect r0 c0 (+ r0 1) (+ c0 1))]
             [colored
              (filter
               (lambda (position)
                 (not (= (at scene (first position) (second position)) 0)))
               positions)]
             [zeros
              (filter
               (lambda (position)
                 (= (at scene (first position) (second position)) 0))
               positions)]
             [colors
              (remove-duplicates
               (map
                (lambda (position)
                  (at scene (first position) (second position)))
                colored))])
        (if (and (= (length colored) 3)
                 (= (length zeros) 1)
                 (= (length colors) 1))
            (list
             (list (first (first zeros))
                   (second (first zeros))
                   (first colors)))
            '())))
    (define (completion-pass scene)
      (paint-cells
       scene
       (for*/fold
        ([writes '()])
        ([r (in-range (- (rows scene) 1))]
         [c (in-range (- (cols scene) 1))])
         (append writes (window-write scene r c)))))
    (completion-pass (completion-pass g))))

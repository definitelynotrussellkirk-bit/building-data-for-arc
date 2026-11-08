(rule!
  (let ((dummy 0))
    (define (has? p cells) (member? p cells))
    (define (rotate-cw-cells cells)
      (if (empty? cells)
          cells
          (let* ((bb (bbox-of-cells cells))
                 (h (+ 1 (third bb))))
            (normalize-cells
              (map (lambda (p)
                     (list (second p) (- h 1 (first p))))
                   cells)))))
    (define a (normalize-cells (find-color g 1)))
    (define b (normalize-cells (find-color g 2)))
    (define rotate-a? (>= (length a) (length b)))
    (define aa (if rotate-a? (rotate-cw-cells a) a))
    (define bb (if rotate-a? b (rotate-cw-cells b)))
    (define ba (bbox-of-cells aa))
    (define bbb (bbox-of-cells bb))
    (define out-h (max (if ba (+ 1 (third ba)) 0) (if bbb (+ 1 (third bbb)) 0)))
    (define out-w (max (if ba (+ 1 (fourth ba)) 0) (if bbb (+ 1 (fourth bbb)) 0)))
    (define ctrl (at g 0 0))
    (define res
      (cond [(= ctrl 3) (remove-duplicates (append aa bb))]
            [(= ctrl 4) (append (filter (lambda (p) (not (has? p bb))) aa)
                                (filter (lambda (p) (not (has? p aa))) bb))]
            [(= ctrl 5) (filter (lambda (p) (has? p bb)) aa)]
            [else (list)]))
    (if (empty? res)
        (empty-grid 1 1 0)
        (paint-cells (empty-grid out-h out-w 0) res 8))))

(rule!
  (let ((dummy 0))
    (define (has? p cells) (member? p cells))
    (define s2 (normalize-cells (find-color g 2)))
    (define s3 (normalize-cells (find-color g 3)))
    (define inter (filter (lambda (p) (has? p s3)) s2))
    (paint-cells (empty-grid (rows g) (cols g) 0) inter 8)))
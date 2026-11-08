(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define (row-empty? r)
               (andmap (lambda (c) (zero? (at g r c))) (range 0 w)))
             (define (col-empty? c)
               (andmap (lambda (r) (zero? (at g r c))) (range 0 h)))
             (cellmap g (r c v) (cond ((row-empty? r) 2) (else v)))))))
(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((n (cols g))
                  (nz (for/sum ((c (range 0 n))) (if (!= (at g 0 c) 0) 1 0)))
                  (sz (* nz n)))
             (build-grid sz
                         sz
                         (r c)
                         (let ((idx (+ (- c (- sz 1)) r)))
                           (if (and (>= idx 0) (< idx n)) (at g 0 idx) 0)))))))
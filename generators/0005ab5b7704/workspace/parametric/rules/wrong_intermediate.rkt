(rule!
 ;; Ablation: measure and rank every column before applying the marker selector.
 (let ((keep (filter (lambda (c) (= (at g 0 c) 4)) (range 0 w))))
   (define (body-count c)
     (length
      (filter (lambda (r) (not (= (at g r c) 0)))
              (range 1 h))))
   (define (first-n xs n)
     (if (or (= n 0) (empty? xs))
         (list)
         (cons (first xs) (first-n (rest xs) (- n 1)))))
   (let* ((all-ordered
           (sort (range 0 w)
                 (lambda (a b)
                   (let ((ca (body-count a))
                         (cb (body-count b)))
                     (or (> ca cb)
                         (and (= ca cb) (< a b)))))))
          (ordered (first-n all-ordered (length keep))))
     (for/list ((r (in-range 1 h)))
       (for/list ((c (in-list ordered))) (at g r c))))))

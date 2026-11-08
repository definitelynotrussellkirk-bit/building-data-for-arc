(rule!
  (let ((dummy 0))
    (define (majority-entry vals)
      (let* ((colors (remove-duplicates (filter (lambda (v) (not (= v 0))) vals)))
             (ranked
               (sort colors
                 (lambda (a b)
                   (let ((ca (count-where (lambda (v) (= v a)) vals))
                         (cb (count-where (lambda (v) (= v b)) vals)))
                     (or (> ca cb) (and (= ca cb) (> a b))))))))
        (if (empty? ranked)
            (list 0 0)
            (let ((winner (first ranked)))
              (list winner (count-where (lambda (v) (= v winner)) vals))))))
    (let* ((hm (quotient (rows g) 2))
           (wm (quotient (cols g) 2))
           (q1 (subgrid g 0 0 (- hm 1) (- wm 1)))
           (q2 (subgrid g 0 wm (- hm 1) (- (cols g) 1)))
           (q3 (subgrid g hm 0 (- (rows g) 1) (- wm 1)))
           (q4 (subgrid g hm wm (- (rows g) 1) (- (cols g) 1)))
           (entries
             (list (majority-entry (apply append q1))
                   (majority-entry (apply append q2))
                   (majority-entry (apply append q3))
                   (majority-entry (apply append q4))))
           (ordered
             (sort entries
               (lambda (a b)
                 (or (> (second a) (second b))
                     (and (= (second a) (second b)) (> (first a) (first b))))))))
      (list (list (first (first ordered)) (first (second ordered)))
            (list (first (third ordered)) (first (fourth ordered)))))))

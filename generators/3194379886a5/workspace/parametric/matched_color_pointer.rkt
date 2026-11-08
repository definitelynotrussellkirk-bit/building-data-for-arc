(rule!
  (let ((dummy 0))
    (define (split-panels-row grid count)
      (let* ((panel-w (quotient (- (cols grid) (- count 1)) count)))
        (for/list ((i (in-range count)))
          (let ((left (* i (+ panel-w 1))))
            (subgrid grid 0 left (- (rows grid) 1) (+ left panel-w -1))))))
    (define transform-names
      (list 'id 'rot90 'rot180 'rot270 'flip-h 'flip-v 'transpose 'anti-transpose))
    (define (anti-transpose-grid grid) (rotate-180 (transpose grid)))
    (define (apply-transform-name name grid)
      (cond ((equal? name 'id) grid)
            ((equal? name 'rot90) (rotate-cw grid))
            ((equal? name 'rot180) (rotate-180 grid))
            ((equal? name 'rot270) (rotate-ccw grid))
            ((equal? name 'flip-h) (flip-lr grid))
            ((equal? name 'flip-v) (flip-ud grid))
            ((equal? name 'transpose) (transpose grid))
            (else (anti-transpose-grid grid))))
    (define (canonical-cells panel)
      (sort
       (normalize-cells
        (filter (lambda (p) (not (= (at panel (first p) (second p)) 0)))
                (grid-positions panel)))
       cell<))
    (let* ((panels (split-panels-row g 4))
           (libs (list (first panels) (second panels) (third panels)))
           (q (fourth panels))
           (qcanon (canonical-cells q))
           (qcolor (first (filter (lambda (v) (not (= v 0))) (apply append q))))
           (chosen-index
            (first
             (filter
              (lambda (i)
                (any? (lambda (name)
                        (equal? (canonical-cells
                                 (apply-transform-name name (list-ref libs i)))
                                qcanon))
                      transform-names))
              (list 0 1 2))))
           (chosen (list-ref libs chosen-index))
           (pointer-color
            (first (filter (lambda (v) (not (= v 0))) (apply append chosen))))
           (target (list-ref libs (- pointer-color 1))))
      (grid-from-fn
       (rows target)
       (cols target)
       (lambda (r c) (if (= (at target r c) 0) 0 qcolor))))))

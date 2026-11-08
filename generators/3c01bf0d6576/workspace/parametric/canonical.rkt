(rule!
  (let ((dummy 0))
    (define (apply-transform grid cmd)
      (cond [(= cmd 0) grid]
            [(= cmd 1) (rotate-cw grid)]
            [(= cmd 2) (rotate-180 grid)]
            [(= cmd 3) (transpose grid)]
            [(= cmd 4) (flip-lr grid)]
            [else (flip-ud grid)]))
    ;; Components are 4-connected across all non-zero colours.
    (define (nonzero-components grid)
      (let loop ([remaining (filter-cells grid (lambda (r c v) (not (= v 0))))] [acc (list)])
        (if (empty? remaining)
            (reverse acc)
            (let* ((start (first remaining))
                   (cells (connected-region grid (first start) (second start)
                            (lambda (r c v) (not (= v 0))) 4)))
              (loop (filter (lambda (p) (not (member? p cells))) remaining)
                    (cons cells acc))))))
    (define (crop-cells cells)
      ;; Crop from the original grid, so any disconnected cell inside this
      ;; component's bbox remains part of the visible motif.
      (let ((bb (bbox-of-cells cells)))
        (subgrid g (first bb) (second bb) (third bb) (fourth bb))))
    ;; Reading order chooses A, A', then B; later components are ignored except
    ;; when crop-cells includes them inside one of those bounding boxes.
    (let* ((components (sort (nonzero-components g)
                             (lambda (a b)
                               (let ((ba (bbox-of-cells a)) (bb (bbox-of-cells b)))
                                 (if (= (first ba) (first bb))
                                     (< (second ba) (second bb))
                                     (< (first ba) (first bb)))))))
           (a (crop-cells (first components)))
           (ap (crop-cells (second components)))
           (b (crop-cells (third components)))
           (cmd (find-first (lambda (t) (equal? (apply-transform a t) ap)) (list 0 1 2 3 4 5))))
      (apply-transform b (if (eq? cmd #f) 0 cmd)))))
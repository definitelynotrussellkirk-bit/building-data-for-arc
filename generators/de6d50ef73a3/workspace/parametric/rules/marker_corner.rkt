(rule!
  (let ((dummy 0))
    (define (nonzero-cells grid)
      (filter
        (lambda (p) (not (= (at grid (first p) (second p)) 0)))
        (grid-positions grid)))
    (define (crop-nonzero grid)
      (let ((cells (nonzero-cells grid)))
        (if (empty? cells)
            (list (list 0))
            (let ((bb (bbox-of-cells cells)))
              (subgrid grid (first bb) (second bb) (third bb) (fourth bb))))))
    (define (paste-nonzero grid pat top left)
      (for*/fold ((out grid))
                 ((r (in-range (rows pat))) (c (in-range (cols pat))))
        (let ((v (at pat r c)) (rr (+ top r)) (cc (+ left c)))
          (if (and (not (= v 0))
                   (in-bounds? rr cc (rows out) (cols out)))
              (set-cell out rr cc v)
              out))))
    (define cells (nonzero-cells g))
    (define bb (bbox-of-cells cells))
    (define pat (crop-nonzero g))
    (define values
      (map (lambda (p) (at g (first p) (second p))) cells))
    (define colors (remove-duplicates values))
    (define (count-color x)
      (length (filter (lambda (v) (= v x)) values)))
    (define (least-color remaining best)
      (if (empty? remaining)
          best
          (least-color
            (rest remaining)
            (if (< (count-color (first remaining)) (count-color best))
                (first remaining)
                best))))
    (define marker-color (least-color (rest colors) (first colors)))
    (define marker
      (first
        (filter
          (lambda (p) (= (at g (first p) (second p)) marker-color))
          cells)))
    (define top
      (if (= (first marker) (first bb)) 0 (- (rows g) (rows pat))))
    (define left
      (if (= (second marker) (second bb)) 0 (- (cols g) (cols pat))))
    (paste-nonzero (empty-grid (rows g) (cols g) 0) pat top left)))

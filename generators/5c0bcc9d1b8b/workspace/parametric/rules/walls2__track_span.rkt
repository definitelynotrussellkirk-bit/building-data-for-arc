#lang racket
(require json)

(define OUTPUT-WALL-OFFSET 2)
(define LENGTH-MEASURE 'track-span)

(define (grid-rows grid) (length grid))
(define (grid-cols grid) (length (first grid)))
(define (at grid row col) (list-ref (list-ref grid row) col))

(define (divider-line? values)
  (or (andmap (lambda (value) (or (= value 0) (= value 5))) values)
      (> (for/sum ([value (in-list values)]) (if (= value 0) 1 0))
         (quotient (length values) 2))))

(define (divider-rows grid)
  (for/list ([row (in-range (grid-rows grid))]
             #:when (divider-line? (list-ref grid row)))
    row))

(define (divider-cols grid)
  (for/list ([col (in-range (grid-cols grid))]
             #:when
             (divider-line?
              (for/list ([row (in-range (grid-rows grid))])
                (at grid row col))))
    col))

(define (gray-cells grid)
  (for*/list ([row (in-range (grid-rows grid))]
              [col (in-range (grid-cols grid))]
              #:when (= (at grid row col) 5))
    (list row col)))

(define (full-grid height width value)
  (build-list height (lambda (_) (make-list width value))))

(define (set-cell grid target-row target-col value)
  (for/list ([values (in-list grid)] [row (in-naturals)])
    (if (= row target-row)
        (for/list ([cell (in-list values)] [col (in-naturals)])
          (if (= col target-col) value cell))
        values)))

(define (paint-row grid target-row value)
  (for/list ([values (in-list grid)] [row (in-naturals)])
    (if (= row target-row)
        (make-list (grid-cols grid) value)
        values)))

(define (paint-col grid target-col value)
  (for/list ([values (in-list grid)])
    (for/list ([cell (in-list values)] [col (in-naturals)])
      (if (= col target-col) value cell))))

(define (selected-line-length cells vertical?)
  (cond
    [(eq? LENGTH-MEASURE 'cell-count) (length cells)]
    [(eq? LENGTH-MEASURE 'track-span)
     (let ([coordinates
            (map (lambda (cell) (if vertical? (first cell) (second cell)))
                 cells)])
       (+ 1 (- (apply max coordinates) (apply min coordinates))))]
    [else (error 'selected-line-length "unsupported LENGTH-MEASURE")]))

(define (solve grid)
  (define height (grid-rows grid))
  (define width (grid-cols grid))
  (define drows (divider-rows grid))
  (define dcols (divider-cols grid))
  (define center-row (quotient (- height 1) 2))
  (define center-col (quotient (- width 1) 2))
  (define vertical? (>= (length dcols) 2))
  (define cells (gray-cells grid))
  (define line-length (selected-line-length cells vertical?))
  (define base (full-grid height width 7))
  (define with-walls
    (if vertical?
        (for/fold ([out base])
                  ([col (in-list
                         (list (- center-col OUTPUT-WALL-OFFSET)
                               (+ center-col OUTPUT-WALL-OFFSET)))])
          (paint-col out col 0))
        (for/fold ([out base])
                  ([row (in-list
                         (list (- center-row OUTPUT-WALL-OFFSET)
                               (+ center-row OUTPUT-WALL-OFFSET)))])
          (paint-row out row 0))))
  (define with-crossbar
    (if vertical?
        (for/fold ([out with-walls]) ([row (in-list drows)])
          (paint-row out row 0))
        (for/fold ([out with-walls]) ([col (in-list dcols)])
          (paint-col out col 0))))
  (define half (quotient (- line-length 1) 2))
  (for/fold ([out with-crossbar]) ([index (in-range line-length)])
    (if vertical?
        (let ([row (+ (- center-row half) index)])
          (if (and (>= row 0) (< row height))
              (set-cell out row center-col 5)
              out))
        (let ([col (+ (- center-col half) index)])
          (if (and (>= col 0) (< col width))
              (set-cell out center-row col 5)
              out)))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)

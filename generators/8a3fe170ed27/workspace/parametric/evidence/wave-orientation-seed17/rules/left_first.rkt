#lang racket
(require json racket/list)

(define FIRST-SHIFT -1)
(define CYCLE (list 0 FIRST-SHIFT 0 (- FIRST-SHIFT)))

(define (active-row? row)
  (for/or ([value (in-list row)])
    (not (= value 0))))

(define (shift-row row dc)
  (define width (length row))
  (for/list ([destination (in-range width)])
    (define source (- destination dc))
    (if (and (<= 0 source) (< source width))
        (list-ref row source)
        0)))

(define (solve grid)
  (define active-rows
    (for/list ([row (in-list grid)]
               [row-index (in-naturals)]
               #:when (active-row? row))
      row-index))
  (if (null? active-rows)
      grid
      (let ([anchor (last active-rows)])
        (for/list ([row (in-list grid)]
                   [row-index (in-naturals)])
          (if (active-row? row)
              (shift-row row
                         (list-ref CYCLE
                                   (modulo (- anchor row-index) 4)))
              row)))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)

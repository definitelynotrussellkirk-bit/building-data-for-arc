#lang racket
(require json)

(define SCALE 2)

(define (expand-row row)
  (apply append
         (for/list ([value (in-list row)])
           (make-list SCALE value))))

(define (solve grid)
  (apply append
         (for/list ([row (in-list grid)])
           (define expanded (expand-row row))
           (make-list SCALE expanded))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)

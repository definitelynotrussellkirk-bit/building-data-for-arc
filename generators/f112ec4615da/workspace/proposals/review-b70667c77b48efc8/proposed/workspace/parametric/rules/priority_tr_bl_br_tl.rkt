#lang racket
(require json)

(define PRIORITY '(tr bl br tl))
(define grid (read-json))
(define H (length grid))
(define W (length (first grid)))
(define HH (quotient H 2))
(define HW (quotient W 2))

(define (cell r c)
  (list-ref (list-ref grid r) c))

(define (role-value role r c)
  (case role
    [(tl) (cell r c)]
    [(tr) (cell r (+ c HW))]
    [(bl) (cell (+ r HH) c)]
    [(br) (cell (+ r HH) (+ c HW))]
    [else (error 'overlay-priority "unknown role ~a" role)]))

(define output
  (for/list ([r (in-range HH)])
    (for/list ([c (in-range HW)])
      (or (for/first ([role PRIORITY]
                      #:when (not (= (role-value role r c) 0)))
            (role-value role r c))
          0))))

(write-json output)
(newline)

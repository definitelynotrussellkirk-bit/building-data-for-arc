#lang racket
(require json)

(define STOP-AT-BLOCKER? #t)

(define input-grid (read-json))
(define H (length input-grid))
(define W (length (first input-grid)))
(define source (list->vector (map list->vector input-grid)))
(define out (list->vector (for/list ([row (in-list input-grid)]) (list->vector row))))

(define (cell grid r c) (vector-ref (vector-ref grid r) c))
(define (set-cell! grid r c value) (vector-set! (vector-ref grid r) c value))
(define (inside? r c) (and (<= 0 r) (< r H) (<= 0 c) (< c W)))

(define corners
  (list (list 0 0)
        (list 0 (- W 1))
        (list (- H 1) 0)
        (list (- H 1) (- W 1))))
(define marker
  (first
   (filter (lambda (point)
             (member (cell source (first point) (second point)) '(1 2 3 4)))
           corners)))
(define mr (first marker))
(define mc (second marker))
(define marker-color (cell source mr mc))
(define direction
  (cond [(= marker-color 1) '(-1 0)]
        [(= marker-color 2) '(0 1)]
        [(= marker-color 3) '(1 0)]
        [else '(0 -1)]))
(define dr (first direction))
(define dc (second direction))

(for* ([r (in-range H)] [c (in-range W)])
  (define value (cell source r c))
  (unless (or (= value 0) (= value 5) (and (= r mr) (= c mc)))
    (let loop ([rr (+ r dr)] [cc (+ c dc)])
      (when (inside? rr cc)
        (unless (and STOP-AT-BLOCKER? (= (cell source rr cc) 5))
          (set-cell! out rr cc value)
          (loop (+ rr dr) (+ cc dc)))))))

(write-json (for/list ([row (in-vector out)]) (vector->list row)))
(newline)

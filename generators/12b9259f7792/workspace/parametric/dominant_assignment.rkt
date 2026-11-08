(rule!
  (let ((dummy 0))
    (define markers
      (filter (lambda (cell) (and (>= (third cell) 1) (<= (third cell) 4)))
              (grid-cells g)))
    (define blobs
      (filter (lambda (o) (= (obj-color o) 5)) (objects g 0)))
    (define (dist marker obj)
      (apply min
             (map (lambda (p)
                    (+ (abs (- (first p) (first marker)))
                       (abs (- (second p) (second marker)))))
                  (obj-cells obj))))
    ;; Step A: replace every gray component by its nearest marker color.
    (define assigned
      (for/fold ([out g]) ([obj (in-list blobs)])
        (let ((best (first (sort markers (lambda (a b) (< (dist a obj) (dist b obj)))))))
          (paint-cells out (obj-cells obj) (third best)))))
    ;; Intermediate: total assigned blob area for each marker color.
    (define colors (remove-duplicates (map third markers)))
    (define (assigned-area color)
      (- (length (filter (lambda (cell) (= (third cell) color)) (grid-cells assigned)))
         (length (filter (lambda (cell) (= (third cell) color)) markers))))
    (define winner
      (first
       (sort colors
             (lambda (a b)
               (or (> (assigned-area a) (assigned-area b))
                   (and (= (assigned-area a) (assigned-area b)) (< a b)))))))
    (define (marker-position? r c)
      (any? (lambda (m) (and (= r (first m)) (= c (second m)))) markers))
    ;; Step B: keep all original markers, but retain only blobs assigned to
    ;; the marker color with greatest total assigned area.
    (grid-from-fn
     (rows assigned) (cols assigned)
     (lambda (r c)
       (let ((v (at assigned r c)))
         (cond [(marker-position? r c) (at g r c)]
               [(and (>= v 1) (<= v 4) (not (= v winner))) 0]
               [else v]))))))

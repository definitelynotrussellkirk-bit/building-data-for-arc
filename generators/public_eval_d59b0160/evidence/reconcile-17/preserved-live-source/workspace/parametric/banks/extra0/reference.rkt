(rule!
 ;; Read the distinct non-background, non-green colors inside the green key.
 ;; Each separate multicolor panel contains a black rectangle and colored marks.
 ;; Replace every panel containing ALL key colors with orange. Extra colors,
 ;; duplicate marks and the positions of marks do not affect set containment.
 (lambda (g)
  (let ()
   (define output-policy "all_matches")
   (define bg 7)
   (define key-box (bbox-of-cells (find-color g 3)))
   (define key-cells (positions-in-rect (first key-box) (second key-box) (third key-box) (fourth key-box)))
   (define key-colors
    (remove-duplicates (filter (lambda (v) (and (not (= v bg)) (not (= v 3))))
     (map (lambda (p) (at g (first p) (second p))) key-cells))))
   (define without-key (recolor-cells g key-cells bg))
   (define panels (objects-multicolor without-key bg))
   (define (palette o)
    (remove-duplicates (filter (lambda (v) (not (= v 0)))
      (map (lambda (p) (at g (first p) (second p))) (obj-cells o)))))
   (define (matches? o) (for/and ((v key-colors)) (member v (palette o))))
   (define matches (filter matches? panels))
   (define survivors (filter (lambda (o) (not (matches? o))) panels))
   (define erased
    (cond
     ((equal? output-policy "exact_colors")
      (filter (lambda (o) (and (matches? o) (= (length (palette o)) (length key-colors)))) panels))
     ((equal? output-policy "any_color")
      (filter (lambda (o) (for/or ((v key-colors)) (member v (palette o)))) panels))
     (else matches)))
   (define stage-one
    (for/fold ((out g)) ((o erased)) (recolor-cells out (obj-cells o) bg)))
   (define area
    (cond
     ((or (null? matches) (member output-policy (list "all_matches" "exact_colors" "any_color"))) -1)
     ((equal? output-policy "smallest_area") (obj-size (pick-min matches obj-size)))
     ((equal? output-policy "largest_any") (obj-size (pick-max panels obj-size)))
     ((equal? output-policy "first_match") (obj-size (first matches)))
     ((equal? output-policy "key_count") (length key-colors))
     ((equal? output-policy "most_colors") (obj-size (pick-max matches (lambda (o) (length (palette o))))))
     ((equal? output-policy "second_largest")
      (if (> (length survivors) 1)
       (obj-size (second (sort survivors (lambda (a b) (> (obj-size a) (obj-size b)))))) -1))
     ((equal? output-policy "largest_duplicate")
      (let ((repeated (filter (lambda (o)
                       (> (count-if (lambda (x) (= (obj-size x) (obj-size o))) panels) 1)) panels)))
       (if (null? repeated) -1 (obj-size (pick-max repeated obj-size)))))
     (else (obj-size (pick-max matches obj-size)))))
   (for/fold ((out stage-one)) ((o survivors) #:when (= (obj-size o) area))
    (recolor-cells out (obj-cells o) bg)))))

(rule!
 (lambda (g)
  (define outermost-only? #f)
  (define pixels (apply append g))
  (define palette (remove-duplicates pixels))
  (define bg
   (first (sort palette >
                #:key (lambda (color)
                        (count (lambda (pixel) (= pixel color)) pixels)))))
  (define fg (first (filter (lambda (color) (not (= color bg))) palette)))

  ;; A component's complement includes every cell outside that component,
  ;; including other foreground components. Padding exposes the exterior.
  (define (cavity-of obj)
   (define box (obj-bbox obj))
   (define occupied (obj-cells obj))
   (define origin-r (- (first box) 1))
   (define origin-c (- (second box) 1))
   (define height (+ (- (third box) (first box)) 3))
   (define width (+ (- (fourth box) (second box)) 3))
   (define complement
    (for/list ([r (in-range height)])
     (for/list ([c (in-range width)])
      (if (member (list (+ origin-r r) (+ origin-c c)) occupied) 0 1))))
   (define enclosed
    (filter
     (lambda (region)
      (define bounds (obj-bbox region))
      (and (> (first bounds) 0) (> (second bounds) 0)
           (< (third bounds) (- height 1))
           (< (fourth bounds) (- width 1))))
     (objects complement 0)))
   (apply append
    (for/list ([region enclosed])
     (for/list ([cell (obj-cells region)])
      (list (+ origin-r (first cell)) (+ origin-c (second cell)))))))

  (define described
   (for/list ([obj (objects g bg)])
    (define cavity (cavity-of obj))
    (hash 'box (obj-bbox obj) 'cells (obj-cells obj)
          'cavity cavity 'frame? (not (null? cavity)))))
  (define (frame? obj) (hash-ref obj 'frame?))
  (define (inside-cavity? inner outer)
   (andmap (lambda (cell) (member cell (hash-ref outer 'cavity)))
           (hash-ref inner 'cells)))
  (define selected
   (if outermost-only?
       (filter
        (lambda (obj)
         (or (not (frame? obj))
             (not (ormap
                   (lambda (other)
                    (and (not (eq? obj other)) (frame? other)
                         (inside-cavity? obj other)))
                   described))))
        described)
       described))

  ;; Stage B consumes only the selected, input-dependent object collection.
  (define layout-objects selected)
  (define (axis-groups low-index high-index)
   (define intervals
    (apply append
     (for/list ([obj layout-objects])
      (define box (hash-ref obj 'box))
      (define lo (list-ref box low-index))
      (define hi (list-ref box high-index))
      (if (frame? obj)
          (list (cons lo lo) (cons hi hi))
          (list (cons lo hi))))))
   (define ordered (sort intervals < #:key car))
   (reverse
    (for/fold ([merged (list)]) ([interval ordered])
     (if (and (pair? merged) (<= (car interval) (cdar merged)))
         (cons (cons (caar merged) (max (cdar merged) (cdr interval)))
               (cdr merged))
         (cons interval merged)))))
  (define row-groups (axis-groups 0 2))
  (define column-groups (axis-groups 1 3))
  (define (compressed-position groups position)
   (let find ([remaining groups] [coordinate 0])
    (define interval (first remaining))
    (if (<= (car interval) position (cdr interval))
        coordinate
        (find (rest remaining) (+ coordinate 2)))))
  (define glyphs
   (for/list ([obj layout-objects])
    (define box (hash-ref obj 'box))
    (list (frame? obj)
          (compressed-position row-groups (first box))
          (compressed-position column-groups (second box))
          (compressed-position row-groups (third box))
          (compressed-position column-groups (fourth box)))))
  (define first-row
   (apply min (map (lambda (item) (if (first item) (second item) (- (second item) 1))) glyphs)))
  (define first-column
   (apply min (map (lambda (item) (if (first item) (third item) (- (third item) 1))) glyphs)))
  (define last-row
   (apply max (map (lambda (item) (if (first item) (fourth item) (+ (second item) 1))) glyphs)))
  (define last-column
   (apply max (map (lambda (item) (if (first item) (fifth item) (+ (third item) 1))) glyphs)))
  (for/list ([r (in-range first-row (+ last-row 1))])
   (for/list ([c (in-range first-column (+ last-column 1))])
    (if (ormap
         (lambda (item)
          (define r0 (second item))
          (define c0 (third item))
          (define r1 (fourth item))
          (define c1 (fifth item))
          (if (first item)
              (and (<= r0 r r1) (<= c0 c c1)
                   (or (= r r0) (= r r1) (= c c0) (= c c1)))
              (and (= r r0) (= c c0))))
         glyphs)
        fg bg)))))

(rule!
 ;; Recover one complete colored motif attached to a corner of a hollow zero
 ;; frame.  Normalize that motif to a top-left corner.  Every other participating
 ;; corner retains only the motif's deepest inward-diagonal cell; its color is
 ;; the color of the completed copy.  Reflect the recovered motif horizontally
 ;; and/or vertically into each marked corner, preserving the source copy.
 (lambda (g)
  (let ()
   (define rotate-transport? #f)
   (define use-source-color? #f)
   (define first-target-only? #f)
   (define h (rows g))
   (define w (cols g))
   (define bg (mode g -1))
   ;; Kinds: 0=TL, 1=TR, 2=BL, 3=BR.
   (define edge-dirs
    '((((1 0) (0 1))) (((1 0) (0 -1))) (((-1 0) (0 1))) (((-1 0) (0 -1)))))
   (define out-dirs
    '((((-1 0) (0 -1))) (((-1 0) (0 1))) (((1 0) (0 -1))) (((1 0) (0 1)))))
   (define (dirs table kind) (first (list-ref table kind)))
   (define (reflect-offset dr dc kind)
    (cond [(= kind 0) (list dr dc)]
          [(= kind 1) (list dr (- dc))]
          [(= kind 2) (list (- dr) dc)]
          [else (list (- dr) (- dc))]))
   (define (rotate-offset dr dc kind)
    (cond [(= kind 0) (list dr dc)]
          [(= kind 1) (list dc (- dr))]
          [(= kind 2) (list (- dc) dr)]
          [else (list (- dr) (- dc))]))
   (define (edge-metric r c dr dc)
    (let loop ([step 1] [count 0] [saw-zero? #f])
     (let ([rr (+ r (* step dr))] [cc (+ c (* step dc))])
      (if (or (not (in-bounds? rr cc h w)) (= (at g rr cc) bg))
          (list count saw-zero?)
          (loop (+ step 1) (+ count 1) (or saw-zero? (= (at g rr cc) 0)))))))
   (define (candidate-corner? r c kind)
    (let* ([ds (dirs edge-dirs kind)]
           [d1 (first ds)] [d2 (second ds)]
           [r1 (+ r (first d1))] [c1 (+ c (second d1))]
           [r2 (+ r (first d2))] [c2 (+ c (second d2))])
     (and (in-bounds? r1 c1 h w) (in-bounds? r2 c2 h w)
          (not (= (at g r1 c1) bg)) (not (= (at g r2 c2) bg))
          (let ([m1 (edge-metric r c (first d1) (second d1))]
                [m2 (edge-metric r c (first d2) (second d2))])
           (and (>= (first m1) 3) (second m1)
                (>= (first m2) 3) (second m2)
                (for/and ([d (in-list (dirs out-dirs kind))])
                 (let ([rr (+ r (first d))] [cc (+ c (second d))])
                  (or (not (in-bounds? rr cc h w))
                      (not (= (at g rr cc) 0))))))))))
   (define (corner-kind r c)
    (for/first ([kind (in-range 4)] #:when (candidate-corner? r c kind)) kind))
   (define corners
    (filter-map
     (lambda (p)
      (let ([r (first p)] [c (second p)])
       (if (= (at g r c) bg) #f
        (let ([kind (corner-kind r c)])
         (if (number? kind) (list r c kind) #f)))))
     (grid-positions g)))
   (define (colored-around corner)
    (define r (first corner))
    (define c (second corner))
    (define kind (third corner))
    (for*/list ([dr (in-range -4 5)] [dc (in-range -4 5)]
                #:when (let ([rr (+ r dr)] [cc (+ c dc)])
                         (and (in-bounds? rr cc h w)
                              (not (= (at g rr cc) bg))
                              (not (= (at g rr cc) 0)))))
     (let ([off (reflect-offset dr dc kind)])
      (list off (at g (+ r dr) (+ c dc))))))
   (define around (map (lambda (corner) (list corner (colored-around corner))) corners))
   (define source-records
    (filter-map
     (lambda (record)
      (define corner (first record))
      (define items (second record))
      (define outward
       (filter (lambda (item)
                (let ([off (first item)])
                 (or (< (first off) 0) (< (second off) 0)))) items))
      (define colors (remove-duplicates (map second outward)))
      (if (and (>= (length outward) 2) (= (length colors) 1))
          (let* ([color (first colors)]
                 [sprite (remove-duplicates
                          (map first (filter (lambda (item) (= (second item) color)) items)))])
           (if (for/or ([off (in-list sprite)])
                (and (= (first off) (second off)) (> (first off) 0)))
               (list corner color sprite) #f))
          #f))
     around))
   (when (empty? source-records) (error 'corner-motif "no complete source motif"))
   (define canonical (third (first source-records)))
   (unless (for/and ([record (in-list source-records)])
            (and (= (length (third record)) (length canonical))
                 (for/and ([off (in-list canonical)]) (member off (third record)))))
    (error 'corner-motif "source motifs disagree"))
   (define diag-depth
    (apply max
     (for/list ([off (in-list canonical)]
                #:when (and (= (first off) (second off)) (> (first off) 0)))
      (first off))))
   (define marker (list diag-depth diag-depth))
   (define source-corners (map first source-records))
   (define source-color (second (first source-records)))
   (define targets
    (filter-map
     (lambda (record)
      (define corner (first record))
      (define items (second record))
      (if (member corner source-corners) #f
       (let* ([r (first corner)] [c (second corner)] [kind (third corner)]
              [actual-marker (reflect-offset (first marker) (second marker) kind)]
              [mr (+ r (first actual-marker))] [mc (+ c (second actual-marker))])
        (if (not (in-bounds? mr mc h w)) #f
         (let* ([color (at g mr mc)]
                [hits (filter (lambda (item) (member (first item) canonical)) items)])
          (if (and (not (= color bg)) (not (= color 0))
                   (= (length hits) 1)
                   (equal? (first (first hits)) marker)
                   (= (second (first hits)) color))
              (list corner (if use-source-color? source-color color)) #f))))))
     around))
   (when (empty? targets) (error 'corner-motif "no target corners"))
   (define selected-targets (if first-target-only? (list (first targets)) targets))
   (for/fold ([out g]) ([target (in-list selected-targets)])
    (define corner (first target))
    (define color (second target))
    (define r (first corner))
    (define c (second corner))
    (define kind (third corner))
    (define cells
     (filter
      (lambda (p) (in-bounds? (first p) (second p) h w))
      (for/list ([off (in-list canonical)])
       (define actual
        (if rotate-transport?
            (rotate-offset (first off) (second off) kind)
            (reflect-offset (first off) (second off) kind)))
       (list (+ r (first actual)) (+ c (second actual))))))
    (recolor-cells out cells color)))))

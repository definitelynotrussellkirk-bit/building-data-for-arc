(rule!
 ;; The green L frames a set of key colors on orange, in any orientation.
 ;; Mask the whole legend before extracting multicolor rectangular panels.
 ;; Ignore black panel filler and repeated dots. In the canonical rule erase
 ;; a panel iff its palette contains every key color, retaining extra colors.
 ;; Alternatives select any overlap or an exactly equal palette. Preserve the
 ;; framed key and every unselected panel byte-for-byte, including border ones.
 (lambda (g)
  (let ()
   (define match-mode 'contains_all)
   (define frame (first (filter (lambda (o) (= (obj-color o) 3)) (objects g 7))))
   (define key-cells (positions-in-rect (obj-r1 frame) (obj-c1 frame) (obj-r2 frame) (obj-c2 frame)))
   (define key (remove-duplicates
    (filter (lambda (v) (and (not (= v 7)) (not (= v 3))))
     (map (lambda (p) (at g (first p) (second p))) key-cells))))
   (define masked (paint-cells g key-cells 7))
   (define panels (objects-multicolor masked 7))
   (define (selected? palette)
    (cond [(eq? match-mode 'contains_any) (for/or ([k key]) (member k palette))]
          [(eq? match-mode 'exact_palette)
           (and (= (length key) (length palette)) (for/and ([k key]) (member k palette)))]
          [else (for/and ([k key]) (member k palette))]))
   (for/fold ([out g]) ([panel panels])
    (let ([palette (remove-duplicates (filter (lambda (v) (not (= v 0)))
                    (map (lambda (p) (at g (first p) (second p))) (obj-cells panel))))])
     (if (selected? palette) (paint-cells out (obj-cells panel) 7) out))))))

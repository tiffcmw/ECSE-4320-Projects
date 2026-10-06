; scalar_unroll8 saxpy_s1 u32: largest loop body (25 instr) [truncated to 24]
ldp	w14, w15, [x13, #-0x10]
ldp	w16, w17, [x12, #-0x10]
madd	w14, w14, w8, w16
madd	w15, w15, w8, w17
stp	w14, w15, [x12, #-0x10]
ldp	w14, w15, [x13, #-0x8]
ldp	w16, w17, [x12, #-0x8]
madd	w14, w14, w8, w16
madd	w15, w15, w8, w17
stp	w14, w15, [x12, #-0x8]
ldp	w14, w15, [x13]
ldp	w16, w17, [x12]
madd	w14, w14, w8, w16
madd	w15, w15, w8, w17
ldp	w16, w17, [x13, #0x8]
ldp	w0, w3, [x12, #0x8]
madd	w16, w16, w8, w0
stp	w14, w15, [x12]
madd	w14, w17, w8, w3
sub	x10, x10, #0x8
stp	w16, w14, [x12, #0x8]
add	x12, x12, #0x20
add	x13, x13, #0x20
cmp	x11, x10

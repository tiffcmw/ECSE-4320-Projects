; scalar_unroll8 triad u32: largest loop body (26 instr) [truncated to 24]
ldp	w15, w16, [x14, #-0x10]
ldp	w17, w0, [x13, #-0x10]
madd	w15, w17, w8, w15
madd	w16, w0, w8, w16
stp	w15, w16, [x12, #-0x10]
ldp	w15, w16, [x14, #-0x8]
ldp	w17, w0, [x13, #-0x8]
madd	w15, w17, w8, w15
madd	w16, w0, w8, w16
stp	w15, w16, [x12, #-0x8]
ldp	w15, w16, [x14]
ldp	w17, w0, [x13]
madd	w15, w17, w8, w15
madd	w16, w0, w8, w16
ldp	w17, w0, [x14, #0x8]
ldp	w4, w5, [x13, #0x8]
madd	w17, w4, w8, w17
madd	w0, w5, w8, w0
stp	w15, w16, [x12]
sub	x10, x10, #0x8
stp	w17, w0, [x12, #0x8]
add	x12, x12, #0x20
add	x13, x13, #0x20
add	x14, x14, #0x20

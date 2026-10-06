; scalar_unroll8 mul u32: largest loop body (26 instr) [truncated to 24]
ldp	w14, w15, [x13, #-0x10]
ldp	w16, w17, [x12, #-0x10]
mul	w14, w16, w14
mul	w15, w17, w15
stp	w14, w15, [x11, #-0x10]
ldp	w14, w15, [x13, #-0x8]
ldp	w16, w17, [x12, #-0x8]
mul	w14, w16, w14
mul	w15, w17, w15
stp	w14, w15, [x11, #-0x8]
ldp	w14, w15, [x13]
ldp	w16, w17, [x12]
mul	w14, w16, w14
mul	w15, w17, w15
ldp	w16, w17, [x13, #0x8]
ldp	w0, w4, [x12, #0x8]
mul	w16, w0, w16
mul	w17, w4, w17
stp	w14, w15, [x11]
sub	x9, x9, #0x8
stp	w16, w17, [x11, #0x8]
add	x11, x11, #0x20
add	x12, x12, #0x20
add	x13, x13, #0x20

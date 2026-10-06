; scalar_unroll8 dot u32: largest loop body (21 instr)
ldp	w14, w15, [x13, #-0x10]
ldp	w16, w17, [x12, #-0x10]
madd	w9, w16, w14, w9
madd	w9, w17, w15, w9
ldp	w14, w15, [x13, #-0x8]
ldp	w16, w17, [x12, #-0x8]
madd	w9, w16, w14, w9
madd	w9, w17, w15, w9
ldp	w14, w15, [x13]
ldp	w16, w17, [x12]
madd	w9, w16, w14, w9
madd	w9, w17, w15, w9
ldp	w14, w15, [x13, #0x8]
ldp	w16, w17, [x12, #0x8]
madd	w9, w16, w14, w9
madd	w9, w17, w15, w9
sub	x10, x10, #0x8
add	x12, x12, #0x20
add	x13, x13, #0x20
cmp	x11, x10
b.ne	0x40 <ltmp0+0x40>

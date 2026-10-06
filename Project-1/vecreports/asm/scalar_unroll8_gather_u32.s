; scalar_unroll8 gather u32: largest loop body (33 instr) [truncated to 24]
ldp	w14, w15, [x13, #-0x10]
ldr	w14, [x1, x14, lsl #2]
ldp	w16, w17, [x12, #-0x10]
madd	w14, w14, w8, w16
ldr	w15, [x1, x15, lsl #2]
madd	w15, w15, w8, w17
stp	w14, w15, [x12, #-0x10]
ldp	w14, w15, [x13, #-0x8]
ldr	w14, [x1, x14, lsl #2]
ldp	w16, w17, [x12, #-0x8]
madd	w14, w14, w8, w16
ldr	w15, [x1, x15, lsl #2]
madd	w15, w15, w8, w17
stp	w14, w15, [x12, #-0x8]
ldp	w14, w15, [x13]
ldr	w14, [x1, x14, lsl #2]
ldp	w16, w17, [x12]
madd	w14, w14, w8, w16
ldr	w15, [x1, x15, lsl #2]
madd	w15, w15, w8, w17
ldp	w16, w17, [x13, #0x8]
ldr	w16, [x1, x16, lsl #2]
ldp	w0, w4, [x12, #0x8]
madd	w16, w16, w8, w0

; scalar_unroll8 stencil u32: largest loop body (31 instr) [truncated to 24]
ldp	w14, w15, [x12, #-0x14]
add	w13, w14, w13, lsl #1
ldp	w14, w16, [x12, #-0xc]
add	w13, w13, w14
add	w15, w15, w14, lsl #1
add	w15, w15, w16
stp	w13, w15, [x11, #-0xc]
add	w13, w14, w16, lsl #1
ldur	w14, [x12, #-0x4]
add	w13, w13, w14
add	w15, w16, w14, lsl #1
ldp	w16, w17, [x12]
add	w15, w15, w16
stp	w13, w15, [x11, #-0x4]
add	w13, w14, w16, lsl #1
add	w13, w13, w17
add	w14, w16, w17, lsl #1
ldp	w15, w16, [x12, #0x8]
add	w14, w14, w15
stp	w13, w14, [x11, #0x4]
add	w13, w17, w15, lsl #1
add	w14, w13, w16
add	w15, w15, w16, lsl #1
ldr	w13, [x12, #0x10]

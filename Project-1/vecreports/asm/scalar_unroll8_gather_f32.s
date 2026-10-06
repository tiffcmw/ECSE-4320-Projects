; scalar_unroll8 gather f32: largest loop body (33 instr) [truncated to 24]
ldp	w13, w14, [x12, #-0x10]
ldr	s1, [x1, x13, lsl #2]
ldp	s2, s3, [x11, #-0x10]
fmadd	s1, s0, s1, s2
ldr	s2, [x1, x14, lsl #2]
fmadd	s2, s0, s2, s3
stp	s1, s2, [x11, #-0x10]
ldp	w13, w14, [x12, #-0x8]
ldr	s1, [x1, x13, lsl #2]
ldp	s2, s3, [x11, #-0x8]
fmadd	s1, s0, s1, s2
ldr	s2, [x1, x14, lsl #2]
fmadd	s2, s0, s2, s3
stp	s1, s2, [x11, #-0x8]
ldp	w13, w14, [x12]
ldr	s1, [x1, x13, lsl #2]
ldp	s2, s3, [x11]
fmadd	s1, s0, s1, s2
ldr	s2, [x1, x14, lsl #2]
fmadd	s2, s0, s2, s3
ldp	w13, w14, [x12, #0x8]
ldr	s3, [x1, x13, lsl #2]
stp	s1, s2, [x11]
ldp	s1, s2, [x11, #0x8]

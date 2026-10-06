; scalar_unroll8 gather f64: largest loop body (33 instr) [truncated to 24]
ldp	w13, w14, [x12, #-0x10]
ldr	d1, [x1, x13, lsl #3]
ldp	d2, d3, [x11, #-0x20]
fmadd	d1, d0, d1, d2
ldr	d2, [x1, x14, lsl #3]
fmadd	d2, d0, d2, d3
stp	d1, d2, [x11, #-0x20]
ldp	w13, w14, [x12, #-0x8]
ldr	d1, [x1, x13, lsl #3]
ldp	d2, d3, [x11, #-0x10]
fmadd	d1, d0, d1, d2
ldr	d2, [x1, x14, lsl #3]
fmadd	d2, d0, d2, d3
stp	d1, d2, [x11, #-0x10]
ldp	w13, w14, [x12]
ldr	d1, [x1, x13, lsl #3]
ldp	d2, d3, [x11]
fmadd	d1, d0, d1, d2
ldr	d2, [x1, x14, lsl #3]
fmadd	d2, d0, d2, d3
ldp	w13, w14, [x12, #0x8]
ldr	d3, [x1, x13, lsl #3]
stp	d1, d2, [x11]
ldp	d1, d2, [x11, #0x10]

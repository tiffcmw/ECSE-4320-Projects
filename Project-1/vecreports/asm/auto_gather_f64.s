; auto gather f64: largest loop body (16 instr)
ldp	w12, w13, [x9, #-0x8]
ldp	w14, w15, [x9], #0x10
ldr	d1, [x1, x12, lsl #3]
ldr	d2, [x1, x13, lsl #3]
ldr	d3, [x1, x14, lsl #3]
ldr	d4, [x1, x15, lsl #3]
ldp	d5, d6, [x10, #-0x10]
ldp	d7, d16, [x10]
fmadd	d1, d0, d1, d5
fmadd	d2, d0, d2, d6
fmadd	d3, d0, d3, d7
fmadd	d4, d0, d4, d16
stp	d1, d2, [x10, #-0x10]
stp	d3, d4, [x10], #0x20
subs	x11, x11, #0x4
b.ne	0x24 <ltmp0+0x24>

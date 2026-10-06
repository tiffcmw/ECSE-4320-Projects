; scalar_norestrict stencil f64: largest loop body (8 instr)
ldp	d2, d3, [x8, #-0x8]
fmul	d3, d3, d0
fmadd	d2, d2, d1, d3
ldr	d3, [x8, #0x8]!
fmadd	d2, d3, d1, d2
str	d2, [x9], #0x8
subs	x10, x10, #0x1
b.ne	0x1c <ltmp0+0x1c>

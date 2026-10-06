; scalar stencil f64: largest loop body (8 instr)
ldur	d3, [x8, #-0x10]
fmul	d0, d0, d1
fmadd	d3, d3, d2, d0
ldr	d0, [x8], #0x8
fmadd	d3, d0, d2, d3
str	d3, [x9], #0x8
subs	x10, x10, #0x1
b.ne	0x20 <ltmp0+0x20>

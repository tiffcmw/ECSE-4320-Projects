; scalar triad f64: largest loop body (6 instr)
ldr	d1, [x1], #0x8
ldr	d2, [x2], #0x8
fmadd	d1, d0, d2, d1
str	d1, [x3], #0x8
subs	x0, x0, #0x1
b.ne	0x4 <ltmp0+0x4>

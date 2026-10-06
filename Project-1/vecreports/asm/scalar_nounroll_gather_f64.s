; scalar_nounroll gather f64: largest loop body (7 instr)
ldr	w8, [x3], #0x4
ldr	d1, [x1, x8, lsl #3]
ldr	d2, [x2]
fmadd	d1, d0, d1, d2
str	d1, [x2], #0x8
subs	x0, x0, #0x1
b.ne	0x4 <ltmp0+0x4>

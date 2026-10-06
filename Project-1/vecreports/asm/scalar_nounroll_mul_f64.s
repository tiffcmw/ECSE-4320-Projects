; scalar_nounroll mul f64: largest loop body (6 instr)
ldr	d0, [x1], #0x8
ldr	d1, [x2], #0x8
fmul	d0, d0, d1
str	d0, [x3], #0x8
subs	x0, x0, #0x1
b.ne	0x4 <ltmp0+0x4>

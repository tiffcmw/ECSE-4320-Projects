; scalar triad u32: largest loop body (6 instr)
ldr	w9, [x1], #0x4
ldr	w10, [x2], #0x4
madd	w9, w10, w8, w9
str	w9, [x3], #0x4
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>

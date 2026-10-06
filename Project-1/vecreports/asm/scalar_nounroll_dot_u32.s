; scalar_nounroll dot u32: largest loop body (5 instr)
ldr	w9, [x1], #0x4
ldr	w10, [x2], #0x4
madd	w8, w10, w9, w8
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>

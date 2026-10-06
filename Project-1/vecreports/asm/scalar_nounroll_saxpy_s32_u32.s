; scalar_nounroll saxpy_s32 u32: largest loop body (6 instr)
ldr	w9, [x1], #0x80
ldr	w10, [x2]
madd	w9, w9, w8, w10
str	w9, [x2], #0x80
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>

; auto_norestrict gather u32: largest loop body (7 instr)
ldr	w9, [x3], #0x4
ldr	w9, [x1, x9, lsl #2]
ldr	w10, [x2]
madd	w9, w9, w8, w10
str	w9, [x2], #0x4
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>

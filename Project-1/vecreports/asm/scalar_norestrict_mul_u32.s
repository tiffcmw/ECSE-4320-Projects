; scalar_norestrict mul u32: largest loop body (6 instr)
ldr	w8, [x1], #0x4
ldr	w9, [x2], #0x4
mul	w8, w9, w8
str	w8, [x3], #0x4
subs	x0, x0, #0x1
b.ne	0x4 <ltmp0+0x4>

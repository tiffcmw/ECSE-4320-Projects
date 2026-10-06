; scalar_nounroll stencil u32: largest loop body (7 instr)
ldur	w12, [x9, #-0x8]
add	w12, w12, w8, lsl #1
ldr	w8, [x9], #0x4
add	w12, w12, w8
str	w12, [x10], #0x4
subs	x11, x11, #0x1
b.ne	0x18 <ltmp0+0x18>

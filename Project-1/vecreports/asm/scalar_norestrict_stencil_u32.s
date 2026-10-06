; scalar_norestrict stencil u32: largest loop body (7 instr)
ldp	w11, w12, [x8, #-0x4]
add	w11, w11, w12, lsl #1
ldr	w12, [x8, #0x4]!
add	w11, w11, w12
str	w11, [x9], #0x4
subs	x10, x10, #0x1
b.ne	0x14 <ltmp0+0x14>

; fastmath saxpy_s16 u32: largest loop body (20 instr)
ldur	w13, [x11, #-0x80]
ldur	w14, [x11, #-0x40]
ldr	w15, [x11]
ldr	w16, [x11, #0x40]
ldur	w17, [x10, #-0x80]
ldur	w3, [x10, #-0x40]
ldr	w4, [x10]
ldr	w5, [x10, #0x40]
madd	w13, w13, w8, w17
madd	w14, w14, w8, w3
madd	w15, w15, w8, w4
madd	w16, w16, w8, w5
stur	w13, [x10, #-0x80]
stur	w14, [x10, #-0x40]
str	w15, [x10]
str	w16, [x10, #0x40]
add	x10, x10, #0x100
add	x11, x11, #0x100
subs	x12, x12, #0x4
b.ne	0x28 <ltmp0+0x28>

; auto_norestrict stencil u32: largest loop body (76 instr) [truncated to 24]
lsl	x8, x10, #2
add	x9, x1, x8
ldp	w10, w9, [x9, #-0x4]
add	w9, w10, w9, lsl #1
ldr	w10, [x1, x11, lsl #2]
add	w9, w9, w10
str	w9, [x2, x8]
mov	x10, x11
add	x11, x11, #0x1
cmp	x0, x11
b.ne	0x40 <ltmp0+0x40>
movi.2d	v0, #0000000000000000
ret
cmp	x8, #0x10
b.hs	0x84 <ltmp0+0x84>
mov	x9, #0x0                ; =0
b	0x110 <ltmp0+0x110>
and	x9, x8, #0xfffffffffffffff0
add	x10, x2, #0x24
add	x11, x1, #0x20
mov	x12, x9
ldp	q0, q1, [x11, #-0x20]
ldp	q2, q3, [x11]
ldur	q4, [x11, #-0x1c]

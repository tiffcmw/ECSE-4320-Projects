; auto_norestrict triad u32: largest loop body (62 instr) [truncated to 24]
lsl	x12, x9, #2
add	x10, x1, x12
add	x11, x2, x12
add	x12, x3, x12
sub	x9, x0, x9
ldr	w13, [x10], #0x4
ldr	w14, [x11], #0x4
madd	w13, w14, w8, w13
str	w13, [x12], #0x4
subs	x9, x9, #0x1
b.ne	0x28 <ltmp0+0x28>
movi.2d	v0, #0000000000000000
ret
mov	x9, #0x0                ; =0
sub	x10, x3, x1
cmp	x10, #0x40
b.lo	0x14 <ltmp0+0x14>
sub	x10, x3, x2
cmp	x10, #0x40
b.lo	0x14 <ltmp0+0x14>
cmp	x0, #0x10
b.hs	0x74 <ltmp0+0x74>
mov	x9, #0x0                ; =0
b	0xcc <ltmp0+0xcc>

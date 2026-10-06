; auto_norestrict mul u32: largest loop body (60 instr) [truncated to 24]
lsl	x11, x8, #2
add	x9, x1, x11
add	x10, x2, x11
add	x11, x3, x11
sub	x8, x0, x8
ldr	w12, [x9], #0x4
ldr	w13, [x10], #0x4
mul	w12, w13, w12
str	w12, [x11], #0x4
subs	x8, x8, #0x1
b.ne	0x24 <ltmp0+0x24>
movi.2d	v0, #0000000000000000
ret
mov	x8, #0x0                ; =0
sub	x9, x3, x1
cmp	x9, #0x40
b.lo	0x10 <ltmp0+0x10>
sub	x9, x3, x2
cmp	x9, #0x40
b.lo	0x10 <ltmp0+0x10>
cmp	x0, #0x10
b.hs	0x70 <ltmp0+0x70>
mov	x8, #0x0                ; =0
b	0xc4 <ltmp0+0xc4>

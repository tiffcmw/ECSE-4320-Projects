; auto_norestrict triad f64: largest loop body (39 instr) [truncated to 24]
lsl	x11, x8, #3
add	x9, x1, x11
add	x10, x2, x11
add	x11, x3, x11
sub	x8, x0, x8
ldr	d1, [x9], #0x8
ldr	d2, [x10], #0x8
fmadd	d1, d0, d2, d1
str	d1, [x11], #0x8
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
and	x8, x0, #0xfffffffffffffff8
add	x9, x1, #0x20
add	x10, x2, #0x20
add	x11, x3, #0x20

; auto_norestrict stencil f32: largest loop body (82 instr) [truncated to 24]
fmov	s0, #0.50000000
fmov	s1, #0.25000000
lsl	x8, x10, #2
add	x9, x1, x8
ldp	s2, s3, [x9, #-0x4]
fmul	s3, s3, s0
fmadd	s2, s2, s1, s3
ldr	s3, [x1, x11, lsl #2]
fmadd	s2, s3, s1, s2
str	s2, [x2, x8]
mov	x10, x11
add	x11, x11, #0x1
cmp	x0, x11
b.ne	0x48 <ltmp0+0x48>
movi.2d	v0, #0000000000000000
ret
fmov.4s	v0, #0.25000000
cmp	x8, #0x10
b.hs	0x94 <ltmp0+0x94>
mov	x9, #0x0                ; =0
b	0x124 <ltmp0+0x124>
and	x9, x8, #0xfffffffffffffff0
add	x10, x2, #0x24
add	x11, x1, #0x20

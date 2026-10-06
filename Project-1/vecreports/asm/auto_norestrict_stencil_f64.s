; auto_norestrict stencil f64: largest loop body (50 instr) [truncated to 24]
fmov	d0, #0.50000000
fmov	d1, #0.25000000
lsl	x8, x8, #3
add	x10, x1, x8
ldp	d2, d3, [x10, #-0x8]
fmul	d3, d3, d0
fmadd	d2, d2, d1, d3
ldr	d3, [x1, x9, lsl #3]
fmadd	d2, d3, d1, d2
str	d2, [x2, x8]
mov	x8, x9
add	x9, x9, #0x1
cmp	x0, x9
b.ne	0x48 <ltmp0+0x48>
movi.2d	v0, #0000000000000000
ret
and	x11, x10, #0xfffffffffffffff8
orr	x9, x11, #0x2
orr	x8, x11, #0x1
add	x12, x2, #0x28
add	x13, x1, #0x20
fmov.2d	v0, #0.50000000
fmov.2d	v1, #0.25000000
mov	x14, x11

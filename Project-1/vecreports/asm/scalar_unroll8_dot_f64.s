; scalar_unroll8 dot f64: largest loop body (41 instr) [truncated to 24]
ret
movi.2d	v0, #0000000000000000
ret
mov	x9, #0x0                ; =0
and	x10, x0, #0xfffffffffffffff8
neg	x10, x10
add	x11, x2, #0x20
add	x12, x1, #0x20
movi.2d	v0, #0000000000000000
ldp	d1, d2, [x12, #-0x20]
ldp	d3, d4, [x11, #-0x20]
fmadd	d0, d1, d3, d0
fmadd	d0, d2, d4, d0
ldp	d1, d2, [x12, #-0x10]
ldp	d3, d4, [x11, #-0x10]
fmadd	d0, d1, d3, d0
fmadd	d0, d2, d4, d0
ldp	d1, d2, [x12]
ldp	d3, d4, [x11]
fmadd	d0, d1, d3, d0
fmadd	d0, d2, d4, d0
ldp	d1, d2, [x12, #0x10]
ldp	d3, d4, [x11, #0x10]
fmadd	d0, d1, d3, d0

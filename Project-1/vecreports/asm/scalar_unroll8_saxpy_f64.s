; scalar_unroll8 saxpy f64: largest loop body (25 instr) [truncated to 24]
ldp	d1, d2, [x12, #-0x20]
ldp	d3, d4, [x11, #-0x20]
fmadd	d1, d0, d1, d3
fmadd	d2, d0, d2, d4
stp	d1, d2, [x11, #-0x20]
ldp	d1, d2, [x12, #-0x10]
ldp	d3, d4, [x11, #-0x10]
fmadd	d1, d0, d1, d3
fmadd	d2, d0, d2, d4
stp	d1, d2, [x11, #-0x10]
ldp	d1, d2, [x12]
ldp	d3, d4, [x11]
fmadd	d1, d0, d1, d3
fmadd	d2, d0, d2, d4
stp	d1, d2, [x11]
ldp	d1, d2, [x12, #0x10]
ldp	d3, d4, [x11, #0x10]
fmadd	d1, d0, d1, d3
fmadd	d2, d0, d2, d4
stp	d1, d2, [x11, #0x10]
sub	x9, x9, #0x8
add	x11, x11, #0x40
add	x12, x12, #0x40
cmp	x10, x9

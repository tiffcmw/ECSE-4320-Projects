; scalar_unroll8 triad f64: largest loop body (26 instr) [truncated to 24]
ldp	d1, d2, [x13, #-0x20]
ldp	d3, d4, [x12, #-0x20]
fmadd	d1, d0, d3, d1
fmadd	d2, d0, d4, d2
stp	d1, d2, [x11, #-0x20]
ldp	d1, d2, [x13, #-0x10]
ldp	d3, d4, [x12, #-0x10]
fmadd	d1, d0, d3, d1
fmadd	d2, d0, d4, d2
stp	d1, d2, [x11, #-0x10]
ldp	d1, d2, [x13]
ldp	d3, d4, [x12]
fmadd	d1, d0, d3, d1
fmadd	d2, d0, d4, d2
stp	d1, d2, [x11]
ldp	d1, d2, [x13, #0x10]
ldp	d3, d4, [x12, #0x10]
fmadd	d1, d0, d3, d1
fmadd	d2, d0, d4, d2
sub	x9, x9, #0x8
stp	d1, d2, [x11, #0x10]
add	x11, x11, #0x40
add	x12, x12, #0x40
add	x13, x13, #0x40

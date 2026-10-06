; scalar_unroll8 mul f64: largest loop body (26 instr) [truncated to 24]
ldp	d0, d1, [x13, #-0x20]
ldp	d2, d3, [x12, #-0x20]
fmul	d0, d0, d2
fmul	d1, d1, d3
stp	d0, d1, [x11, #-0x20]
ldp	d0, d1, [x13, #-0x10]
ldp	d2, d3, [x12, #-0x10]
fmul	d0, d0, d2
fmul	d1, d1, d3
stp	d0, d1, [x11, #-0x10]
ldp	d0, d1, [x13]
ldp	d2, d3, [x12]
fmul	d0, d0, d2
fmul	d1, d1, d3
ldp	d2, d3, [x13, #0x10]
ldp	d4, d5, [x12, #0x10]
fmul	d2, d2, d4
fmul	d3, d3, d5
stp	d0, d1, [x11]
sub	x9, x9, #0x8
stp	d2, d3, [x11, #0x10]
add	x11, x11, #0x40
add	x12, x12, #0x40
add	x13, x13, #0x40

; scalar_unroll8 stencil f64: largest loop body (38 instr) [truncated to 24]
fmul	d2, d2, d0
ldp	d3, d4, [x12, #-0x28]
fmadd	d2, d3, d1, d2
ldp	d3, d5, [x12, #-0x18]
fmadd	d2, d3, d1, d2
fmul	d6, d3, d0
fmadd	d4, d4, d1, d6
fmadd	d4, d5, d1, d4
stp	d2, d4, [x11, #-0x18]
fmul	d2, d5, d0
fmadd	d2, d3, d1, d2
ldp	d3, d4, [x12, #-0x8]
fmadd	d2, d3, d1, d2
fmul	d6, d3, d0
fmadd	d5, d5, d1, d6
fmadd	d5, d4, d1, d5
stp	d2, d5, [x11, #-0x8]
fmul	d2, d4, d0
fmadd	d2, d3, d1, d2
ldp	d3, d5, [x12, #0x8]
fmul	d6, d3, d0
fmadd	d4, d4, d1, d6
fmadd	d2, d3, d1, d2
fmadd	d4, d5, d1, d4

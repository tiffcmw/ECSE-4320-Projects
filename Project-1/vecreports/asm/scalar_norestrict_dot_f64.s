; scalar_norestrict dot f64: largest loop body (5 instr)
ldr	d1, [x1], #0x8
ldr	d2, [x2], #0x8
fmadd	d0, d1, d2, d0
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>

; scalar_unroll8 dot f32: largest loop body (21 instr)
ldp	s1, s2, [x12, #-0x10]
ldp	s3, s4, [x11, #-0x10]
fmadd	s0, s1, s3, s0
fmadd	s0, s2, s4, s0
ldp	s1, s2, [x12, #-0x8]
ldp	s3, s4, [x11, #-0x8]
fmadd	s0, s1, s3, s0
fmadd	s0, s2, s4, s0
ldp	s1, s2, [x12]
ldp	s3, s4, [x11]
fmadd	s0, s1, s3, s0
fmadd	s0, s2, s4, s0
ldp	s1, s2, [x12, #0x8]
ldp	s3, s4, [x11, #0x8]
fmadd	s0, s1, s3, s0
fmadd	s0, s2, s4, s0
sub	x9, x9, #0x8
add	x11, x11, #0x20
add	x12, x12, #0x20
cmp	x10, x9
b.ne	0x40 <ltmp0+0x40>

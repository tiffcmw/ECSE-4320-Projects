; scalar_unroll8 triad f32: largest loop body (26 instr) [truncated to 24]
ldp	s1, s2, [x13, #-0x10]
ldp	s3, s4, [x12, #-0x10]
fmadd	s1, s0, s3, s1
fmadd	s2, s0, s4, s2
stp	s1, s2, [x11, #-0x10]
ldp	s1, s2, [x13, #-0x8]
ldp	s3, s4, [x12, #-0x8]
fmadd	s1, s0, s3, s1
fmadd	s2, s0, s4, s2
stp	s1, s2, [x11, #-0x8]
ldp	s1, s2, [x13]
ldp	s3, s4, [x12]
fmadd	s1, s0, s3, s1
fmadd	s2, s0, s4, s2
stp	s1, s2, [x11]
ldp	s1, s2, [x13, #0x8]
ldp	s3, s4, [x12, #0x8]
fmadd	s1, s0, s3, s1
fmadd	s2, s0, s4, s2
sub	x9, x9, #0x8
stp	s1, s2, [x11, #0x8]
add	x11, x11, #0x20
add	x12, x12, #0x20
add	x13, x13, #0x20

; scalar_unroll8 saxpy f32: largest loop body (25 instr) [truncated to 24]
ldp	s1, s2, [x12, #-0x10]
ldp	s3, s4, [x11, #-0x10]
fmadd	s1, s0, s1, s3
fmadd	s2, s0, s2, s4
stp	s1, s2, [x11, #-0x10]
ldp	s1, s2, [x12, #-0x8]
ldp	s3, s4, [x11, #-0x8]
fmadd	s1, s0, s1, s3
fmadd	s2, s0, s2, s4
stp	s1, s2, [x11, #-0x8]
ldp	s1, s2, [x12]
ldp	s3, s4, [x11]
fmadd	s1, s0, s1, s3
fmadd	s2, s0, s2, s4
stp	s1, s2, [x11]
ldp	s1, s2, [x12, #0x8]
ldp	s3, s4, [x11, #0x8]
fmadd	s1, s0, s1, s3
fmadd	s2, s0, s2, s4
stp	s1, s2, [x11, #0x8]
sub	x9, x9, #0x8
add	x11, x11, #0x20
add	x12, x12, #0x20
cmp	x10, x9

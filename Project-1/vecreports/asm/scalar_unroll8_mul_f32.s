; scalar_unroll8 mul f32: largest loop body (26 instr) [truncated to 24]
ldp	s0, s1, [x13, #-0x10]
ldp	s2, s3, [x12, #-0x10]
fmul	s0, s0, s2
fmul	s1, s1, s3
stp	s0, s1, [x11, #-0x10]
ldp	s0, s1, [x13, #-0x8]
ldp	s2, s3, [x12, #-0x8]
fmul	s0, s0, s2
fmul	s1, s1, s3
stp	s0, s1, [x11, #-0x8]
ldp	s0, s1, [x13]
ldp	s2, s3, [x12]
fmul	s0, s0, s2
fmul	s1, s1, s3
ldp	s2, s3, [x13, #0x8]
ldp	s4, s5, [x12, #0x8]
fmul	s2, s2, s4
fmul	s3, s3, s5
stp	s0, s1, [x11]
sub	x9, x9, #0x8
stp	s2, s3, [x11, #0x8]
add	x11, x11, #0x20
add	x12, x12, #0x20
add	x13, x13, #0x20

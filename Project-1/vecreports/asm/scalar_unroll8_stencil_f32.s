; scalar_unroll8 stencil f32: largest loop body (38 instr) [truncated to 24]
fmul	s2, s2, s0
ldp	s3, s4, [x12, #-0x14]
fmadd	s2, s3, s1, s2
ldp	s3, s5, [x12, #-0xc]
fmadd	s2, s3, s1, s2
fmul	s6, s3, s0
fmadd	s4, s4, s1, s6
fmadd	s4, s5, s1, s4
stp	s2, s4, [x11, #-0xc]
fmul	s2, s5, s0
fmadd	s2, s3, s1, s2
ldp	s3, s4, [x12, #-0x4]
fmadd	s2, s3, s1, s2
fmul	s6, s3, s0
fmadd	s5, s5, s1, s6
fmadd	s5, s4, s1, s5
stp	s2, s5, [x11, #-0x4]
fmul	s2, s4, s0
fmadd	s2, s3, s1, s2
ldp	s3, s5, [x12, #0x4]
fmul	s6, s3, s0
fmadd	s4, s4, s1, s6
fmadd	s2, s3, s1, s2
fmadd	s4, s5, s1, s4

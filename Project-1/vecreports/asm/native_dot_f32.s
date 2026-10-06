; native dot f32: largest loop body (38 instr) [truncated to 24]
ldp	q1, q2, [x9, #-0x20]
ldp	q3, q4, [x9], #0x40
ldp	q5, q6, [x10, #-0x20]
ldp	q7, q16, [x10], #0x40
fmul.4s	v1, v1, v5
mov	s5, v1[3]
mov	s17, v1[2]
mov	s18, v1[1]
fmul.4s	v2, v2, v6
mov	s6, v2[3]
mov	s19, v2[2]
mov	s20, v2[1]
fmul.4s	v3, v3, v7
mov	s7, v3[3]
mov	s21, v3[2]
mov	s22, v3[1]
fmul.4s	v4, v4, v16
mov	s16, v4[3]
mov	s23, v4[2]
mov	s24, v4[1]
fadd	s0, s0, s1
fadd	s0, s0, s18
fadd	s0, s0, s17
fadd	s0, s0, s5

; scalar_unroll8 saxpy_s2 f32: largest loop body (37 instr) [truncated to 24]
ldur	s1, [x12, #-0x20]
ldur	s2, [x11, #-0x20]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x20]
ldur	s1, [x12, #-0x18]
ldur	s2, [x11, #-0x18]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x18]
ldur	s1, [x12, #-0x10]
ldur	s2, [x11, #-0x10]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x10]
ldur	s1, [x12, #-0x8]
ldur	s2, [x11, #-0x8]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x8]
ldr	s1, [x12]
ldr	s2, [x11]
fmadd	s1, s0, s1, s2
str	s1, [x11]
ldr	s1, [x12, #0x8]
ldr	s2, [x11, #0x8]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x8]

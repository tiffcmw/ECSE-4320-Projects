; scalar_unroll8 saxpy_s32 f32: largest loop body (37 instr) [truncated to 24]
ldr	s1, [x12]
ldr	s2, [x11]
fmadd	s1, s0, s1, s2
str	s1, [x11]
ldr	s1, [x12, #0x80]
ldr	s2, [x11, #0x80]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x80]
ldr	s1, [x12, #0x100]
ldr	s2, [x11, #0x100]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x100]
ldr	s1, [x12, #0x180]
ldr	s2, [x11, #0x180]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x180]
ldr	s1, [x12, #0x200]
ldr	s2, [x11, #0x200]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x200]
ldr	s1, [x12, #0x280]
ldr	s2, [x11, #0x280]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x280]

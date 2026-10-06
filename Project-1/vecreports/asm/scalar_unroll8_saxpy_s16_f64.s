; scalar_unroll8 saxpy_s16 f64: largest loop body (37 instr) [truncated to 24]
ldr	d1, [x12]
ldr	d2, [x11]
fmadd	d1, d0, d1, d2
str	d1, [x11]
ldr	d1, [x12, #0x80]
ldr	d2, [x11, #0x80]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x80]
ldr	d1, [x12, #0x100]
ldr	d2, [x11, #0x100]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x100]
ldr	d1, [x12, #0x180]
ldr	d2, [x11, #0x180]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x180]
ldr	d1, [x12, #0x200]
ldr	d2, [x11, #0x200]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x200]
ldr	d1, [x12, #0x280]
ldr	d2, [x11, #0x280]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x280]

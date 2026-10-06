; scalar_unroll8 saxpy_s32 u32: largest loop body (37 instr) [truncated to 24]
ldr	w14, [x13]
ldr	w15, [x12]
madd	w14, w14, w8, w15
str	w14, [x12]
ldr	w14, [x13, #0x80]
ldr	w15, [x12, #0x80]
madd	w14, w14, w8, w15
str	w14, [x12, #0x80]
ldr	w14, [x13, #0x100]
ldr	w15, [x12, #0x100]
madd	w14, w14, w8, w15
str	w14, [x12, #0x100]
ldr	w14, [x13, #0x180]
ldr	w15, [x12, #0x180]
madd	w14, w14, w8, w15
str	w14, [x12, #0x180]
ldr	w14, [x13, #0x200]
ldr	w15, [x12, #0x200]
madd	w14, w14, w8, w15
str	w14, [x12, #0x200]
ldr	w14, [x13, #0x280]
ldr	w15, [x12, #0x280]
madd	w14, w14, w8, w15
str	w14, [x12, #0x280]

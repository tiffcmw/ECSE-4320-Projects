; scalar_unroll8 saxpy_s16 u32: largest loop body (37 instr) [truncated to 24]
ldur	w14, [x13, #-0x100]
ldur	w15, [x12, #-0x100]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x100]
ldur	w14, [x13, #-0xc0]
ldur	w15, [x12, #-0xc0]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0xc0]
ldur	w14, [x13, #-0x80]
ldur	w15, [x12, #-0x80]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x80]
ldur	w14, [x13, #-0x40]
ldur	w15, [x12, #-0x40]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x40]
ldr	w14, [x13]
ldr	w15, [x12]
madd	w14, w14, w8, w15
str	w14, [x12]
ldr	w14, [x13, #0x40]
ldr	w15, [x12, #0x40]
madd	w14, w14, w8, w15
str	w14, [x12, #0x40]

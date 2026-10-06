; scalar_unroll8 saxpy_s2 u32: largest loop body (37 instr) [truncated to 24]
ldur	w14, [x13, #-0x20]
ldur	w15, [x12, #-0x20]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x20]
ldur	w14, [x13, #-0x18]
ldur	w15, [x12, #-0x18]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x18]
ldur	w14, [x13, #-0x10]
ldur	w15, [x12, #-0x10]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x10]
ldur	w14, [x13, #-0x8]
ldur	w15, [x12, #-0x8]
madd	w14, w14, w8, w15
stur	w14, [x12, #-0x8]
ldr	w14, [x13]
ldr	w15, [x12]
madd	w14, w14, w8, w15
str	w14, [x12]
ldr	w14, [x13, #0x8]
ldr	w15, [x12, #0x8]
madd	w14, w14, w8, w15
str	w14, [x12, #0x8]

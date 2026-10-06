; auto_norestrict saxpy_s32 f64: largest loop body (8 instr)
ldr	d1, [x1]
ldr	d2, [x2]
fmadd	d1, d0, d1, d2
str	d1, [x2]
add	x2, x2, #0x100
add	x1, x1, #0x100
subs	x0, x0, #0x1
b.ne	0x4 <ltmp0+0x4>

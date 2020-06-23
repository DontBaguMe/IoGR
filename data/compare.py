import os

f_vanilla = open("h:\\iogr\\vanilla.bin","rb")
f_rando = open("h:\\iogr\\rando.sfc","rb")
f_mask = open("h:\\iogr\\mask.bin", "wb")

van_byte = f_vanilla.read(1)
ran_byte = f_rando.read(1)
while van_byte != b"":
    if van_byte == b"\xff" and ran_byte != b"\xff":
        f_mask.write(b"\x11")
    elif van_byte == b"\xff" and ran_byte == b"\xff":
        f_mask.write(b"\xff")
    else:
        f_mask.write(b"\x00")
    van_byte = f_vanilla.read(1)
    ran_byte = f_rando.read(1)

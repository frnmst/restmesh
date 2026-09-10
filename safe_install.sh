#!/bin/bash

# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

read -r -d '' payload << 'EOF'
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

local_hashes="7daa970392429180e70f4be71ad5513404307a0724c2b0cd6a4e2ae6e1fb36aa925581cda3d408589d8c8ee814d4af18e1f334a09080a4b684e93435e697c81ef8b8f4e1474cccb2eccb23ed7e1c0b3fee3d9b992ac882db57dd54396ef660f7" && remote_hashes=$(curl https://pypi.org/pypi/restmesh/json | jq '.urls[] | .digests | to_entries[] | select(.key != "blake2b_256") | .value' | tr -d '"' | sort | tr -d "\n") && [ ${local_hashes} = ${remote_hashes} ] && export PIP_ONLY_BINARY=:all: && pipx install restmesh==0.6.0
-----BEGIN PGP SIGNATURE-----

iQIzBAEBCgAdFiEECQ7wtO7QEmICo89RJBFu2FZmeAoFAmqi0/IACgkQJBFu2FZm
eAr6ew//dUfRnRzWP3d03K6ZR4zi7QS96NGSoPkGPZTrpesXVMDzl74qIjSRL7ht
10ezayMle7SZOy6I9NUhifojMl90iLyQWvM3IEjx63pc31+s0dpcSZLMy8HUFuHu
OYCl7zfoMt7PKG9GHtoUqFpm98K4ys8edKkIoVtEUHrziT9pORWUSoyCe9kVoNG4
HfRiSTrR+MOKIZXCmLrWHusK/tsn5pTbr6EhQ4+3TgewiOL++/77GBWL/Nmr995+
KNck3suUjWSKWWW12wHMnNCXuguW91/LAPh3GMHmgqc4/RJZtldsv9/HQOQGOv6i
RYVWQ1iaoveBAQmNGRfAGduFiLrbD8ecZJQwmxAebvAGLQYMot5Y3tR/VNUhSqwK
vJpKEcU3qUTB0RhMzQM2KB6Xy9LFPcaZfFB5Qkk7n3IdWSBIV4UfmQ5LX9EOEfHc
/bHRCSfeHsnBbHxB2PJd4gJHL2oA3kyjgFWT1cvswddQ+tl4UGcQpnuQG9BMu+8e
zVDd4sPVzgAsn3yKQRy/XVDZ6wxWVZ2NtLIuwTHzvNoMhRRbRwTe9xd3GhTDTIyU
RcALUDmsUlC92O3ofGmjF0NiZILhhpXMzSGoGXN8oY+R5Rs61PYaPGSIKl3So4Ss
eQvVm7spcjj8d+WXRsNVx6s4G+e+2kdXkidWWnV5k8OAEkfJDaY=
=m2h0
-----END PGP SIGNATURE-----
EOF
which curl pipx sort tr jq echo && echo "${payload}" | gpg --verify - && { echo "${payload}" | gpg --decrypt - | sh; } || exit 1

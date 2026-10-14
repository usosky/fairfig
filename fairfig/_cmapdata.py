"""Colour-map lookup tables embedded so fairfig has no extra dependencies.

batlow (sequential) and vik (diverging) from the Scientific colour maps,
version 8, by Fabio Crameri (doi:10.5281/zenodo.1243862), as distributed in
the cmcrameri package. Cite: Crameri, F., Shephard, G.E. & Heron, P.J. (2020)
The misuse of colour in science communication. Nat. Commun. 11, 5444.

MIT License - Colormaps copyright (c) 2020 Fabio Crameri.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions: The above copyright
notice and this permission notice shall be included in all copies or
substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS",
WITHOUT WARRANTY OF ANY KIND.
"""

BATLOW = """
011959 021b59 031c5a 041e5a 051f5a 06215b 07225b 07245b 08255b 09275c 0a285c
0a2a5c 0b2b5c 0b2d5d 0c2e5d 0c2f5d 0d315d 0d325e 0d335e 0e355e 0e365e 0e375e
0f385f 0f395f 0f3b5f 0f3c5f 103d5f 103e5f 103f60 104060 114160 114260 114360
114460 124561 124661 124761 124861 134961 134a61 134b61 144c62 144d62 144e62
154f62 154f62 165062 165162 175262 175362 185462 185562 195662 195762 1a5762
1b5862 1b5962 1c5a62 1d5b62 1e5c62 1e5d62 1f5d61 205e61 215f61 226061 236060
246160 256260 26635f 27635f 28645f 2a655e 2b655e 2c665d 2d675d 2f675c 30685c
31695b 33695a 346a5a 356a59 376b58 386c58 3a6c57 3b6d56 3c6d56 3e6e55 3f6e54
416f53 426f52 447052 457051 477150 48714f 4a724e 4c724d 4d734d 4f734c 50744b
52744a 537549 557548 577647 587646 5a7745 5b7745 5d7844 5f7843 607942 627941
637a40 657a3f 677b3e 687b3e 6a7b3d 6c7c3c 6d7c3b 6f7d3a 717d39 737e38 747e38
767f37 787f36 798035 7b8034 7d8134 7f8133 818232 828231 848331 868330 88842f
8a842f 8c852e 8e852e 8f862d 91862d 93872c 95872c 97882c 99882c 9b892b 9d892b
9f892b a18a2b a38a2c a58b2c a78b2c a98c2c ab8c2d ad8c2d af8d2e b18d2f b38e2f
b58e30 b78e31 b98f32 bb8f33 bd8f34 be9035 c09036 c29037 c49138 c6913a c8913b
ca923c cb923e cd923f cf9340 d19342 d29343 d49445 d69446 d89448 d9954a db954b
dd954d de964f e09651 e19752 e39754 e49756 e69858 e7985a e9995c ea995e eb9a60
ed9a62 ee9b64 ef9b67 f09c69 f19d6b f29d6d f39e70 f49f72 f59f74 f6a077 f7a179
f8a17b f8a27e f9a380 f9a382 faa485 faa587 fba689 fba68c fca78e fca890 fca993
fca995 fdaa97 fdab9a fdac9c fdac9e fdada0 fdaea2 fdafa5 fdafa7 fdb0a9 fdb1ab
fdb2ad fdb2af fdb3b1 fdb4b4 fdb4b6 fdb5b8 fdb6ba fdb7bc fdb7be fdb8c0 fdb9c2
fdbac4 fdbac7 fdbbc9 fdbccb fdbccd fcbdcf fcbed1 fcbfd3 fcbfd6 fcc0d8 fcc1da
fcc2dc fcc3df fcc3e1 fcc4e3 fcc5e5 fbc6e8 fbc6ea fbc7ec fbc8ef fbc9f1 fbcaf3
fbcaf6 facbf8 faccfa
""".split()

VIK = """
001261 011462 011563 011764 011865 011a66 021c67 021d68 021f69 02206a 02226b
02236c 02256d 02276e 02286f 022a70 022b71 022d72 022e73 023074 023175 023376
023477 023678 023779 02397a 023a7b 033c7c 033e7d 033f7e 03417f 034280 034481
034582 034783 034984 034a85 044c86 044d87 044f88 055189 05528a 06548b 06568c
07578d 08598f 095b90 0b5d91 0c5e92 0e6093 106294 116496 136697 156798 176999
196b9a 1c6d9c 1e6f9d 20719e 2373a0 2575a1 2877a2 2b79a4 2d7ba5 307da6 337fa8
3681a9 3983ab 3c85ac 3f87ad 4289af 458bb0 488db2 4b90b3 4e92b4 5194b6 5496b7
5798b9 5a9aba 5d9cbb 619ebd 64a0be 67a2c0 6aa4c1 6da6c2 71a8c4 74aac5 77acc6
7aaec8 7db0c9 80b2ca 84b4cc 87b6cd 8ab8ce 8dbad0 90bcd1 94bed2 97c0d4 9ac2d5
9dc4d6 a0c5d8 a3c7d9 a7c9da aacbdc adcddd b0cfde b3d1df b6d3e1 bad5e2 bdd6e3
c0d8e4 c3dae5 c6dbe6 c9dde7 ccdfe8 cfe0e8 d2e1e9 d5e3e9 d8e4e9 dbe5e9 dee6e9
e0e6e9 e2e7e8 e5e7e8 e7e7e7 e8e7e5 eae6e4 ebe6e2 ece5e0 ede4de eee3dc eee1da
eee0d8 eeded5 eeddd3 eedbd0 eed9cd edd7cb edd5c8 ecd3c5 ecd1c3 ebd0c0 eacebd
e9ccba e9cab8 e8c8b5 e7c6b2 e6c4b0 e5c1ad e4bfaa e4bea8 e3bca5 e2baa2 e1b8a0
e0b69d dfb49a dfb298 deb095 ddae93 dcac90 dbaa8d dba88b daa688 d9a486 d8a283
d7a081 d69f7e d69d7c d59b79 d49977 d39774 d39572 d29470 d1926d d0906b cf8e68
cf8c66 ce8b64 cd8961 cc875f cc855d cb835a ca8258 c98056 c97e53 c87c51 c77b4f
c6794c c6774a c57548 c47445 c37243 c27041 c26e3f c16d3c c06b3a bf6938 be6736
be6533 bd6431 bc622f bb602d ba5e2a b85c28 b75a26 b65824 b55521 b3531f b2511d
b04f1b af4c18 ad4a16 ab4814 a94512 a74310 a5400f a33e0d a13c0b 9f390a 9c3709
9a3508 983307 963107 942f06 912d06 8f2b06 8d2906 8b2706 892606 872406 852206
832106 811f06 7f1e06 7e1d06 7c1b06 7a1a06 781806 761706 741506 731406 711307
6f1107 6d1007 6c0e07 6a0d07 680c07 670a07 650907 630707 620607 600408 5e0308
5d0208 5b0108 590008
""".split()

"""Approximate Simutrans full-night rendering of a sprite sheet (simgraph16.cc
display_day_night_shift at night=4, light_level=0), for previews."""
import numpy as np

RGBTAB = [0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
          0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
          0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
          0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF]
NIGHT_LIGHTS = [0xD3C380, 0x80C3D3, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
                0xC9C9C9, 0xDFDFDF, 0xFFFFE3, 0xD3C380, 0xD3C380, 0xE100E1, 0x0101FF]
T = (231, 255, 255)
RG, B = 0.75 ** 4, 0.83 ** 4


def night(arr):
    a = arr.astype(np.int64)
    v = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    out = np.zeros_like(a)
    # plain pixels: RGB555 quantisation then darkening
    q = (a >> 3) * 255 // 31
    out[..., 0] = q[..., 0] * RG
    out[..., 1] = q[..., 1] * RG
    out[..., 2] = q[..., 2] * B
    for i, c in enumerate(RGBTAB):
        m = v == c
        if not m.any():
            continue
        if i >= 16:
            n = NIGHT_LIGHTS[i - 16]
            out[m] = ((n >> 16) & 255, (n >> 8) & 255, n & 255)
        else:  # player colours: darkened like plain pixels
            out[m, 0] = ((c >> 16) & 255) * RG; out[m, 1] = ((c >> 8) & 255) * RG; out[m, 2] = (c & 255) * B
    tm = np.all(arr == np.array(T), axis=2)
    out[tm] = T
    return out.clip(0, 255).astype(np.uint8)

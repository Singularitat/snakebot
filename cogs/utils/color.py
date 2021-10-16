def hsslv(r, g, b):
    """Gets HSL and HSV values from rgb and returns them.

    r: int
    g: int
    b: int
    """
    maxc = max(r, g, b)
    minc = min(r, g, b)
    sumc = maxc + minc

    rangec = maxc - minc

    lum = sumc / 2.0

    if minc == maxc:
        return 0.0, 0.0, 0.0, lum, maxc
    sv = rangec / maxc
    if lum <= 0.5:
        sl = sv
    else:
        sl = rangec / (2.0 - sumc)

    rc = (maxc - r) / rangec
    gc = (maxc - g) / rangec
    bc = (maxc - b) / rangec

    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    h = (h / 6.0) % 1.0

    return h, sv, sl, lum, maxc

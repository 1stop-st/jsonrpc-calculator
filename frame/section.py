from math import pi, sqrt


def ordered_args(arg_names, *args, **kwargs):
    for arg in args:
        yield arg
    for key in arg_names[len(args):]:
        if key in kwargs:
            yield kwargs[key]


def mandate(func, arg_names, *args, **kwargs):
    return func(*ordered_args(arg_names, *args, **kwargs))


def properties(shape, *args, **kwargs):
    if shape == 'H':
        arg_names = 'H', 'B', 'tw', 'tf', 'r'
        func = h_properties
    elif shape == 'T':
        arg_names = 'H', 'B', 'tw', 'tf', 'r'
        func = t_properties
    elif shape == 'I':
        arg_names = 'H', 'B', 'tw', 'tf'
        func = i_properties
    elif shape == 'O':
        arg_names = 'D', 't'
        func = o_properties
    elif shape == 'C':
        arg_names = 'H', 'B', 'tw', 'tf'
        func = c_properties
    elif shape == 'R':
        arg_names = 'H', 'B', 't', 'r'
        func = r_properties
    return mandate(func, arg_names, *args, **kwargs)


def h_properties(H, B, tw, tf, r=0):
    rd = (1 - 2 / (4 - pi) / 3) * r
    rA = (1 - pi * 0.25) * r ** 2
    rI = (1 / 3. - pi / 16 - 1 / (4 - pi) / 9) * r ** 4
    A = B * tf * 2 + (H - tf * 2) * tw + rA * 4
    tIf = tf * B * B * B / 12.
    tIw = (H - tf * 2) * tw * tw * tw / 12.
    tIr = rI + rA * ((tw * 0.25 + rd) * tw + rd * rd)
    Iz = tIf * 2 + tIw + tIr * 4
    tIf = B * tf ** 3 / 12. + B * tf * (H - tf) ** 2 * 0.25
    tIw = tw * (H - tf * 2) ** 3 / 12.
    tIr = rI + rA * (H * 0.5 - tf - rd) ** 2
    Iy = tIf * 2 + tIw + tIr * 4
    return {
        'Ax': A,
        'Ay': float(tf * B * 2),
        'Az': float(tw * H),
        'Iy': Iy,
        'Iz': Iz,
        'J': (B * tf ** 3 * 2 + (H - tf * 2) * tw ** 3) / 3.,
        'Zy': Iy / H * 2,
        'Zz': Iz / B * 2,
        'iy': sqrt(Iy / A),
        'iz': sqrt(Iz / A)
    }


def t_properties(H, B, tw, tf, r=0):
    rd = (1 - 2 / (4 - pi) / 3) * r
    rA = (1 - pi * 0.25) * r ** 2
    rI = (1 / 3. - pi / 16 - 1 / (4 - pi) / 9) * r ** 4
    A = B * tf + (H - tf) * tw + rA * 2
    Sy = ((B - tw) * tf * tf + H * H * tw) * 0.5 + rA * (tf + rd) * 2
    Cy = Sy / A
    tIf = tf * B * B * B / 12.
    tIw = (H - tf) * tw * tw * tw / 12.
    tIr = rI + rA * (tw * 0.5 + rd) ** 2
    Iz = tIf + tIw + tIr * 2
    tIf = B * tf * tf * tf / 12. + B * tf * (Cy - tf * 0.5) ** 2
    tIw = tw * (H - tf) ** 3 / 12. + tw * (H - tf) * ((H + tf) * 0.5 - Cy) ** 2
    tIr = rI + rA * (Cy - tf - rd) ** 2
    Iy = tIf + tIw + tIr * 2
    return {
        'Ax': A,
        'Ay': float(tf * B),
        'Az': float(tw * H),
        'Iy': Iy,
        'Iz': Iz,
        'Zy': Iy / max(Cy, H - Cy),
        'Zz': Iz / B * 2,
        'iy': sqrt(Iy / A),
        'iz': sqrt(Iz / A),
        'Cy': Cy
    }

def calculate_gradient(color1: int, color2: int, steps: int) -> list:
    if color1 > 0xFFFFFF or color2 > 0xFFFFFF:
        raise ValueError("Color value is too large")
    if color1 < 0 or color2 < 0:
        raise ValueError("Color value is too small")

    def percent_gradient(percent: float) -> int:
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        r = lin_interpolate(r1, r2, percent)
        g = lin_interpolate(g1, g2, percent)
        b = lin_interpolate(b1, b2, percent)
        return rgb_to_hex(r, g, b)

    return [percent_gradient(i / steps) for i in range(steps)]


def calculate_gradient_str(color1: str, color2: str, steps: int) -> list[str]:
    gradient = calculate_gradient(int(color1, 16), int(color2, 16), steps)
    return [int_to_hex_str(color) for color in gradient]


def int_to_hex_str(color: int) -> str:
    return f"#{color:06X}"


def hex_to_rgb(hex_color: int) -> tuple:
    if hex_color > 0xFFFFFF or hex_color < 0:
        raise ValueError("Color value is too large or too small")
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return r, g, b


def rgb_to_hex(r: int, g: int, b: int) -> int:
    if r > 0xFF or g > 0xFF or b > 0xFF:
        raise ValueError("Color value is too large")
    if r < 0 or g < 0 or b < 0:
        raise ValueError("Color value is too small")
    return (r << 16) + (g << 8) + b


def lin_interpolate(f1: int, f2: int, percent: float) -> int:
    res = f1 + percent * (f2 - f1)
    return round(res)


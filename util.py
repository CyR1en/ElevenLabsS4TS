import numpy as np


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


def ease_out_cubic(x: float) -> float:
    return 1 - pow(1 - x, 3)


def reverse_ease_out_cubic(x: float) -> float:
    return 1 + pow(1 - x, 3)


def map_range(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    in_span = in_max - in_min
    out_span = out_max - out_min
    scaled = (x - in_min) / in_span
    return out_min + (scaled * out_span)


def flatten_wave_to_zero(y, n, w):
    y_mean = sum(y) / len(y)
    y_centered = [yi - y_mean for yi in y]
    y_smoothed = []
    for i in range(len(y)):
        start = max(0, i - w)
        end = min(len(y), i + w + 1)
        window = y_centered[start:end]
        y_smoothed.append(sum(window) / len(window))
    for i in range(n - w):
        y_smoothed = flatten_wave_to_zero(y_smoothed, 1, w)
    y_flattened = [yi + y_mean for yi in y_smoothed]
    return y_flattened


def pretty_wave(x):
    x = x / 200
    return (np.sin(8.8 * np.pi * x) + np.sin(11.0 * np.pi * x) + np.sin(13.2 * np.pi * x)) * 10 ** 3.1

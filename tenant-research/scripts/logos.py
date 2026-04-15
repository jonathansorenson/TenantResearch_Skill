#!/usr/bin/env python3
"""
Vector logo generation for tenant research PDF reports.
Uses reportlab Drawing objects for crisp, resolution-independent rendering.

Usage:
    from logos import build_rising_tide_logo, build_comerica_logo, build_tenant_logo

All functions return Drawing objects that can be appended directly to a platypus story.
"""

from reportlab.graphics.shapes import Drawing, String, Line, Group, Polygon, Rect, Circle
from reportlab.graphics.shapes import PolyLine
from reportlab.lib.colors import HexColor, white, Color
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
import math


# ===== Brand Colors =====
NAVY = HexColor('#1B2A4A')       # Rising Tide primary
RT_GOLD = HexColor('#D4A574')    # Rising Tide wave 1
RT_SAGE = HexColor('#6B8F7B')    # Rising Tide wave 2
RT_TEAL = HexColor('#4A5D5E')    # Rising Tide wave 3
RT_SLATE = HexColor('#4A5568')   # Rising Tide secondary text

COMERICA_BLUE = HexColor('#002F6C')  # Comerica official brand blue

# Known brand colors for common CRE tenants
BRAND_COLORS = {
    'comerica': HexColor('#002F6C'),
    'starbucks': HexColor('#00704A'),
    'chase': HexColor('#06589E'),
    'jpmorgan': HexColor('#06589E'),
    'wells fargo': HexColor('#D01924'),
    'bank of america': HexColor('#002663'),
    'fifth third': HexColor('#003A70'),
    'regions': HexColor('#008000'),
    'walgreens': HexColor('#E2001A'),
    'cvs': HexColor('#CC0000'),
    'wework': HexColor('#000000'),
    'dunkin': HexColor('#DD4431'),
    'dutch bros': HexColor('#002F6C'),
    'td bank': HexColor('#2D8C2E'),
    'pnc': HexColor('#F58025'),
    'truist': HexColor('#3B1564'),
    'citizens': HexColor('#007236'),
    'key bank': HexColor('#D71921'),
    'm&t bank': HexColor('#3D2B7B'),
    'us bank': HexColor('#002855'),
    'u.s. bank': HexColor('#002855'),
    'dollar general': HexColor('#FFC726'),
    'dollar tree': HexColor('#34A853'),
    'publix': HexColor('#3A7D32'),
}


def get_brand_color(company_name):
    """Look up brand color for known companies. Returns HexColor or None."""
    name_lower = company_name.lower()
    for key, color in BRAND_COLORS.items():
        if key in name_lower:
            return color
    return None


def _wave_points(x_start, x_end, y_center, amplitude, frequency, phase, n_points=60):
    """Generate smooth sine wave points for logo curves."""
    points = []
    for i in range(n_points):
        x = x_start + (x_end - x_start) * i / (n_points - 1)
        y = y_center + amplitude * math.sin(frequency * (x - x_start) + phase)
        points.extend([x, y])
    return points


def build_rising_tide_logo(width=300, height=70):
    """
    Build the Rising Tide Property Group logo as a vector Drawing.
    Features the 3-wave design + company name, all centered.

    Returns:
        Drawing object (reportlab Flowable)
    """
    d = Drawing(width, height)

    # Wave icon on the left
    wave_x_start = 10
    wave_x_end = 65
    wave_configs = [
        {'color': RT_TEAL, 'y_center': 52, 'amplitude': 5, 'phase': 0, 'width': 2.5},
        {'color': RT_SAGE, 'y_center': 42, 'amplitude': 5, 'phase': 0.3, 'width': 2.5},
        {'color': RT_GOLD, 'y_center': 32, 'amplitude': 5, 'phase': 0.6, 'width': 2.5},
    ]

    for cfg in wave_configs:
        pts = _wave_points(wave_x_start, wave_x_end, cfg['y_center'],
                           cfg['amplitude'], 0.12, cfg['phase'])
        line = PolyLine(pts, strokeColor=cfg['color'], strokeWidth=cfg['width'],
                        strokeLineCap=1)  # round cap
        d.add(line)

    # "RISING TIDE" text
    text_x = 78
    d.add(String(text_x, 42, 'RISING TIDE',
                 fontSize=22, fontName='Helvetica-Bold', fillColor=NAVY))
    d.add(String(text_x + 1, 26, 'PROPERTY GROUP',
                 fontSize=9, fontName='Helvetica', fillColor=RT_SLATE))

    return d


def build_comerica_logo(width=300, height=60):
    """
    Build the Comerica logo as a vector Drawing.
    Current Comerica logo (2022+): Three flowing ribbons above "Comerica" wordmark,
    all in navy blue (#002F6C).

    Returns:
        Drawing object (reportlab Flowable)
    """
    d = Drawing(width, height)
    color = COMERICA_BLUE

    # Three ribbons / flowing lines above the wordmark
    # These represent Commercial Bank, Retail Bank, and Wealth Management
    ribbon_configs = [
        {'y_center': 50, 'amplitude': 3.5, 'phase': 0, 'width': 2.8},
        {'y_center': 44, 'amplitude': 3.0, 'phase': 0.5, 'width': 2.2},
        {'y_center': 38, 'amplitude': 2.5, 'phase': 1.0, 'width': 1.8},
    ]

    # Center the ribbons over the wordmark
    text_width = stringWidth('Comerica', 'Helvetica-Bold', 28)
    text_x = (width - text_width) / 2
    ribbon_x_start = text_x + 5
    ribbon_x_end = text_x + text_width - 5

    for cfg in ribbon_configs:
        pts = _wave_points(ribbon_x_start, ribbon_x_end, cfg['y_center'],
                           cfg['amplitude'], 0.04, cfg['phase'], n_points=50)
        line = PolyLine(pts, strokeColor=color, strokeWidth=cfg['width'],
                        strokeLineCap=1)
        d.add(line)

    # "Comerica" wordmark — centered
    d.add(String(width / 2, 8, 'Comerica',
                 fontSize=28, fontName='Helvetica-Bold', fillColor=color,
                 textAnchor='middle'))

    return d


def build_tenant_logo(company_name, brand_color=None, width=300, height=50):
    """
    Build a generic tenant logo as a vector Drawing.
    Used as a fallback when the tenant is not a known brand with a specific logo builder.

    Creates the company name in large bold text with the brand color, plus a subtle
    underline accent.

    Args:
        company_name: The company name
        brand_color: HexColor for the brand. If None, uses professional dark blue.
        width: Drawing width
        height: Drawing height

    Returns:
        Drawing object (reportlab Flowable)
    """
    if brand_color is None:
        brand_color = HexColor('#002855')

    d = Drawing(width, height)

    # Auto-size font
    font_size = 28
    while stringWidth(company_name, 'Helvetica-Bold', font_size) > width - 20 and font_size > 14:
        font_size -= 2

    # Company name — centered
    d.add(String(width / 2, height / 2 - 4, company_name,
                 fontSize=font_size, fontName='Helvetica-Bold', fillColor=brand_color,
                 textAnchor='middle'))

    # Subtle accent line under the name
    text_w = stringWidth(company_name, 'Helvetica-Bold', font_size)
    line_x = (width - text_w) / 2
    d.add(Line(line_x, height / 2 - 12, line_x + text_w, height / 2 - 12,
               strokeColor=brand_color, strokeWidth=1.5))

    return d


# ===== Convenience: build cover logos for any tenant =====

def build_cover_logos(company_name):
    """
    Build both logos for the cover page.

    Returns:
        (rising_tide_drawing, tenant_drawing) — both are Drawing flowables
    """
    rt = build_rising_tide_logo()

    # Check for specific logo builders
    name_lower = company_name.lower()
    if 'comerica' in name_lower:
        tenant = build_comerica_logo()
    else:
        brand_color = get_brand_color(company_name)
        tenant = build_tenant_logo(company_name, brand_color=brand_color)

    return rt, tenant


if __name__ == '__main__':
    # Test
    rt = build_rising_tide_logo()
    print(f'Rising Tide logo: {rt.width}x{rt.height}')
    cl = build_comerica_logo()
    print(f'Comerica logo: {cl.width}x{cl.height}')
    tl = build_tenant_logo('Test Company')
    print(f'Generic tenant logo: {tl.width}x{tl.height}')

#!/usr/bin/env python3
"""
Reusable chart-building functions for tenant research PDF reports.
Uses reportlab.graphics to create actual visual charts (not just tables).
Import and call these from the main PDF generation script.

Usage:
    from charts import (
        build_score_dashboard,
        build_bar_chart,
        build_trend_chart,
        build_competitive_bars,
        build_risk_heatmap
    )
"""

from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Group
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth

# Rising Tide color palette
NAVY = HexColor('#1B2A4A')
SLATE = HexColor('#4A5568')
ACCENT = HexColor('#2E86AB')
GREEN = HexColor('#2D7D46')
TEAL = HexColor('#2E86AB')
AMBER = HexColor('#D4A017')
ORANGE = HexColor('#D46A17')
RED = HexColor('#C0392B')
LIGHT_GRAY = HexColor('#F0F0F0')
WHITE = HexColor('#FFFFFF')
DARK_TEXT = HexColor('#2D3748')


def grade_color(score):
    """Return color for a given score (0-100).
    Scale: A=90-100, B=80-89, C=70-79, D=60-69, F=0-59"""
    if score >= 90:
        return GREEN
    elif score >= 80:
        return TEAL
    elif score >= 70:
        return AMBER
    elif score >= 60:
        return ORANGE
    else:
        return RED


def letter_grade(score):
    """Return letter grade for a given score.
    Scale: A=90-100, B=80-89, C=70-79, D=60-69, F=0-59"""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def _truncate_label(text, max_width, font_name='Helvetica', font_size=9):
    """Truncate text to fit within max_width pixels, adding ellipsis if needed."""
    if stringWidth(text, font_name, font_size) <= max_width:
        return text
    while len(text) > 3 and stringWidth(text + '...', font_name, font_size) > max_width:
        text = text[:-1]
    return text + '...'


def _wrap_label(text, max_width, font_name='Helvetica', font_size=9):
    """Wrap text into multiple lines to fit within max_width pixels.
    Returns list of lines."""
    if stringWidth(text, font_name, font_size) <= max_width:
        return [text]
    words = text.split()
    lines = []
    current_line = ''
    for word in words:
        test = (current_line + ' ' + word).strip()
        if stringWidth(test, font_name, font_size) <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else [text]


def build_score_dashboard(composite_score, dimensions, width=480, height=None):
    """
    Build the main score dashboard for the executive summary page.

    Args:
        composite_score: int, 0-100
        dimensions: list of dicts with keys 'name', 'score' (0-100)
        width: drawing width
        height: drawing height (auto-calculated if None)

    Returns:
        Drawing object (a reportlab Flowable)
    """
    bar_height = 22
    gap = 8
    n = len(dimensions)
    # Auto-size height to fit all dimensions with padding
    if height is None:
        height = max(200, (n * (bar_height + gap)) + 60)

    d = Drawing(width, height)

    # --- Left side: Big composite score box ---
    box_size = 120
    cx = 70
    cy = height / 2
    score_color = grade_color(composite_score)

    d.add(Rect(cx - box_size/2, cy - box_size/2, box_size, box_size,
               fillColor=score_color, strokeColor=None, rx=12, ry=12))

    # Score number (large)
    d.add(String(cx, cy + 15, str(composite_score),
                 fontSize=40, fontName='Helvetica-Bold', fillColor=WHITE, textAnchor='middle'))

    # "out of 100"
    d.add(String(cx, cy - 8, '/100',
                 fontSize=13, fontName='Helvetica', fillColor=WHITE, textAnchor='middle'))

    # Letter grade
    grade = letter_grade(composite_score)
    d.add(String(cx, cy - 30, f'Grade: {grade}',
                 fontSize=14, fontName='Helvetica-Bold', fillColor=WHITE, textAnchor='middle'))

    # --- Right side: Horizontal bars for each dimension ---
    label_area_width = 140  # generous space for dimension names
    chart_left = cx + box_size/2 + 20 + label_area_width
    chart_right_margin = 60  # space for score labels
    chart_width = width - chart_left - chart_right_margin
    chart_top = height - 30

    for i, dim in enumerate(dimensions):
        y = chart_top - (i * (bar_height + gap)) - bar_height
        score = dim['score']
        name = dim['name']
        color = grade_color(score)

        # Wrap long labels into multiple lines
        label_x = chart_left - 8
        lines = _wrap_label(name, label_area_width, 'Helvetica', 9)
        if len(lines) == 1:
            d.add(String(label_x, y + bar_height/2 - 3, lines[0],
                         fontSize=9, fontName='Helvetica', fillColor=DARK_TEXT,
                         textAnchor='end'))
        else:
            # Stack lines vertically, centered on bar
            line_height = 10
            total_text_height = len(lines) * line_height
            start_y = y + bar_height/2 + total_text_height/2 - line_height + 2
            for j, line in enumerate(lines):
                d.add(String(label_x, start_y - j * line_height, line,
                             fontSize=8, fontName='Helvetica', fillColor=DARK_TEXT,
                             textAnchor='end'))

        # Background bar (gray)
        d.add(Rect(chart_left, y, chart_width, bar_height,
                   fillColor=LIGHT_GRAY, strokeColor=None, rx=4, ry=4))

        # Score bar
        bar_w = max(2, (score / 100.0) * chart_width)
        d.add(Rect(chart_left, y, bar_w, bar_height,
                   fillColor=color, strokeColor=None, rx=4, ry=4))

        # Score label — always to the right of the bar
        d.add(String(chart_left + chart_width + 5, y + bar_height/2 - 4,
                     f'{score} ({letter_grade(score)})',
                     fontSize=9, fontName='Helvetica-Bold', fillColor=DARK_TEXT,
                     textAnchor='start'))

    return d


def build_bar_chart(data, labels, title='', width=420, height=220,
                    bar_color=ACCENT, y_label='', show_values=True):
    """
    Build a vertical bar chart (e.g., for revenue by year).

    Args:
        data: list of numbers
        labels: list of strings (x-axis labels, same length as data)
        title: chart title
        width, height: drawing dimensions
        bar_color: color for bars (or list of colors)
        y_label: Y-axis label
        show_values: whether to show value labels on bars

    Returns:
        Drawing object
    """
    d = Drawing(width, height)

    # Title
    title_offset = 0
    if title:
        d.add(String(width / 2, height - 12, title,
                     fontSize=11, fontName='Helvetica-Bold', fillColor=NAVY,
                     textAnchor='middle'))
        title_offset = 20

    left_margin = 65 if y_label else 50
    chart = VerticalBarChart()
    chart.x = left_margin
    chart.y = 35
    chart.width = width - left_margin - 30
    chart.height = height - 35 - title_offset - 20
    chart.data = [data]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.angle = 0
    # Prevent label overlap for many bars
    if len(labels) > 6:
        chart.categoryAxis.labels.angle = 30
        chart.categoryAxis.labels.dy = -10
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.valueAxis.valueMin = 0

    if isinstance(bar_color, list):
        for i, color in enumerate(bar_color):
            chart.bars[0].fillColor = color
    else:
        chart.bars[0].fillColor = bar_color

    chart.bars[0].strokeColor = None
    chart.barWidth = min(40, (chart.width / max(len(data), 1)) * 0.6)

    # Value labels on top of bars
    if show_values:
        chart.barLabelFormat = '%.1f'
        chart.barLabels.nudge = 8
        chart.barLabels.fontSize = 7
        chart.barLabels.fontName = 'Helvetica'
        chart.barLabels.fillColor = DARK_TEXT

    d.add(chart)

    # Y-axis label
    if y_label:
        d.add(String(12, (height - title_offset) / 2 + 10, y_label,
                     fontSize=8, fontName='Helvetica', fillColor=SLATE,
                     textAnchor='middle', angle=90))

    return d


def build_trend_chart(data_series, labels, title='', width=420, height=200,
                      line_colors=None, series_names=None, y_label=''):
    """
    Build a line chart for trends over time.

    Args:
        data_series: list of lists (each inner list is one line)
        labels: list of x-axis labels
        title: chart title
        width, height: drawing dimensions
        line_colors: list of colors for each series
        series_names: legend names for each series
        y_label: Y-axis label

    Returns:
        Drawing object
    """
    d = Drawing(width, height)

    if title:
        d.add(String(width / 2, height - 12, title,
                     fontSize=11, fontName='Helvetica-Bold', fillColor=NAVY,
                     textAnchor='middle'))

    chart = HorizontalLineChart()
    chart.x = 60
    chart.y = 35
    chart.width = width - 90
    chart.height = height - 65
    chart.data = data_series
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0

    if line_colors is None:
        line_colors = [ACCENT, GREEN, AMBER, RED, NAVY]

    for i, color in enumerate(line_colors[:len(data_series)]):
        chart.lines[i].strokeColor = color
        chart.lines[i].strokeWidth = 2.5
        chart.lines[i].symbol = None

    d.add(chart)

    # Legend
    if series_names:
        legend_y = 8
        legend_x = 60
        for i, name in enumerate(series_names):
            color = line_colors[i] if i < len(line_colors) else SLATE
            d.add(Rect(legend_x, legend_y, 10, 10, fillColor=color, strokeColor=None))
            d.add(String(legend_x + 14, legend_y + 1, name,
                         fontSize=7, fontName='Helvetica', fillColor=SLATE))
            legend_x += stringWidth(name, 'Helvetica', 7) + 25

    return d


def build_competitive_bars(companies, metric_values, metric_name='Market Share',
                           highlight_company=None, width=420, height=None):
    """
    Build horizontal bar chart comparing companies on a metric.
    Handles long company names with wrapping and proper spacing.

    Args:
        companies: list of company names
        metric_values: list of numeric values
        metric_name: label for the metric
        highlight_company: name of company to highlight in accent color
        width: drawing width
        height: auto-calculated if None

    Returns:
        Drawing object
    """
    n = len(companies)
    bar_h = 22
    bar_gap = 10
    if height is None:
        height = max(160, n * (bar_h + bar_gap) + 60)

    d = Drawing(width, height)

    # Title
    d.add(String(width / 2, height - 12, f'Competitive Landscape: {metric_name}',
                 fontSize=11, fontName='Helvetica-Bold', fillColor=NAVY,
                 textAnchor='middle'))

    # Calculate label width needed
    label_width = 130
    chart_left = label_width + 10
    chart_width = width - chart_left - 60
    max_val = max(metric_values) if metric_values else 1
    start_y = height - 45

    for i, (company, value) in enumerate(zip(companies, metric_values)):
        y = start_y - i * (bar_h + bar_gap)
        is_highlight = (highlight_company and company == highlight_company)
        bar_color = ACCENT if is_highlight else SLATE

        # Company label — wrap if needed
        lines = _wrap_label(company, label_width, 'Helvetica', 9)
        if len(lines) == 1:
            d.add(String(chart_left - 8, y + bar_h/2 - 3, lines[0],
                         fontSize=9, fontName='Helvetica-Bold' if is_highlight else 'Helvetica',
                         fillColor=DARK_TEXT, textAnchor='end'))
        else:
            line_h = 10
            total_h = len(lines) * line_h
            sy = y + bar_h/2 + total_h/2 - line_h + 2
            for j, line in enumerate(lines):
                d.add(String(chart_left - 8, sy - j * line_h, line,
                             fontSize=8,
                             fontName='Helvetica-Bold' if is_highlight else 'Helvetica',
                             fillColor=DARK_TEXT, textAnchor='end'))

        # Background bar
        d.add(Rect(chart_left, y, chart_width, bar_h,
                   fillColor=LIGHT_GRAY, strokeColor=None, rx=4, ry=4))

        # Value bar
        bar_w = max(2, (value / max_val) * chart_width)
        d.add(Rect(chart_left, y, bar_w, bar_h,
                   fillColor=bar_color, strokeColor=None, rx=4, ry=4))

        # Value label to the right
        d.add(String(chart_left + chart_width + 5, y + bar_h/2 - 4,
                     str(value),
                     fontSize=9, fontName='Helvetica-Bold', fillColor=DARK_TEXT,
                     textAnchor='start'))

    return d


def build_risk_heatmap(dimensions, width=420, height=None):
    """
    Build a color-coded risk summary (colored rectangles with labels).
    Text wraps within cells to prevent overflow.

    Args:
        dimensions: list of dicts with 'name' and 'score' (0-100)
        width: drawing width
        height: auto-calculated if None

    Returns:
        Drawing object
    """
    cols = min(3, len(dimensions))
    rows = (len(dimensions) + cols - 1) // cols
    cell_h = 62
    cell_pad = 10
    title_space = 35
    if height is None:
        height = rows * (cell_h + cell_pad) + title_space + cell_pad

    d = Drawing(width, height)

    d.add(String(width / 2, height - 14, 'Risk Assessment Summary',
                 fontSize=11, fontName='Helvetica-Bold', fillColor=NAVY,
                 textAnchor='middle'))

    cell_w = (width - 20 - (cols - 1) * cell_pad) / cols
    # start_y is the BOTTOM edge of the first row of boxes.
    # Top edge = start_y + cell_h, which must be <= height - title_space
    # so boxes never overlap the title or exceed the Drawing boundary.
    start_y = height - title_space - cell_h

    for i, dim in enumerate(dimensions):
        col = i % cols
        row = i // cols
        x = 10 + col * (cell_w + cell_pad)
        y = start_y - row * (cell_h + cell_pad)

        color = grade_color(dim['score'])
        grade = letter_grade(dim['score'])

        # Colored cell
        d.add(Rect(x, y, cell_w, cell_h,
                   fillColor=color, strokeColor=None, rx=6, ry=6))

        # Dimension name — wrap within cell, vertically centered above score
        name = dim['name']
        max_text_w = cell_w - 14
        lines = _wrap_label(name, max_text_w, 'Helvetica-Bold', 9)

        if len(lines) == 1:
            d.add(String(x + cell_w/2, y + cell_h - 22, lines[0],
                         fontSize=9, fontName='Helvetica-Bold', fillColor=WHITE,
                         textAnchor='middle'))
        else:
            line_h = 11
            top_y = y + cell_h - 16
            for j, line in enumerate(lines):
                d.add(String(x + cell_w/2, top_y - j * line_h, line,
                             fontSize=8, fontName='Helvetica-Bold', fillColor=WHITE,
                             textAnchor='middle'))

        # Score — positioned at bottom of cell with breathing room
        d.add(String(x + cell_w/2, y + 12,
                     f'{dim["score"]}/100 ({grade})',
                     fontSize=11, fontName='Helvetica-Bold', fillColor=WHITE,
                     textAnchor='middle'))

    return d


# Convenience: safe bullet character for reportlab
BULLET = u'\u2022'  # Use this instead of raw bullet chars that cause encoding issues

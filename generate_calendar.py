#!/usr/bin/env python3
from __future__ import annotations
import sys
import argparse
from datetime import datetime, timedelta
import calendar
from typing import Optional

import tomllib  # using built-in tomllib (Python 3.11+)

def parse_cron_expression(cron_expr: str) -> dict[str, any]:
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression, must have 5 fields")

    minute_str, hour_str, day_str, month_str, weekday_str = parts
    minute = int(minute_str)
    hour = int(hour_str)

    def cron_to_python_wd(cw: int) -> int:
        return (cw - 1) % 7

    if weekday_str == "*":
        valid_weekdays = set(range(7))
    else:
        valid_weekdays = set()
        for part in weekday_str.split(','):
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start), int(end)
                for d in range(start, end+1):
                    valid_weekdays.add(cron_to_python_wd(d))
            else:
                valid_weekdays.add(cron_to_python_wd(int(part)))

    return {
        "minute": minute,
        "hour": hour,
        "valid_weekdays": valid_weekdays
    }

def load_exemptions(toml_path: str) -> dict[str, list[tuple[datetime.date, datetime.date]]]:
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    uptimes = []
    downtimes = []
    if "exemptions" in data:
        if "uptimes" in data["exemptions"]:
            for item in data["exemptions"]["uptimes"]:
                start = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
                end = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
                uptimes.append((start, end))
        if "downtimes" in data["exemptions"]:
            for item in data["exemptions"]["downtimes"]:
                start = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
                end = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
                downtimes.append((start, end))

    return {
        "uptimes": uptimes,
        "downtimes": downtimes
    }

def is_in_range(day: datetime, ranges: list[tuple[datetime.date, datetime.date]]) -> bool:
    d = day.date()
    for start, end in ranges:
        if start <= d <= end:
            return True
    return False

def calculate_uptime_for_day(cron_up: str, cron_down: str, day: datetime,
                             exemptions: Optional[dict[str, list[tuple[datetime.date, datetime.date]]]] = None
                            ) -> tuple[str, str] | None:
    # If exemptions are provided, check them
    if exemptions:
        # Downtimes take precedence
        if is_in_range(day, exemptions["downtimes"]):
            # Entire day is downtime
            return None
        elif is_in_range(day, exemptions["uptimes"]):
            # Entire day is uptime (override cron)
            return ("00:00", "23:59")

    # If no exemption applies, fall back to cron
    up = parse_cron_expression(cron_up)
    down = parse_cron_expression(cron_down)
    weekday = day.weekday()
    if weekday in up["valid_weekdays"] and weekday in down["valid_weekdays"]:
        start_time = f"{up['hour']:02d}:{up['minute']:02d}"
        end_time = f"{down['hour']:02d}:{down['minute']:02d}"
        return (start_time, end_time)
    else:
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate an SVG calendar for planned uptime.")
    parser.add_argument("cron_up", type=str, help="Cron expression for scaling up.")
    parser.add_argument("cron_down", type=str, help="Cron expression for scaling down.")
    parser.add_argument("output_path", type=str, help="Output SVG file path.")
    parser.add_argument("--days", type=int, default=14, help="Number of days to display from today.")
    parser.add_argument("--exemptions_toml", type=str, help="Path to exemptions TOML file.", default=None)
    args = parser.parse_args()

    exemptions = None
    if args.exemptions_toml:
        exemptions = load_exemptions(args.exemptions_toml)

    start_day = datetime.now()
    days = [start_day + timedelta(days=i) for i in range(args.days)]
    day_width = 120
    day_height = 80
    margin = 20
    svg_width = day_width * len(days) + margin * 2
    svg_height = day_height * 2 + margin * 2

    top_row_color = "#237f7e"     
    bottom_row_color = "#2b9b9a"  

    svg = [
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="white"/>'
    ]

    for i, day in enumerate(days):
        x = margin + i * day_width
        day_str = f"{day.day}.{day.month}"
        weekday_abbr = calendar.day_abbr[day.weekday()]

        # Top row: date and weekday
        svg.append(f'<rect x="{x}" y="{margin}" width="{day_width}" height="{day_height}" fill="{top_row_color}"/>')
        svg.append(
            f'<text x="{x+day_width/2}" y="{margin+30}" font-weight="bold" font-family="sans-serif" font-size="20" text-anchor="middle" fill="white">{day_str}</text>'
        )
        svg.append(
            f'<text x="{x+day_width/2}" y="{margin+50}" font-family="sans-serif" font-size="16" text-anchor="middle" fill="white">{weekday_abbr}</text>'
        )

        # Bottom row: uptime or no uptime
        uptime = calculate_uptime_for_day(args.cron_up, args.cron_down, day, exemptions)
        svg.append(f'<rect x="{x}" y="{margin+day_height}" width="{day_width}" height="{day_height}" fill="{bottom_row_color}"/>')
        if uptime:
            svg.append(
                f'<text x="{x+day_width/2}" y="{margin+day_height+20}" font-family="sans-serif" font-size="16" text-anchor="middle" fill="white">{uptime[0]}</text>'
            )
            svg.append(
                f'<text x="{x+day_width/2}" y="{margin+day_height+40}" font-family="sans-serif" font-size="16" text-anchor="middle" fill="white">-</text>'
            )
            svg.append(
                f'<text x="{x+day_width/2}" y="{margin+day_height+60}" font-family="sans-serif" font-size="16" text-anchor="middle" fill="white">{uptime[1]}</text>'
            )
        else:
            svg.append(
                f'<text x="{x+day_width/2}" y="{margin+day_height+40}" font-family="sans-serif" font-size="16" text-anchor="middle" fill="white">No uptime</text>'
            )

    svg.append('</svg>')

    with open(args.output_path, "w") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    main()

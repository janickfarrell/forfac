# forexfactory_scraper.py
# pip install requests beautifulsoup4

import csv
import re
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

FIELDS = ["date", "time", "currency", "impact", "event", "actual", "forecast", "previous"]

# منطقه زمانی خروجی: GMT — با کوکی fftimezone کنترل می‌شود
COOKIES = {
    "fftimezone": "Etc/GMT",
    "fftimeformat": "1",  # فرمت ۲۴ ساعته
}

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]

# رنگ آیکون → شدت اثر
IMPACT_COLOR_MAP = {
    "red": "High",
    "ora": "Medium",
    "yel": "Low",
    "gry": "Holiday",
}

# کلاس سطح → شدت اثر
IMPACT_LEVEL_MAP = {
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "none": "Holiday",
}


def get_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)
    resp.raise_for_status()
    return resp.text


def clean(text: str) -> str:
    return " ".join(text.split()) if text else ""


def parse_impact(tr) -> str:
    cell = tr.select_one("td.calendar__impact")
    if not cell:
        return ""

    # ۱) اگر title وجود داشت همان را استفاده کن
    icon = cell.select_one("[title]")
    if icon and icon.get("title"):
        return icon["title"].replace("Impact Expected", "").strip()

    # ۲) در غیر این صورت از روی کلاس‌های سلول و فرزندانش تشخیص بده
    classes = set(cell.get("class", []))
    for el in cell.select("[class]"):
        classes.update(el.get("class", []))
    class_str = " ".join(classes).lower()

    for key, name in IMPACT_COLOR_MAP.items():
        if f"impact-{key}" in class_str:   # icon--ff-impact-red / -ora / -yel / -gry
            return name
    for key, name in IMPACT_LEVEL_MAP.items():
        if f"--{key}" in class_str:        # calendar__impact--high / --medium / ...
            return name
    return ""


def parse_calendar(html: str, year: int) -> list:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.calendar__table")
    if not table:
        raise RuntimeError(
            "Calendar table not found; request may be blocked or page structure changed."
        )

    events = []
    current_date = ""
    current_time = ""
    current_year = year
    prev_month_idx = None

    for tr in table.select("tr.calendar__row"):
        event_cell = tr.select_one("td.calendar__event")
        if not event_cell:
            continue  # skip separator rows

        # date/time appear only on the first row of each group; keep last seen value
        date_cell = tr.select_one("td.calendar__date")
        if date_cell:
            d = clean(date_cell.get_text(" "))
            if d:
                # اگر در نمای هفتگی از دسامبر به ژانویه عبور کردیم، سال را یکی زیاد کن
                m = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", d, re.IGNORECASE)
                if m:
                    idx = MONTHS.index(m.group(1).lower()) + 1
                    if prev_month_idx is not None and idx < prev_month_idx:
                        current_year += 1
                    prev_month_idx = idx
                # الصاق سال به تاریخ: «Thu Jan 2 2025»
                current_date = f"{d} {current_year}"

        time_cell = tr.select_one("td.calendar__time")
        if time_cell:
            t = clean(time_cell.get_text())
            if t:
                current_time = t

        def cell(selector):
            el = tr.select_one(selector)
            return clean(el.get_text()) if el else ""

        events.append({
            "date": current_date,
            "time": current_time,
            "currency": cell("td.calendar__currency"),
            "impact": parse_impact(tr),
            "event": clean(event_cell.get_text()),
            "actual": cell("td.calendar__actual"),
            "forecast": cell("td.calendar__forecast"),
            "previous": cell("td.calendar__previous"),
        })

    return events


def save_csv(events, path):
    # utf-8-sig so Excel opens it correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(events)


def month_url(year: int, month_abbr: str) -> str:
    return "https://www.forexfactory.com/calendar?month=" + month_abbr + "." + str(year)


def year_from_url(url: str) -> int:
    # سال را از خود URL برمی‌داریم (month=jan.2025 یا week=dec29.2025)
    m = re.search(r"(\d{4})", url)
    return int(m.group(1)) if m else date.today().year


if __name__ == "__main__":
    args = sys.argv[1:]

    # اگر عدد وارد شود (مثل 2025) به‌عنوان «سال» در نظر گرفته می‌شود و هر ۱۲ ماهش دانلود می‌شود
    urls = []
    for a in args:
        if a.isdigit():
            urls += [month_url(int(a), m) for m in MONTHS]
        else:
            urls.append(a)

    if not urls:  # پیش‌فرض: سال جاری
        year = date.today().year
        urls = [month_url(year, m) for m in MONTHS]

    all_events = []
    for url in urls:
        print("Fetching: " + url)
        all_events.extend(parse_calendar(get_html(url), year_from_url(url)))
        time.sleep(2)  # avoid getting IP-banned

    output = "forexfactory_calendar.csv"
    save_csv(all_events, output)
    print("Done! " + str(len(all_events)) + " events saved to " + output)

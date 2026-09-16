# ForexFactory Calendar Scraper

A small Python scraper that downloads the [Forex Factory](https://www.forexfactory.com/calendar) economic calendar and saves it as a CSV file — **automatically updated every day at 00:10 UTC via GitHub Actions**.

## Features

- Scrapes all 12 months of a given year, or any specific month/week URL
- Extracts: `date`, `time` (GMT), `currency`, `impact`, `event`, `actual`, `forecast`, `previous`
- Detects event impact (High / Medium / Low / Holiday) from icon colors or CSS classes
- Handles the year rollover (Dec → Jan) in weekly views
- Exports `forexfactory_calendar.csv` with `utf-8-sig` encoding so Excel opens it correctly
- Polite crawling: 2-second delay between requests to avoid IP bans

## Output

`forexfactory_calendar.csv` (tracked in this repo, refreshed daily):

| date          | time  | currency | impact | event | actual | forecast | previous |
| ------------- | ----- | -------- | ------ | ----- | ------ | -------- | -------- |
| Thu Jan 2 2026 | 13:30 | USD     | High   | ...   | ...    | ...      | ...      |

All times are **GMT** (controlled by the `fftimezone` cookie, 24-hour format).

## Usage (local)

```bash
pip install -r requirements.txt

# Default: all 12 months of the current year
python forexfactory_scraper.py

# A specific year
python forexfactory_scraper.py 2025

# Specific month/week URLs
python forexfactory_scraper.py "https://www.forexfactory.com/calendar?month=jan.2025"
```

## GitHub Actions automation

The workflow in `.github/workflows/daily-update.yml`:

1. Runs **every day at 00:10 UTC** (`cron: "10 0 * * *"`), or manually via *Actions → Daily calendar update → Run workflow*.
2. Installs Python + dependencies.
3. Runs the scraper for the current year.
4. Commits and pushes `forexfactory_calendar.csv` only if the data changed.

Notes:

- Scheduled runs can be delayed a few minutes by GitHub under heavy load — this is normal.
- GitHub pauses scheduled workflows after 60 days of repo inactivity; the daily auto-commit counts as activity, so the schedule stays alive.
- The scheduled trigger only runs from the **default branch**.

## راهنمای فارسی

این پروژه تقویم اقتصادی Forex Factory را اسکرپ می‌کند و در فایل `forexfactory_calendar.csv` ذخیره می‌کند. ساعت‌ها به GMT و فرمت ۲۴ ساعته است و فایل خروجی با انکودینگ `utf-8-sig` ذخیره می‌شود تا در اکسل درست باز شود.

- **اجرای محلی:** `pip install -r requirements.txt` و سپس `python forexfactory_scraper.py` (یا با آرگومان سال مثل `2025`).
- **به‌روزرسانی خودکار:** GitHub Action هر روز ساعت **00:10 UTC** اجرا می‌شود، اسکرپر را اجرا می‌کند و اگر دیتا تغییر کرده باشد، فایل CSV را کامیت و پوش می‌کند. از تب Actions هم می‌توانید آن را دستی اجرا کنید.

## License

MIT — see [LICENSE](LICENSE).

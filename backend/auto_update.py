"""
Runs the movie catalog update automatically, on a repeating schedule,
using the free 'schedule' library — no Windows Task Scheduler needed.

Just start this once and leave the window open (or minimized). It will:
  1. Run an update immediately when started.
  2. Then automatically re-run it every day at the time you set below.

Usage:
    python auto_update.py

To change the time it runs daily, edit UPDATE_TIME below (24-hour format).
"""
import time
import schedule

from ingest import main as run_ingest

UPDATE_TIME = "04:00"  # change to whatever time you want, e.g. "09:30"


def job():
    print(f"\n=== Running scheduled update at {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    try:
        run_ingest()
    except SystemExit as e:
        print(f"Update stopped: {e}")
    except Exception as e:
        print(f"Update failed: {e}")
    print("=== Update finished. Waiting for next scheduled run. ===\n")


if __name__ == "__main__":
    print(f"Auto-updater started. Will run once now, then daily at {UPDATE_TIME}.")
    print("Leave this window open. Press Ctrl+C to stop.")

    job()  # run once immediately on startup

    schedule.every().day.at(UPDATE_TIME).do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)

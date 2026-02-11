import schedule
import time
import subprocess
import logging

def run_daily_job():
    print("Running daily research job...")
    try:
        subprocess.run(["python3", "scripts/daily_run.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Job failed: {e}")
    except Exception as e:
        print(f"Error running job: {e}")

# Schedule job every day at 09:00
schedule.every().day.at("09:00").do(run_daily_job)

if __name__ == "__main__":
    print("Scheduler started. Waiting for 09:00...")
    while True:
        schedule.run_pending()
        time.sleep(60)

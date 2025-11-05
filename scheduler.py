from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess, sys, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent
PY = sys.executable
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)

def job():
    log = LOGS / f"run_{datetime.datetime.now():%Y%m%d_%H%M}.log"
    with log.open("a", encoding="utf-8") as f:
        subprocess.run([PY, str(ROOT/"main.py")], stdout=f, stderr=f, check=False)

if __name__ == "__main__":
    sched = BlockingScheduler(timezone="Asia/Kolkata")
    sched.add_job(job, "cron", hour=7, minute=30)  # every day 07:30 IST
    sched.start()

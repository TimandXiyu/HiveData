from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from casher import casher


import logging
import os


if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET)
    if not os.path.exists('worker_keywords.json'):
        raise FileNotFoundError('worker hash table not found')
    logging.info('scheduler started')
    scheduler = BlockingScheduler()
    logging.info(f'scheduler initialized, data will be downloaded at 10:00')
    trigger = CronTrigger(hour='14', minute='59')
    scheduler.add_job(casher, trigger=trigger, misfire_grace_time=10)
    # scheduler.add_job(casher, 'interval', seconds=60, misfire_grace_time=10)
    logging.info('job added to scheduler')
    logging.info('job started')
    scheduler.start()





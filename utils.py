import psutil
import json
import datetime
from pathlib import Path
import json as js
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os
from glob import glob
import logging
import numpy as np


def toLowerCase(string):
    return "".join(chr(ord(c) + 32) if 65 <= ord(c) <= 90 else c for c in string)


def kill_chrome():
    for proc in psutil.process_iter():
        if "chrome" in proc.name():
            proc.kill()


def read_name_list():
    with open('worker_keywords.json') as json_file:
        name_list = json.load(json_file)
        return name_list


def save_today_record(today, prev):
    today_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    last_day = prev[list(prev.keys())[-1]]
    prev[today_time] = str(today) + f'-{today - float(last_day.split("-")[0])}'
    with open('daily_records.json', 'w') as fp:
        json.dump(prev, fp)


def write_to_json(data):
    json = Path('./data/history.json')
    cur_time = f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'
    data = float(data)

    if not json.exists():
        with open(json, 'w') as jsonfile:
            js.dump({cur_time: [data, data]}, jsonfile)
    else:
        with open(json) as jsonfile:
            prev_content = js.load(jsonfile)
            if float(prev_content[list(prev_content.keys())[-1]][0]) < 0.1:
                prev_content[cur_time] = [data, data - float(prev_content[list(prev_content.keys())[-1]][0])]
            else:
                prev_content[cur_time] = [data, data]
        with open(json, 'w') as jsonfile:
            js.dump(prev_content, jsonfile, indent=0)


def calibrate_rate(hashrate, stale_rate):
    stale_rate = float(stale_rate[:-1])
    if stale_rate > 4.1:
        delta = (stale_rate - 4) / 100 * 5
        if delta >= 0.1:
            return int(hashrate * 0.9)
        hashrate -= hashrate * delta
        return int(hashrate)
    elif stale_rate < 2.3:
        delta = (2.3 - stale_rate) * 3.5 / 100
        if delta > 0.5:
            return int(hashrate * 1.05)
        hashrate += hashrate * delta
        return int(hashrate)
    else:
        return int(hashrate)

def sum_data(start, end, dir_path):
    start = datetime.datetime(year=start[0], month=start[1], day=start[2])
    end = datetime.datetime(year=end[0], month=end[1], day=end[2])
    dir_path = dir_path + r'/????-??-??.csv'
    logs = glob(dir_path)
    logs.sort(key=os.path.getmtime)
    dates = [str(Path(x).stem).split('-') for x in logs]
    dates = [datetime.datetime(year=int(x[0]), month=int(x[1]), day=int(x[2])) for x in dates]
    targets = []
    for i, date in enumerate(dates):
        if start <= date <= end:
            targets.append(logs[i])
    mean_list = []
    for log in targets:
        df_log = pd.read_csv(log, index_col=0)
        mean = pd.DataFrame(df_log.mean(axis=0))
        mean.columns = [f'{log}-average']
        mean_list.append(mean.T)
    mean = pd.concat(mean_list, join='inner')
    mean = mean.round(0)
    mean.to_csv('./data/temp.csv')
    return mean


def get_ref_time(ref_hour=15):
    today = datetime.datetime.now()
    one_day_delta = datetime.timedelta(days=1)
    ref = datetime.datetime(today.year, today.month, today.day, ref_hour)
    mid = datetime.datetime(today.year, today.month, today.day, 0)
    yesterday_ref = ref - one_day_delta
    return ref, mid, yesterday_ref


def income_split(x, y, income):
    return x / (x + y) * income, income - x / (x + y) * income


def income_split_2(x, y):
    percentages = []
    for i, total_income in enumerate(y):
        percentages.append(total_income * np.array(x[i]) / np.sum(np.array(x[i])))
    return percentages


def send_email(recv, miner):
    mail_host = 'smtp.163.com'
    mail_user = 'CaptainPoolAdmin'
    mail_pass = 'ZFFHKHKKMQNIZZDW'
    sender = 'CaptainPoolAdmin@163.com'
    message = MIMEText(f'以下旷工已经掉线: {miner}，赶紧上线学习！', 'plain', 'utf-8')
    message['Subject'] = '你TM掉线了'
    message['From'] = sender
    retry = 3

    while retry:
        try:
            for r in recv:
                message['To'] = r
                smtpObj = smtplib.SMTP()
                smtpObj.connect(mail_host, 25)
                smtpObj.login(mail_user, mail_pass)
                smtpObj.sendmail(sender, r, message.as_string())
                smtpObj.quit()
                retry = 0
                logging.info(f'alert email sent to {r}')

        except smtplib.SMTPException as e:
            retry -= 1
            if retry == 0:
                raise ConnectionError('failed connecting to mail server')


def write_reminder(content):
    with open('./states.json', 'w') as jsfile:
        json.dump(content, jsfile, indent=4)


def read_reminder():
    if not Path('./states.json').exists():
        with open('./states.json', 'w') as jsfile:
            content = {}
            json.dump(content, jsfile)
    with open('./states.json') as jsfile:
        content = json.load(jsfile)
        return content


def read_codebook():
    with open('./email codebook.json') as jsfile:
        return json.load(jsfile)


def random_income(income_sum, days=2):
    split_anchor = 1 / days
    random_split = np.random.uniform(high=split_anchor * 1.05, low=split_anchor * 0.95, size=days)
    random_split *= income_sum
    random_split[-1] = income_sum - np.sum(random_split[:-1])
    return random_split



if __name__ == "__main__":
    # sum_data([2022, 4, 3], [2022, 4, 7], './data')
    # incomes = random_income(0.1433, days=2)
    # print(incomes)
    # pass
    print(income_split_2([[0.07625, 0.07744], [0.08341, 0.08062]], [3379, 3281]))


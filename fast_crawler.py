import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import psutil
import json
import datetime
import re
import pandas as pd
from pathlib import Path
import json as js
from glob import glob
import os

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
            js.dump(prev_content, jsonfile)


def casher(output_dir='./data/'):
    kill_chrome()
    retry = 5
    logging.basicConfig(level=logging.NOTSET)
    options = webdriver.ChromeOptions()
    options.add_argument(r"user-data-dir=C:\Users\monalaptop01\AppData\Local\Google\Chrome\User Data")
    options.add_argument(r"profile-directory=Profile 1")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(r'./chromedriver.exe', chrome_options=options)
    time.sleep(2)
    driver.get("https://hiveon.net/eth/workers?miner=0x0c11ed4f68ed21b51b6bff2b8de0660e721fed08")
    time.sleep(10)
    while retry != 0:
        try:
            all_reading = driver.find_element_by_xpath("/html/body/div[1]/div[1]/div/section[3]/div/div/div[2]").text.split('\n')[8:]
            time.sleep(2)
            # driver.find_element_by_xpath(
            #     "/html/body/div[1]/div[1]/div/section[3]/div/div/div[1]/div[1]/div/div/div/span[2]").click()
            # time.sleep(2)
            # all_reading += driver.find_element_by_xpath(
            #     "/html/body/div[1]/div[1]/div/section[3]/div/div/div[2]").text.split('\n')[8:]
            all_reading = [x for x in all_reading if x != 'MH/s']
            all_reading = [x for x in all_reading if x != 'H/s']
            time.sleep(5)

            retry = 0

            parsed_reading = {}
            for worker in range(0, len(all_reading), 10):
                for tgt_worker in list(read_name_list().keys()):
                    try:
                        parsed_reading[tgt_worker] = parsed_reading[tgt_worker]
                    except KeyError:
                        parsed_reading[tgt_worker] = 0
                    if re.search(toLowerCase(tgt_worker), toLowerCase(all_reading[worker])):
                        parsed_reading[tgt_worker] += round(
                            calibrate_rate(round(float(all_reading[worker + 3])), all_reading[worker + 6]))

            parsed_reading = pd.DataFrame(parsed_reading, index=[f'{datetime.datetime.now().strftime("%d:%H:%M")}'])

            today = datetime.datetime.today()
            tmr = today + datetime.timedelta(days=1)
            now = datetime.datetime.now()
            ref, mid, y_ref = get_ref_time(15)

            if not Path(output_dir).exists():
                Path(output_dir).mkdir()

            if now > ref:
                if not Path(output_dir + f'{tmr.strftime("%Y-%m-%d")}.csv').exists():
                    parsed_reading.to_csv(output_dir + f'{tmr.strftime("%Y-%m-%d")}.csv')
                else:
                    prev_df = pd.read_csv(output_dir + f'{tmr.strftime("%Y-%m-%d")}.csv', index_col=0)
                    prev_df = prev_df.append(parsed_reading)
                    prev_df.to_csv(output_dir + f'{tmr.strftime("%Y-%m-%d")}.csv')
            elif now < ref:
                if not Path(output_dir + f'{today.strftime("%Y-%m-%d")}.csv').exists():
                    parsed_reading.to_csv(output_dir + f'{today.strftime("%Y-%m-%d")}.csv')
                else:
                    prev_df = pd.read_csv(output_dir + f'{today.strftime("%Y-%m-%d")}.csv', index_col=0)
                    prev_df = prev_df.append(parsed_reading)
                    prev_df.to_csv(output_dir + f'{today.strftime("%Y-%m-%d")}.csv')

        except NoSuchElementException:
            driver.refresh()
            time.sleep(10)
            retry -= 1
    time.sleep(5)
    driver.quit()
    time.sleep(5)
    kill_chrome()

    # if not Path(output_dir + f'{datetime.datetime.now().strftime("%Y-%m-%d")}.csv').exists():
    #     parsed_reading.to_csv(output_dir + f'{datetime.datetime.now().strftime("%Y-%m-%d")}.csv')
    # else:
    #     prev_df = pd.read_csv(output_dir + f'{datetime.datetime.now().strftime("%Y-%m-%d")}.csv', index_col=0)
    #     prev_df = prev_df.append(parsed_reading)
    #     prev_df.to_csv(output_dir + f'{datetime.datetime.now().strftime("%Y-%m-%d")}.csv')


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

if __name__ == "__main__":
<<<<<<< HEAD
    # sum_data((2022, 1, 1), (2022, 1, 3), './data')
    print(income_split(0.09126, 0.08724, 4194.38))
    # casher('/data')
=======
    # sum_data((2021, 12, 19), (2021, 12, 22), './data')
    # print(income_split(0.09749, 0.09711, 4573.32))
    casher()
>>>>>>> 0a7aeee47722998f3c824da0391d7254d3a8c9df

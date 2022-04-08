import logging
from selenium import webdriver
import time
import datetime
import re
import os
import pandas as pd
from pathlib import Path
import json as js
from selenium.webdriver.common.by import By

from utils import toLowerCase, kill_chrome, read_name_list, save_today_record, write_to_json, calibrate_rate


def daily_logger(output_dir='./data/'):
    # kill_chrome()
    logging.basicConfig(level=logging.NOTSET)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={os.getenv('APPDATA')}\\Local\\Google\\Chrome\\User Data")
    options.add_argument(r"profile-directory=Profile 1")
    driver = webdriver.Chrome(r'./chromedriver.exe', chrome_options=options)
    time.sleep(2)
    driver.get("https://hiveon.net/eth/workers?miner=0x0c11ed4f68ed21b51b6bff2b8de0660e721fed08")
    time.sleep(10)
    all_reading = driver.find_element(by=By.XPATH, value="/html/body/div[1]/div[1]/div/section[3]/div/div/div[2]").text.split('\n')[8:]
    time.sleep(2)
    driver.find_element(by=By.XPATH, value="/html/body/div[1]/div[1]/div/section[3]/div/div/div[1]/div[1]/div/div/div/span[2]").click()
    time.sleep(2)
    all_reading += driver.find_element(by=By.XPATH, value="/html/body/div[1]/div[1]/div/section[3]/div/div/div[2]").text.split('\n')[8:]
    time.sleep(2)
    unpaid = float(driver.find_element(by=By.XPATH, value="/html/body/div[1]/div[1]/div/section[2]/div/div[1]/div/div[3]/div[1]/div[5]").text.split(' ')[0])
    all_reading = [x for x in all_reading if x != 'MH/s']
    all_reading = [x for x in all_reading if x != 'H/s']
    write_to_json(unpaid)
    time.sleep(5)

    with open('./data/history.json') as jsonfile:
        income = js.load(jsonfile)
        income = income[list(income.keys())[-1]][1]

    parsed_reading = {}
    for worker in range(0, len(all_reading), 10):
        for tgt_worker in list(read_name_list().keys()):
            try:
                parsed_reading[tgt_worker] = parsed_reading[tgt_worker]
            except KeyError:
                parsed_reading[tgt_worker] = 0
            if re.search(toLowerCase(tgt_worker), toLowerCase(all_reading[worker])):

                parsed_reading[tgt_worker] += round(calibrate_rate(round(float(all_reading[worker + 2])), all_reading[worker + 6]))

    parsed_reading = pd.DataFrame(parsed_reading, index=['hashrate']).T

    total_hashrate = parsed_reading['hashrate'].sum()

    income_list = parsed_reading['hashrate'].apply(lambda x: (x / total_hashrate) * income)
    parsed_reading = pd.concat((parsed_reading, income_list), axis=1).T

    if not Path(output_dir).exists():
        Path(output_dir).mkdir()
    parsed_reading.to_csv(output_dir + f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")}-processed.csv')
    time.sleep(5)
    driver.quit()


if __name__ == "__main__":
    daily_logger()

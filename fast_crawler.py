import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import datetime
import re
import pandas as pd
import os
from pathlib import Path
from utils import toLowerCase, kill_chrome, read_name_list, save_today_record, write_to_json, calibrate_rate, \
    get_ref_time, read_reminder, write_reminder, send_email, read_codebook


def fast_logger(output_dir='./data/'):
    kill_chrome()
    retry = 5
    logging.basicConfig(level=logging.NOTSET)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={os.getenv('LOCALAPPDATA')}\\Google\\Chrome\\User Data")
    options.add_argument(r"profile-directory=Profile 1")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(r'./chromedriver.exe', chrome_options=options)
    time.sleep(2)
    driver.get("https://hiveon.net/eth/workers?miner=0x0c11ed4f68ed21b51b6bff2b8de0660e721fed08")
    time.sleep(2)
    while retry != 0:
        try:
            all_reading = driver.find_element_by_xpath("/html/body/div[1]/div[1]/div/section[3]/div/div/div[2]").text.split('\n')[8:]
            time.sleep(2)
            try:
                driver.find_element_by_xpath(
                    "/html/body/div[1]/div[1]/div/section[3]/div/div/div[1]/div[1]/div/div/div/span[2]").click()
                time.sleep(2)
                offlines = driver.find_element_by_xpath(
                    "/html/body/div[1]/div[1]/div/section[3]/div/div/div[2]").text.split('\n')[8:]
                offlines = [x for x in offlines if x != 'MH/s']
                offlines = [x for x in offlines if x != 'H/s']

                tgt_miner = read_codebook()
                offline_miner = {}
                for miner in list(tgt_miner.keys()):
                    empty = True
                    for i in range(0, len(offlines), 10):
                        if re.search(toLowerCase(miner), toLowerCase(offlines[i])):
                            if empty:
                                offline_miner[miner] = [offlines[i]]
                            else:
                                offline_miner[miner].append(offlines[i])
                prev_state = read_reminder()
                prev_state_ = prev_state.copy()
                for prev_off_miner in (prev_state.keys()):
                    if prev_off_miner not in (offline_miner.keys()):
                        del prev_state_[prev_off_miner]
                prev_state = prev_state_
                for off_miner in list(offline_miner.keys()):
                    try:
                        if prev_state[off_miner] > 0:
                            prev_state[off_miner] -= 1
                            logging.info(f'recv={[tgt_miner[off_miner][0]]}, miner={offline_miner[off_miner]}, remain={prev_state[off_miner]}')
                            # send_email(recv=[tgt_miner[off_miner][0]], miner=offline_miner[off_miner])
                        elif prev_state[off_miner] == -1:
                            logging.info(f'recv={[tgt_miner[off_miner][0]]}, miner={offline_miner[off_miner]}, infinite')
                            # send_email(recv=[tgt_miner[off_miner][0]], miner=offline_miner[off_miner])
                    except KeyError:
                        prev_state[off_miner] = tgt_miner[off_miner][1]
                write_reminder(prev_state)

            except NoSuchElementException:
                pass

            all_reading = [x for x in all_reading if x != 'MH/s']
            all_reading = [x for x in all_reading if x != 'H/s']

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
                if not Path(output_dir + f'/{tmr.strftime("%Y-%m-%d")}.csv').exists():
                    parsed_reading.to_csv(output_dir + f'/{tmr.strftime("%Y-%m-%d")}.csv')
                else:
                    prev_df = pd.read_csv(output_dir + f'/{tmr.strftime("%Y-%m-%d")}.csv', index_col=0)
                    prev_df = prev_df.append(parsed_reading)
                    prev_df.to_csv(output_dir + f'/{tmr.strftime("%Y-%m-%d")}.csv')
            elif now < ref:
                if not Path(output_dir + f'{today.strftime("%Y-%m-%d")}.csv').exists():
                    parsed_reading.to_csv(output_dir + f'/{today.strftime("%Y-%m-%d")}.csv')
                else:
                    prev_df = pd.read_csv(output_dir + f'/{today.strftime("%Y-%m-%d")}.csv', index_col=0)
                    prev_df = prev_df.append(parsed_reading)
                    prev_df.to_csv(output_dir + f'/{today.strftime("%Y-%m-%d")}.csv')

        except NoSuchElementException:
            driver.refresh()
            time.sleep(10)
            retry -= 1
    time.sleep(5)
    driver.quit()
    time.sleep(5)
    kill_chrome()


if __name__ == "__main__":
    fast_logger('./data')

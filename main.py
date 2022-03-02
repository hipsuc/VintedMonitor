from monitor_vinted import MonitorVinted
import pandas as pd
import json
from threading import Thread
from time import sleep

monitors = []
threads = []

def main() -> None:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
        webhook_link = config["webhook_link"]
        webhook_avatar = config["webhook_avatar"]
        webhook_name = config["webhook_name"]
        delay = config["delay"]
    df = pd.read_csv("tasks.csv", dtype="string")
    for i in range(len(df)):
        print(df.iloc[i]["proxies"])
        monitors.append(MonitorVinted(df.iloc[i]["keyword"], df.iloc[i]["filter"], df.iloc[i]["rpp"], df.iloc[i]["min_price"], df.iloc[i]["max_price"], df.iloc[i]["min_seller_eval"], df.iloc[i]["min_seller_mark"], df.iloc[i]["proxies"], webhook_link, delay, webhook_avatar, webhook_name))
    for monitor in monitors:
        t = Thread(target=monitor.monitor, args=())
        t.start()
        sleep(3)
        threads.append(t)
    for thread in threads:
        thread.join()
    threads.clear()

if __name__ == "__main__":
    main()

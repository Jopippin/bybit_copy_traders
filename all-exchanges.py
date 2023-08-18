import csv
import requests
from datetime import datetime

class Trade:
    def __init__(self, open_time, side):
        self.open_time = open_time
        self.side = side

okx_all_traders_url = "https://www.okx.com/priapi/v5/ecotrade/public/follow-rank"
okx_open_trades_url = "https://www.okx.com/priapi/v5/ecotrade/public/position-detail"
okx_bot_trades_url = "https://www.okx.com/priapi/v5/algo/marketplace/public/profit-sharing/orders-pending"


gate_leader_list_url = "https://www.gate.io/api/copytrade/copy_trading/trader/profit"
gate_open_trades_url = "https://www.gate.io/api/copytrade/copy_trading/trader/position"

bb_leader_list_url = "https://api2.bybit.com/fapi/beehive/public/v1/common/dynamic-leader-list"
bb_open_trades_url = "https://api2.bybit.com/fapi/beehive/public/v1/common/order/list-detail"

def get_okx_trades_data():
    trades_data = []

    page_size = 20 # max allowed value per request by OKX's API
    page_no = 1
    total_pages = 1

    while page_no <= total_pages:
        params = {
            "size" : str(page_size),
            "num" : str(page_no),
            "sort": "desc"
        }

        response = requests.get(okx_all_traders_url, params=params)

        if response.status_code == 200:
            traders_json = response.json()

            if 'data' in traders_json:
                data = traders_json.get('data', [])[0]
                total_pages = int(data.get('pages', 1))
                traders_data = data.get('ranks', [])

                for trader in traders_data:
                    trader_unique_name = trader.get('uniqueName', '')
                    
                    open_trades_params = {
                        "uniqueName" : str(trader_unique_name)
                    }

                    open_trades_res = requests.get(okx_open_trades_url, params=open_trades_params)

                    if open_trades_res.status_code == 200:
                            open_trades_json = open_trades_res.json()

                            if 'data' in open_trades_json:
                                open_trades = open_trades_json.get('data')

                                if open_trades:
                                    for trade in open_trades:
                                        open_time = convert_to_milliseconds(trade.get('openTime', 0))
                                        side = "LONG" if trade.get('posSide') == 'long' else "SHORT"

                                        trade_object = Trade(open_time, side)
                                        trades_data.append(trade_object)
                    
                    bot_trades_params = {
                        "traderUniqueName" : str(trader_unique_name),
                        "page" : "1",
                        "pageSize" : "9"
                    }

                    bot_trades_res = requests.get(okx_bot_trades_url, params=bot_trades_params)

                    if bot_trades_res.status_code == 200:
                        bot_trades_json = bot_trades_res.json()
                        if 'data' in bot_trades_json:
                            bot_trades_data = bot_trades_json.get('data', [])[0]
                            bot_trades = bot_trades_data.get('strategies', [])
                            if bot_trades:
                                for bot_trade in bot_trades:
                                    bot_side = "LONG" if bot_trade.get('direction') == 'long' else "SHORT"
                                    bot_runtime = int(bot_trade.get('cTime', 0))

                                    trade_object = Trade(open_time, side)
                                    trades_data.append(trade_object)

        page_no += 1

    return trades_data

def get_gate_trades_data():
    trades_data = []

    page_size = 100 # max allowed value per request by Gate's API
    page_no = 1
    total_pages = 1

    while page_no <= total_pages:
        params = {
            "status": "running",
            "order_by": "sharp_ratio",
            "sort_by": "desc",
            "page": str(page_no),
            "page_size": str(page_size),
            "cycle": "threemonth",
        }

        response = requests.get(gate_leader_list_url, params=params)

        if response.status_code == 200:
            leader_data = response.json()

            total_pages = int(leader_data.get('pagecount', 1)) # default value 1 if 'pagecount' is not present

            if 'data' in leader_data:
                leaders = leader_data.get('data', []);

                for leader in leaders:
                    leader_id = leader.get('leader_id', '')

                    open_trades_params = {
                        "leader_id" : leader_id,
                        "page_size" : "10",
                        "page" : "1"
                    }

                    open_trades_res = requests.get(gate_open_trades_url, params=open_trades_params)

                    if open_trades_res.status_code == 200:
                        open_trades_data = open_trades_res.json()

                        if 'data' in open_trades_data:
                            open_trades = open_trades_data.get('data', [])

                            if open_trades:
                                for trade in open_trades:                     
                                    trade_update_time = convert_to_milliseconds(trade.get('update_time', 0))
                                    trade_side = "LONG" if trade.get('mode') == 1 else "SHORT"

                                    trade_object = Trade(trade_update_time, trade_side)
                                    trades_data.append(trade_object)

        page_no += 1
    
    return trades_data

def get_bybit_trades_data():
    trades_data = []

    page_size = 16
    page_no = 1
    total_pages = 1

    while page_no <= total_pages:
        params = {
            "timeStamp": "1691913286002",
            "pageNo": str(page_no),
            "pageSize": str(page_size),
            "dataDuration": "DATA_DURATION_NINETY_DAY",  
            "leaderTag": "LEADER_TAG_TOP_TRADING_STRATEGIES",
            "code": "",
            "leaderLevel": "",
            "userTag": ""
        }

        response = requests.get(bb_leader_list_url, params=params)

        if response.status_code == 200:
            data = response.json()

            if 'result' in data and 'leaderDetails' in data['result']:
                leader_details = data['result']['leaderDetails']

                total_pages = int(data['result']['totalPageCount'])

                for leader in leader_details:
                    leader_mark = leader.get('leaderMark')

                    open_trades_params = {
                        "timeStamp": "1691913819857",
                        "leaderMark": leader_mark,
                        "pageSize": "8",
                        "page": "1"
                    }

                    open_trades_response = requests.get(bb_open_trades_url, params=open_trades_params)

                    if open_trades_response.status_code == 200:
                        open_trades_data = open_trades_response.json()

                        if 'result' in open_trades_data and 'data' in open_trades_data['result']:
                            open_trades = open_trades_data['result']['data']
                            open_trade_info_protection = open_trades_data['result']['openTradeInfoProtection']

                            if open_trade_info_protection == 0:
                                if open_trades:
                                    for trade in open_trades:
                                        created_at_e3 = convert_to_milliseconds(trade.get('createdAtE3'))
                                        side = trade.get('side')
                                        side_display = "LONG" if side == "Buy" else "SHORT"

                                        trade_object = Trade(created_at_e3, side_display)
                                        trades_data.append(trade_object)

        page_no += 1

    return trades_data

def convert_to_milliseconds(timestamp):
    if len(str(timestamp)) == 10:
        return int(timestamp) * 1000
    return timestamp

if __name__ == "__main__":
    all_trades = []

    okx_trades_data = get_okx_trades_data()
    all_trades.extend(okx_trades_data)

    gate_trades_data = get_gate_trades_data()
    all_trades.extend(gate_trades_data)

    bybit_trades_data = get_bybit_trades_data()
    all_trades.extend(bybit_trades_data)

    trade_data = []
    for trade in all_trades:
        trade_data.append([
            trade.open_time, 
            trade.side
        ])

    csv_filename = "trades.csv"
    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Open Time", "Side"])
        writer.writerows(trade_data)

    print(f"Data written to {csv_filename}")
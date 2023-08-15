import requests
import time
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed

leader_list_url = "https://api2.bybit.com/fapi/beehive/public/v1/common/dynamic-leader-list"
open_trades_url = "https://api2.bybit.com/fapi/beehive/public/v1/common/order/list-detail"
leader_income_url = "https://api2.bybit.com/fapi/beehive/public/v1/common/leader-income"
page_size = 16
page_no = 1
total_pages = 1

logged_trade_ids = set()

while page_no <= total_pages:
    params = {
        "timeStamp": "1691998238971",
        "pageNo": str(page_no),
        "pageSize": str(page_size),
        "dataDuration": "DATA_DURATION_NINETY_DAY",
        "leaderTag": "",
        "code": "",
        "leaderLevel": "COPY_TRADE_LEADER_LEVEL_BRONZE_TRADER,COPY_TRADE_LEADER_LEVEL_SILVER_TRADER,COPY_TRADE_LEADER_LEVEL_GOLD_TRADER",
        "userTag": "6"
    }

    response = requests.get(leader_list_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if 'result' in data and 'leaderDetails' in data['result']:
            leader_details = data['result']['leaderDetails']
            total_pages = int(data['result']['totalPageCount'])

            for leader in leader_details:
                leader_mark = leader.get('leaderMark')
                nick_name = leader.get('nickName')
                profile_photo_url = leader.get('profilePhoto')
                stable_score_level = leader.get('metricValues')[4] if 'metricValues' in leader else ""
                last_leader_level = leader.get('lastLeaderLevel')
                win_rate = leader.get('metricValues')[3] if 'metricValues' in leader else ""
                roi = leader.get('metricValues')[0] if 'metricValues' in leader else ""
                total_trade_profit = leader.get('metricValues')[1] if 'metricValues' in leader else ""
                total_follow_profit = leader.get('metricValues')[2] if 'metricValues' in leader else ""

                print(f"------------------------------")
                print(f"{leader_mark} {nick_name}")
                print(f"{last_leader_level.replace('COPY_TRADE_LEADER_LEVEL_', '')}")
                print(f"90d Stability: {stable_score_level}")
                print(f"90d Win Rate: {win_rate}")
                print(f"90d ROI: {roi}")
                print(f"90d PnL: {total_trade_profit}")
                print(f"90d Followers PnL: {total_follow_profit}")

                leader_income_params = {
                    "timeStamp": "1691934031528",
                    "leaderMark": leader_mark
                }

                leader_income_response = requests.get(leader_income_url, params=leader_income_params)
                leader_income_data = leader_income_response.json()

                if 'result' in leader_income_data:
                    ninety_day_yield_rate = leader_income_data['result']['ninetyDayYieldRateE4']
                    cum_trade_count = leader_income_data['result']['cumTradeCount']
                    cum_win_count = leader_income_data['result']['cumWinCount']
                    cum_loss_count = leader_income_data['result']['cumLossCount']
                    ninety_day_profit = int(leader_income_data['result']['ninetyDayProfitE8'])

                    print(f"90d Yield Rate: {ninety_day_yield_rate}")
                    print(f"90d Trade Count: {cum_trade_count}")
                    print(f"90d Win Count: {cum_win_count}")
                    print(f"90d Loss Count: {cum_loss_count}")

                    if ninety_day_profit >= 1000000:
                        ninety_day_profit_str = f"{ninety_day_profit / 1000000:.2f}M"
                    elif ninety_day_profit >= 1000:
                        ninety_day_profit_str = f"{ninety_day_profit / 1000:.2f}K"
                    else:
                        ninety_day_profit_str = str(ninety_day_profit)
                    print(f"90d Profit: {ninety_day_profit_str}")

                    ave_position_time_minutes_str = leader_income_data['result']['avePositionTime']
                    ave_position_time_minutes = int(ave_position_time_minutes_str)

                    ave_position_time_hours = ave_position_time_minutes / 60

                    print(f"Avr Holding Time: {ave_position_time_hours:.2f} hours")

                open_trades_params = {
                    "timeStamp": "1691913819857",
                    "leaderMark": leader_mark,
                    "pageSize": "8",
                    "page": "1"
                }

                open_trades_response = requests.get(open_trades_url, params=open_trades_params)
                open_trades_data = open_trades_response.json()

                if 'result' in open_trades_data and 'data' in open_trades_data['result']:
                    open_trades = open_trades_data['result']['data']
                    open_trade_info_protection = open_trades_data['result']['openTradeInfoProtection']

                    if open_trade_info_protection == 0 and open_trades:
                        formatted_trades = []

                        for trade in open_trades:
                            createdtTimeE3 = trade.get('transactTimeE3')

                            if createdtTimeE3 not in logged_trade_ids:
                                # Log the trade in the CSV file
                                symbol = trade.get('symbol')
                                created_at_e3 = trade.get('createdAtE3')
                                created_at = datetime.fromtimestamp(int(created_at_e3) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                                side = trade.get('side')
                                entry_price = trade.get('entryPrice')
                                entry_price_with_currency = f"{entry_price} USDT"
                                side_display = "LONG" if side == "Buy" else "SHORT"

                                leverage_value = int(trade.get('leverageE2', 0)) // 100
                                leverage_display = f"{leverage_value}x"

                                formatted_trade = (
                                    f"{created_at}, {symbol}, {entry_price_with_currency}, {side_display}, {leverage_display} "
                                )

                                

                                if 'stopLossPrice' in trade and trade['stopLossPrice']:
                                    formatted_trade += f", SL: {trade['stopLossPrice']}"
                                if 'takeProfitPrice' in trade and trade['takeProfitPrice']:
                                    formatted_trade += f", TP: {trade['takeProfitPrice']}"

                                trade_identifier = f"{created_at}"
                                trade_already_logged = False

                                with open("trade_log.txt", "r", encoding="utf-8") as file:
                                    for line in file:
                                        if trade_identifier in line:
                                            trade_already_logged = True
                                            break

                                if not trade_already_logged:
                                    formatted_trades.append(formatted_trade)
                                    logged_trade_ids.add(created_at)

                        if formatted_trades:
                            # Log trades to the CSV file
                            with open("trade_log.txt", "a", encoding="utf-8") as file:
                                for trade in formatted_trades:
                                    file.write(trade + "\n")

                            webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1140007491850211459/8gGy_GBT0LwgDXMrsJxnG15GqZ7p7PtJHV5VHYxDLq-QDxCJquapO0bQL5Y11akxhnzV')
                            embed = DiscordEmbed(title=f"{nick_name} Opened Some Trades", color=242424)
                            embed.set_thumbnail(url=profile_photo_url)
                            trader_info = (
                                f"{last_leader_level.replace('COPY_TRADE_LEADER_LEVEL_', '')}\n\n"
                                f"90d Stability: {stable_score_level}\n"
                                f"90d Win Rate: {win_rate}\n"
                                f"90d ROI: {roi}\n"
                                f"90d PnL: {total_trade_profit}\n"
                                f"90d Followers PnL: {total_follow_profit}\n"
                                f"90d Yield Rate: {ninety_day_yield_rate}\n"
                                f"90d Trade Count: {cum_trade_count}\n"
                                f"90d Win Count: {cum_win_count}\n"
                                f"90d Loss Count: {cum_loss_count}\n"
                                f"90d Profit: {ninety_day_profit_str}\n"
                                f"Avr Holding Time: {ave_position_time_hours:.2f} hours\n\n"
                            )

                            trader_info += "\n".join(formatted_trades)

                            embed.add_embed_field(name="", value=trader_info, inline=False)
                            webhook.add_embed(embed)
                            webhook.execute()

    page_no += 1

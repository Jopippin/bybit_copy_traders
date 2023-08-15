import re
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook, DiscordEmbed

current_time = datetime.now()
four_hour_threshold = current_time - timedelta(hours=4)
one_hour_threshold = current_time - timedelta(hours=1)

total_trades_4h = 0
buy_count_4h = 0
sell_count_4h = 0
total_trades_1h = 0
buy_count_1h = 0
sell_count_1h = 0

with open("trade_log.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

for line in lines:
    match = re.search(r"crtime: (\d+-\d+-\d+ \d+:\d+), ([A-Za-z]+), ([A-Za-z\s]+)", line)
    if match:
        logging_time_str = match.group(1)
        long_short = match.group(2).strip()

        logging_time = datetime.strptime(logging_time_str, "%Y-%m-%d %H:%M")

        if logging_time >= four_hour_threshold:
            total_trades_4h += 1
            if long_short == "Buy":
                buy_count_4h += 1
            elif long_short == "Sell":
                sell_count_4h += 1

        if logging_time >= one_hour_threshold:
            total_trades_1h += 1
            if long_short == "Buy":
                buy_count_1h += 1
            elif long_short == "Sell":
                sell_count_1h += 1

def calculate_percentages(total, count):
    return (count * 100.0 / total) if total > 0 else 0

buy_percentage_4h = calculate_percentages(total_trades_4h, buy_count_4h)
sell_percentage_4h = calculate_percentages(total_trades_4h, sell_count_4h)
buy_percentage_1h = calculate_percentages(total_trades_1h, buy_count_1h)
sell_percentage_1h = calculate_percentages(total_trades_1h, sell_count_1h)

if buy_percentage_1h > sell_percentage_1h:
    buy_color_1h = 0x00FF00  
    sell_color_1h = 0xFF0000  
else:
    buy_color_1h = 0xFF0000  
    sell_color_1h = 0x00FF00  

webhook_url = "https://discord.com/api/webhooks/1140587850799272119/k0iLtH6xqc7fbaxwoE-ptZcv71g1S36ae_TDdj9lGwVeFyEPx4k5X3DxhrZ-FkTI0Pla"
webhook = DiscordWebhook(url=webhook_url)

embed = DiscordEmbed(title="Trade Analysis", description="Trading statistics for the past 1 hour and 4 hours")

if buy_percentage_1h > sell_percentage_1h:
    embed.set_color(buy_color_1h)
else:
    embed.set_color(sell_color_1h)

embed.add_embed_field(name="Past 1 Hour",
                      value=f"Total Trades: {total_trades_1h}\n"
                            f"%Long: {buy_percentage_1h:.2f}%\n"
                            f"%Short: {sell_percentage_1h:.2f}%")

embed.add_embed_field(name="Past 4 Hours",
                      value=f"Total Trades: {total_trades_4h}\n"
                            f"%Long: {buy_percentage_4h:.2f}%\n"
                            f"%Short: {sell_percentage_4h:.2f}%")

webhook.add_embed(embed)
response = webhook.execute()

print("Past 4 Hours:")
print("Number of Trades Total:", total_trades_4h)
print("%Long:", buy_percentage_4h)
print("%Short:", sell_percentage_4h)
print("\nPast 1 Hour:")
print("Number of Trades Total:", total_trades_1h)
print("%Long:", buy_percentage_1h)
print("%Short:", sell_percentage_1h)

if response.status_code == 204:
    print("Data sent successfully to Discord webhook!")
else:
    print("Failed to send data to Discord webhook.")

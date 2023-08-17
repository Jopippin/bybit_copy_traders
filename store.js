const fetch = require('node-fetch');
const fs = require('fs');

class Trade {
    constructor(open_time, side) {
        this.open_time = open_time;
        this.side = side;
    }
}

const okxAllTradersUrl = "https://www.okx.com/priapi/v5/ecotrade/public/follow-rank";
const okxOpenTradesUrl = "https://www.okx.com/priapi/v5/ecotrade/public/position-detail";
const okxBotTradesUrl = "https://www.okx.com/priapi/v5/algo/marketplace/public/profit-sharing/orders-pending";

const gateLeaderListUrl = "https://www.gate.io/api/copytrade/copy_trading/trader/profit";
const gateOpenTradesUrl = "https://www.gate.io/api/copytrade/copy_trading/trader/position";

const bbLeaderListUrl = "https://api2.bybit.com/fapi/beehive/public/v1/common/dynamic-leader-list";
const bbOpenTradesUrl = "https://api2.bybit.com/fapi/beehive/public/v1/common/order/list-detail";

async function getOkxTradesData() {
    const tradesData = [];

    let pageSize = 20;
    let pageNo = 1;
    let totalPages = 1;

    while (pageNo <= totalPages) {
        const params = new URLSearchParams({
            "size": pageSize.toString(),
            "num": pageNo.toString(),
            "sort": "desc"
        });

        const response = await fetch(`${okxAllTradersUrl}?${params}`);

        if (response.ok) {
            const tradersJson = await response.json();

            if ('data' in tradersJson) {
                const data = tradersJson.data[0];
                totalPages = parseInt(data.pages) || 1;
                const tradersData = data.ranks || [];

                for (const trader of tradersData) {
                    const traderUniqueName = trader.uniqueName;

                    const openTradesParams = new URLSearchParams({
                        "uniqueName": traderUniqueName
                    });

                    const openTradesRes = await fetch(`${okxOpenTradesUrl}?${openTradesParams}`);

                    if (openTradesRes.ok) {
                        const openTradesJson = await openTradesRes.json();

                        if ('data' in openTradesJson) {
                            const openTrades = openTradesJson.data || [];

                            for (const trade of openTrades) {
                                const openTime = convertToMilliseconds(trade.openTime);
                                const side = trade.posSide === 'long' ? "LONG" : "SHORT";

                                const tradeObject = new Trade(openTime, side);
                                tradesData.push(tradeObject);
                            }
                        }
                    }

                    const botTradesParams = new URLSearchParams({
                        "traderUniqueName": traderUniqueName,
                        "page": "1",
                        "pageSize": "9"
                    });

                    const botTradesRes = await fetch(`${okxBotTradesUrl}?${botTradesParams}`);

                    if (botTradesRes.ok) {
                        const botTradesJson = await botTradesRes.json();
                        if ('data' in botTradesJson) {
                            const botTradesData = botTradesJson.data[0];
                            const botTrades = botTradesData.strategies || [];

                            for (const botTrade of botTrades) {
                                const botSide = botTrade.direction === 'long' ? "LONG" : "SHORT";
                                const botRuntime = parseInt(botTrade.cTime) || 0;

                                const tradeObject = new Trade(botRuntime, botSide);
                                tradesData.push(tradeObject);
                            }
                        }
                    }
                }
            }
        }

        pageNo++;
    }

    return tradesData;
}

async function getGateTradesData() {
    const tradesData = [];

    let pageSize = 100;
    let pageNo = 1;
    let totalPageCount = 1;

    while (pageNo <= totalPageCount) {
        const params = new URLSearchParams({
            "status": "running",
            "order_by": "sharp_ratio",
            "sort_by": "desc",
            "page": pageNo.toString(),
            "page_size": pageSize.toString(),
            "cycle": "threemonth",
        });

        const response = await fetch(`${gateLeaderListUrl}?${params}`);

        if (response.ok) {
            const leaderData = await response.json();

            totalPageCount = parseInt(leaderData.pagecount) || 1;

            if ('data' in leaderData) {
                const leaders = leaderData.data;

                for (const leader of leaders) {
                    const leaderId = leader.leader_id;

                    const openTradesParams = new URLSearchParams({
                        "leader_id": leaderId,
                        "page_size": "10",
                        "page": "1"
                    });

                    const openTradesRes = await fetch(`${gateOpenTradesUrl}?${openTradesParams}`);

                    if (openTradesRes.ok) {
                        const openTradesData = await openTradesRes.json();

                        if ('data' in openTradesData) {
                            const openTrades = openTradesData.data;

                            for (const trade of openTrades) {
                                const updateTime = convertToMilliseconds(trade.update_time);
                                const tradeSide = trade.mode === 1 ? "LONG" : "SHORT";

                                const tradeObject = new Trade(updateTime, tradeSide);
                                tradesData.push(tradeObject);
                            }
                        }
                    }
                }
            }
        }

        pageNo++;
    }

    return tradesData;
}

async function getBybitTradesData() {
    const tradesData = [];

    let pageSize = 16;
    let pageNo = 1;
    let totalPageCount = 1;

    while (pageNo <= totalPageCount) {
        const params = new URLSearchParams({
            "timeStamp": "1691913286002",
            "pageNo": pageNo.toString(),
            "pageSize": pageSize.toString(),
            "dataDuration": "DATA_DURATION_NINETY_DAY",  
            "leaderTag": "LEADER_TAG_TOP_TRADING_STRATEGIES",
            "code": "",
            "leaderLevel": "",
            "userTag": ""
        });

        const response = await fetch(`${bbLeaderListUrl}?${params}`);

        if (response.ok) {
            const data = await response.json();

            if ('result' in data && 'leaderDetails' in data.result) {
                const leaderDetails = data.result.leaderDetails;

                totalPageCount = parseInt(data.result.totalPageCount);

                for (const leader of leaderDetails) {
                    const leaderMark = leader.leaderMark;

                    const openTradesParams = new URLSearchParams({
                        "timeStamp": "1691913819857",
                        "leaderMark": leaderMark,
                        "pageSize": "8",
                        "page": "1"
                    });

                    const openTradesResponse = await fetch(`${bbOpenTradesUrl}?${openTradesParams}`);

                    if (openTradesResponse.ok) {
                        const openTradesData = await openTradesResponse.json();

                        if ('result' in openTradesData && 'data' in openTradesData.result) {
                            const openTrades = openTradesData.result.data;
                            const openTradeInfoProtection = openTradesData.result.openTradeInfoProtection;

                            if (openTradeInfoProtection === 0) {
                                for (const trade of openTrades) {
                                    const createdAtE3 = convertToMilliseconds(trade.createdAtE3);
                                    const side = trade.side;
                                    const sideDisplay = side === "Buy" ? "LONG" : "SHORT";

                                    const tradeObject = new Trade(createdAtE3, sideDisplay);
                                    tradesData.push(tradeObject);
                                }
                            }
                        }
                    }
                }
            }
        }

        pageNo++;
    }

    return tradesData;
}

function convertToMilliseconds(timestamp) {
    if (timestamp.toString().length === 10) {
        return parseInt(timestamp) * 1000;
    }
    return timestamp;
}

// The entry point of the script
(async () => {
    const allTrades = [];

    const okxTradesData = await getOkxTradesData();
    allTrades.push(...okxTradesData);

    const gateTradesData = await getGateTradesData();
    allTrades.push(...gateTradesData);

    const bybitTradesData = await getBybitTradesData();
    allTrades.push(...bybitTradesData);

    const tradeData = allTrades.map(trade => [trade.open_time, trade.side]);

    const csvFilename = "trades.csv";
    const csvContent = "Open Time,Side\n" + tradeData.map(row => row.join(",")).join("\n");

    fs.writeFileSync(csvFilename, csvContent, 'utf-8');
    console.log(`Data written to ${csvFilename}`);
})();

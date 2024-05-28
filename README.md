# Crypto Trading Bot

This Crypto Trading Bot is designed to trade Crypto currencies on the Binance exchange. The bot implements two trading strategies: Mean Reversion and Momentum. It dynamically adjusts the order quantities based on the available balance and uses risk management techniques to limit potential losses.

## Features

- **Mean Reversion Strategy:** Buys when the price is below the lower Bollinger Band and sells when the price is above the upper Bollinger Band.
- **Momentum Strategy:** Buys when the price is above the Exponential Moving Average (EMA) and sells at a small profit.
- **ATR-Based Position Sizing:** Uses the Average True Range (ATR) to determine the position size based on market volatility and available balance.
- **Smart Order Routing:** Splits large orders into smaller chunks to minimize market impact.
- **Risk Management:** Applies stop-loss and take-profit orders to manage risk.
- **Real-Time Logging:** Logs all actions and decisions for monitoring and debugging.


## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/SatheeshPeriyasamy/Market_Maker_Bot_Binance.git
    cd Market_Maker_Bot_Binance
    ```

2. Install the required Python packages:

    ```bash
    pip install ccxt pandas ta
    ```

## Configuration

1. Set up your Binance API key and secret in the `binance` initialization:

    ```python
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'
    ```

2. Adjust the risk management parameters as needed:

    ```python
    risk_percentage = 0.01  # 1% risk
    stop_loss_pct = 0.01    # 1% stop-loss
    take_profit_pct = 0.02  # 2% take-profit
    ```

## Usage

Run the bot with:

```bash
python bot.py
 ```
## Disclaimar
This bot is provided for educational purposes only. Trading cryptocurrencies involves significant risk and can result in substantial losses. Use this bot at your own risk. The authors are not responsible for any financial losses you may incur.


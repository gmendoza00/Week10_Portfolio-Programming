import sqlite3
import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt
import pandas as pd
import requests
import yfinance as yf
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class DatabaseManager:
    def __init__(self):
        self.connection = sqlite3.connect('financial_data.db')
        self.cursor = self.connection.cursor()
        self.create_tables()

    def close(self):
        self.connection.close()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Stocks (
                                ticker TEXT,
                                name TEXT,
                                quantity INTEGER,
                                purchase_price REAL,
                                current_price REAL,
                                dividend_yield REAL,
                                earnings_per_share REAL
                              )''')
        self.connection.commit()


class DataAnalysis:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def calculate_moving_average(self, df, window=20):
        return df['Close'].rolling(window=window).mean()

    def calculate_ema(self, df, span=20):
        return df['Close'].ewm(span=span, adjust=False).mean()

    def plot_moving_averages(self, df, sma, ema):
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['Close'], label='Close Price', color='blue')
        plt.plot(df.index, sma, label='SMA', color='orange')
        plt.plot(df.index, ema, label='EMA', color='green')
        plt.title('Stock Price with Moving Averages')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.show()


class Application(tk.Tk):
    def __init__(self, db_manager, data_analysis):
        super().__init__()
        self.db_manager = db_manager
        self.data_analysis = data_analysis
        self.title("Financial Data Analysis")
        self.geometry("600x400")
        self.session = self.setup_requests_session()
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self, text="Enter Ticker Symbol:")
        self.label.pack(pady=10)
        self.entry = tk.Entry(self)
        self.entry.pack(pady=10)
        self.button = tk.Button(self, text="Fetch & Analyze Data", command=self.fetch_and_analyze_data)
        self.button.pack(pady=20)

    def setup_requests_session(self):
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]  # Use allowed_methods instead of method_whitelist
        )
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def fetch_and_analyze_data(self):
        ticker = self.entry.get().strip().upper()
        try:
            data = yf.download(ticker, start="2023-01-01", end="2024-01-01", session=self.session)
            if data.empty or 'Close' not in data.columns:
                messagebox.showerror("Error", "No data fetched for {ticker}. Ticker may be incorrect or delisted.")
                return
            data.reset_index(inplace=True)
            data['date'] = pd.to_datetime(data['Date'])
            data.set_index('date', inplace=True)
            sma = self.data_analysis.calculate_moving_average(data)
            ema = self.data_analysis.calculate_ema(data)
            self.data_analysis.plot_moving_averages(data, sma, ema)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch or analyze data for {ticker}: {str(e)}")


if __name__ == "__main__":
    db_manager = DatabaseManager()
    data_analysis = DataAnalysis(db_manager)
    app = Application(db_manager, data_analysis)
    app.mainloop()

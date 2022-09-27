from __future__ import annotations
import dataclasses
import glob

import yfinance as yf
from pandas import DatetimeIndex, Series
from pytrends.request import TrendReq
import pandas as pd
from pandas.core.frame import DataFrame
import pickle
import matplotlib.pyplot as plt


@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class TrendTickerRelation:
    ticker_name: str
    start: str
    end: str
    trend: pd.DataFrame
    data: pd.DataFrame

    def save(self, path: str = None) -> None:
        path = path or f"{self.ticker_name}_{self.start}_{self.end}.ttr"
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> TrendTickerRelation:
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def fetch(cls, ticker_name: str, start: str, end: str) -> TrendTickerRelation:
        """

        :param ticker_name: NQSTMC or whatever name it is
        :param start: date as 'yyyy-mm-dd'
        :param end: date as 'yyyy-mm-dd'
        :return:
        """
        start_yr, start_month, start_day = (int(x) for x in start.split("-"))
        end_yr, end_month, end_day = (int(x) for x in end.split("-"))
        trend = TrendReq().get_historical_interest([ticker_name],
                                                   year_start=start_yr,
                                                   month_start=start_month,
                                                   day_start=start_day,
                                                   year_end=end_yr,
                                                   month_end=end_month,
                                                   day_end=end_day,
                                                   frequency="daily",
                                                   sleep=60)
        data = yf.download(ticker_name, interval="1d", start=start, end=end)
        return cls(
            ticker_name,
            start,
            end,
            trend,
            data
        )

    def display(self) -> None:
        highs: Series = self.high_values
        d: Series = self.ticker_trend

        plt.plot(d.keys(), d.values)
        plt.plot(highs.keys(), highs.values)
        plt.show()

    @property
    def high_values(self) -> pd.Series:
        return self.data["High"]

    @property
    def ticker_trend(self) -> pd.Series:
        return self.trend[self.ticker_name]

    @property
    def delta_high_values(self) -> pd.Series:
        return self.high_values.diff()

    @property
    def delta_trend_values(self) -> pd.Series:
        return self.ticker_trend.diff()


def inp(statement: str, options: list[str], default: str = None, allow_lower: bool = False) -> str:
    str_options = ", ".join(f'\"{x}\"' for x in options)
    i = input(statement + f"\nenter {str_options}" + f" [{default}]: " if isinstance(default, str) else ": ").strip()
    if not len(options):
        return i if i != "" or default is None else default
    if allow_lower:
        options = [x.lower() for x in options]
        i = i.lower()

    if i == "" and default:
        return default

    while i not in options:
        print("Invalid option... Please choose a valid choice")
        i = input()
        i = i.lower() if allow_lower else i

    return i


def enum_inp(statement, options: list[str], default: int = None) -> int:
    return int(inp(statement + "\n" + "\n".join(f"{i+1}. {x}" + "" for i, x in enumerate(options)),
                   [str(x) for x in range(1, len(options) + 1)], str(default)))


while True:
    command = enum_inp("Enter a Command", [
        "Load from internet",
        "Load from file"
    ], default=1)

    if command == 1:
        ticker = inp("Enter a ticker NASDAQ id", [], default="META")
        start = inp("Enter a starting date (YYYY-MM-DD)", [], default="2022-01-01")
        end = inp("Enter an end date (YYYY-MM-DD)", [], default="2022-06-01")
        try:
            relation = TrendTickerRelation.fetch(ticker, start, end)
        except KeyError:
            print("Google request failed (too many requests).. please try again."
                  "  If this error continues, wait 5-10 mins before trying again")
            continue
        relation.display()
        save = inp("Would you like to save?", ["y", "n"], default="n", allow_lower=True)
        if save:
            relation.save()
    elif command == 2:
        f = list(glob.glob("*.ttr"))
        if not len(f):
            print("No files saved...")
            continue
        file = enum_inp("Enter file to load", f)
        relation = TrendTickerRelation.load(f[file-1])
        relation.display()

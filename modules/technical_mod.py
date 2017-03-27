from __future__ import division
import requests
import quandl
import datetime
from datetime import timedelta, time
from dateutil.relativedelta import relativedelta
import pandas as pd
import math
import numpy as np 


class Bill_Ackman(object):
	TODAY = datetime.date.today()
	SUMMARY_DATA = {}

	def __init__(self, api_key, ticker):
		self.api_key = api_key
		self.ticker = ticker


	def api_call(self, delta): # Delta for the number of weeks we want data for
		end_date = self.TODAY
		start_date = end_date - timedelta(weeks=delta)
		print start_date, end_date, self.ticker

		prices_df = quandl.get('WIKI/'+self.ticker, authtoken=self.api_key, start_date=start_date, end_date=end_date)
		prices_df.index = pd.to_datetime(prices_df.index, infer_datetime_format=True)
		prices_df['Ticker'] = self.ticker
		return prices_df


	def chaikin_mf(self, df):
		df["MF Multiplier"] = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"]))/(df["High"] - df["Low"]) # Money Flow Multiplier formula
		df["MF Volume"] = df["MF Multiplier"] * df["Volume"] # Calculate Money Flow Volume for each period
		CMF_for_period = df["MF Volume"].sum()/df["Volume"].sum()
		self.SUMMARY_DATA["Chaikin Money Flow"] = CMF_for_period


	def ulcer_index(self, df): # default period is 14
		max_close = df["Close"].max()
		df["Pct Drawdown"] = ((df["Close"] - max_close)/max_close) * 100
		df["Pct Drawdown Sq"] = df["Pct Drawdown"].map(lambda x: x ** 2.0)
		
		square_avg = ((df["Pct Drawdown Sq"].sum())/float(len(df["Pct Drawdown Sq"])))
		ulcer_index = math.sqrt(square_avg)
		self.SUMMARY_DATA["Ulcer Index"] = ulcer_index


	def aroon(self, df): # default period is 25
		df["25d High"] = df["High"].rolling(min_periods=25, window=25, center=False).max()
		df["25d Low"] = df["Low"].rolling(min_periods=25, window=25, center=False).min()

		ind = range(0,len(df))
		indexlist = list(ind)
		df.index = indexlist

		recent_high = df.iloc[-1]["25d High"]
		ind_of_high = np.where(df["25d High"]==recent_high)[0][0] # pull first match from numpy array

		recent_low = df.iloc[-1]["25d Low"]
		ind_of_low = np.where(df["25d Low"]==recent_low)[0][0]

		days_since_high = (len(df) - 1) - ind_of_high
		days_since_low = (len(df) - 1) - ind_of_low

		aroon_up = float(((25 - days_since_high)/25) * 100)
		aroon_down = float(((25 - days_since_low)/25) * 100)

		self.SUMMARY_DATA["Aroon Up"] = aroon_up
		self.SUMMARY_DATA["Aroon Down"] = aroon_down


	def rsi(self, df): # Calculate whether a security is overbought or oversold
		df["Change"] = df["Close"] - df["Open"]
		df["Gain"] = df["Change"].map(lambda x: x > 0)

		gain_df = df[df["Gain"]==True]
		loss_df = df[df["Gain"]==False]
		loss_df["Change"] = loss_df["Change"].apply(lambda x: x * -1)

		gain_df["Avg Gain"] = gain_df["Change"].rolling(min_periods=14, window=14, center=False).mean() # Calc mean gain over the last 14 periods
		gain_df["Smoothed Gain"] = gain_df["Avg Gain"].rolling(min_periods=2, window=2, center=False).mean() # Smoothing 
		loss_df["Avg Loss"] = loss_df["Change"].rolling(min_periods=14, window=14, center=False).mean()
		loss_df["Smoothed Loss"] = loss_df["Avg Loss"].rolling(min_periods=2, window=2, center=False).mean()

		# get rid of first 14 entries which we can't calculate a moving avg for
		gain_df = gain_df.dropna(how="any")
		loss_df = loss_df.dropna(how="any") 

		avg_gain = gain_df.iloc[-1]["Smoothed Gain"]
		avg_loss = loss_df.iloc[-1]["Smoothed Loss"]

		rel_strength = avg_gain/avg_loss # over 70 is overbought and below 30 is oversold
		rsi = 100 - (100/(1+rel_strength))

		self.SUMMARY_DATA["Relative Strength Index"] = rsi


	def bollinger_bands(self, df):
		df["Middle Band"] = df["Close"].rolling(min_periods=20, window=20, center=False).mean()
		middle_band = df.iloc[-1]["Middle Band"]

		df["Std Dev"] =  df["Close"].rolling(min_periods=20, window=20, center=False).std()
		df["Upper Band"] = df["Middle Band"] + (df["Std Dev"] * 2)
		df["Lower Band"] = df["Middle Band"] + (df["Std Dev"] * 2)

		# Calculate most recent bands
		std_dev = df.iloc[-1]["Std Dev"]
		upper_band = middle_band + (std_dev * 2)
		lower_band = middle_band - (std_dev * 2)

		# Not a perfect representation but good reference point in the absence of charting
		W_lows = df[df["Close"] < df["Lower Band"]]
		M_tops = df[df["Close"] > df["Upper Band"]]

		self.SUMMARY_DATA["Bollinger Band - Upper"] = upper_band
		self.SUMMARY_DATA["Bollinger Band - Middle"] = middle_band
		self.SUMMARY_DATA["Bollinger Band - Lower"] = lower_band		


	def avg_true_range(self, df): 
		ind = range(0,len(df))
		indexlist = list(ind)
		df.index = indexlist

		for index, row in df.iterrows():
			if index != 0:
				tr1 = row["High"] - row["Low"]
				tr2 = abs(row["High"] - df.iloc[index-1]["Close"])
				tr3 = abs(row["Low"] - df.iloc[index-1]["Close"])

				true_range = max(tr1, tr2, tr3)
				df.set_value(index,"True Range", true_range)

		df["Avg TR"] = df["True Range"].rolling(min_periods=14, window=14, center=False).mean()
		return df


	def chandelier_exit(self, df): # default period is 22
		df_tr = self.avg_true_range(df)

		rolling_high = df_tr["High"][-22:].max()
		rolling_low = df_tr["Low"][-22:].max()

		chandelier_long = rolling_high - df_tr.iloc[-1]["Avg TR"] * 3
		chandelier_short = rolling_low - df_tr.iloc[-1]["Avg TR"] * 3

		self.SUMMARY_DATA["Chandelier Short"] = chandelier_short
		self.SUMMARY_DATA["Chandelier Long"] = chandelier_long


	def run_all(self):
		df = self.api_call(15)
		self.chaikin_mf(df)
		self.ulcer_index(df)
		self.aroon(df)
		self.rsi(df)
		self.bollinger_bands(df)
		self.chandelier_exit(df)
		for key, val in sorted(self.SUMMARY_DATA.items()):
			self.SUMMARY_DATA[key] = "{0:.2f}".format(val)
			print key, val





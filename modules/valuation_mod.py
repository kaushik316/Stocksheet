from __future__ import division
import requests
from bs4 import BeautifulSoup
import re
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


chromedriver = "/Users/kaushikvisvanathan/Documents/chromedriver/chromedriver" # modify as needed with the path to driver
os.environ["webdriver.chrome.driver"] = chromedriver

class Warren_Buffet(object):
	URLS = ["http://www.marketwatch.com/investing/stock/{}", 
	        "http://www.marketwatch.com/investing/stock/{}/financials", 
	        "http://www.marketwatch.com/investing/stock/{}/financials/cash-flow",
	        "https://finance.yahoo.com/quote/{}/key-statistics"]
	SUMMARY_DATA = {"Market cap":" ", "P/E ratio": " ", "EPS":" ", "Dividend": " ", "Div yield": " "}
	 # keys are case sensitive - match data on the mw financials page


	def __init__(self, risk_free_rate, market_return, ticker):
		self.name = "Warren_Buffet"
		self.ticker = ticker
		self.risk_free_rate = risk_free_rate # Return on 10 year US Treasury Bonds
		self.market_return = market_return # 3yr Return on the SPY (S&P 500 tracker)
		self.mw_url = "" # URL with appended ticker


	def selenium_scraper(self,element,url):
		browser = webdriver.Chrome(chromedriver)
		browser.get(url)
		wait = WebDriverWait(browser, 3) 
		# Since there are JS and React elements on the page, need to wait until full page loads
		beta_text = wait.until(EC.visibility_of_element_located((By.XPATH, element))) 
		soup = BeautifulSoup(browser.page_source, "lxml")
		browser.quit()
		return soup


	def y_scraper(self): # Use CAPM formula to calculate cost of equity: Cost of Equity = Rf + Beta(Rm-Rf)
		ystock_url = Warren_Buffet.URLS[3].format(self.ticker)
		scraped_data = {"Beta": "", "Total Debt": ""}

		for key in scraped_data:			
			webpage = self.selenium_scraper("//span[. = '{}']".format(key), ystock_url)
			soup = webpage.find_all("span", text=key)
			for tag in soup:
				scraped_data[key] = tag.parent.next_sibling.text

		self.beta = float(scraped_data["Beta"]) #improve readability of the below formula, dont need this variable.
		self.SUMMARY_DATA["Beta"] = self.beta
		self.SUMMARY_DATA["Total debt"] = self.raw_to_floats(scraped_data["Total Debt"])
		print self.SUMMARY_DATA["Total debt"]
	
		self.cost_of_eq = self.risk_free_rate + self.beta * (self.market_return - self.risk_free_rate)


	def raw_to_floats(self, num): # convert to floats as numbers on MW are represented with a "M" or "B"  			
		multiplier = 1/1000000

		if "M" in num:
			multiplier = 1
		if "B" in num:
			multiplier = 1000 

		processor = re.compile(r'[^\d.]+')
		try:
			processed_num = float(processor.sub('', num))
			n = processed_num * multiplier
			return n
		except ValueError:
			return 0.0


	def mw_scraper(self):
		mw_url = Warren_Buffet.URLS[0].format(self.ticker)
		r = requests.get(mw_url)
		soup = BeautifulSoup(r.text, "lxml")
		# Get the above metrics from the divs having "column data" class
		for item in soup.findAll(True, {"class": re.compile("^(column|data)$")}):
			if 'lastcolumn' in item.attrs['class'] and 'data' in item.attrs['class'] or "column" in item.attrs['class']:
				for key in self.SUMMARY_DATA:	
					if item.text == key:
						letter_check = re.search('[a-zA-Z]', item.find_next_sibling().text) # Check for items that are not pure numbers -e.g "6.6BN"
						if letter_check is not None:
							self.SUMMARY_DATA[key] = self.raw_to_floats(item.find_next_sibling().text)
						else:
							self.SUMMARY_DATA[key] = item.find_next_sibling().text


	def statement_scraper(self, url, *line_items): 
		statement_url = url.format(self.ticker)
		r = requests.get(statement_url)
		soup = BeautifulSoup(r.text, "lxml")

		for line_item in line_items:
			target_list = []
			try:
				target = soup.find("td", text=line_item).parent
				target_row = target.findAll("td", {"class" : "valueCell"})
				for cell in target_row:
					num_in_MMs = self.raw_to_floats(cell.text)
					target_list.append(num_in_MMs)
				yield target_list

			except AttributeError: # Some elements have a "+" icon next to them and searching by text won't work
				table_rows = soup.findAll("td", {"class" : "rowTitle"})
				for row in table_rows:
					if line_item.lower() in row.text.lower():
						_match = re.search(r"" + line_item + "$",row.text) # search for the line item in the results of our scrape
						if _match:
							outer_row = row.parent

				_row = outer_row.findAll("td", {"class" : "valueCell"}) # Create a list with the FCF over the past four years
				_list = []

				for amount in _row:
					amount = self.raw_to_floats(amount.text)
					_list.append(amount)
				yield _list


	def get_growth_rate(self, trend_list):
		#Calculate the growth rate of a list of line items from 2012 - 2016
		trend_list = [num for num in trend_list if num != 0]
		growth_sum = 0
		for a, b in zip(trend_list[::1], trend_list[1::1]):
		    growth_sum += (b - a) / a

		growth_rate = growth_sum/(len(trend_list)-1)
		return growth_rate


	def get_cf(self):
		cf_generator = self.statement_scraper(self.URLS[2], "Free Cash Flow")
		cash_flow = next(cf_generator)
		cf_growth_rate = self.get_growth_rate(cash_flow)
		self.SUMMARY_DATA["Cash Flow"] = cash_flow
		self.SUMMARY_DATA["CF Growth Rate"] = "{0:.2f}%".format(cf_growth_rate * 100)


	def calc_wacc(self):
		self.y_scraper()
		self.mw_scraper()
		is_generator = self.statement_scraper(self.URLS[1], "Gross Interest Expense", "Income Tax", "Pretax Income") # income statement generator
		
		interest_list = next(is_generator)
		int_expense = interest_list[-1]

		tax_list = next(is_generator)
		inc_tax = tax_list[-1]

		pretax_inc_list = next(is_generator)
		pretax_inc = pretax_inc_list[-1]

		if pretax_inc < 1 or inc_tax < 1: # Adjusts for smaller companies who may temporarily have negative income or tax benefits
			tax_rate = 0.35
		else:
			tax_rate = inc_tax/pretax_inc

		self.cost_of_debt = int_expense/self.SUMMARY_DATA["Total debt"]

		weighted_coe = (self.SUMMARY_DATA["Market cap"]/(self.SUMMARY_DATA["Total debt"] + self.SUMMARY_DATA["Market cap"])) * self.cost_of_eq
		weighted_cod = (self.SUMMARY_DATA["Total debt"]/(self.SUMMARY_DATA["Market cap"] + self.SUMMARY_DATA["Total debt"])) * self.cost_of_debt * (1 - tax_rate)

		wacc = weighted_coe + weighted_cod 
		self.SUMMARY_DATA["WACC"] = "{0:.2f}%".format(wacc * 100)
		print "The Weighted Average Cost of Capital for {0:s} is {1:.2f}%. Other key stats are listed below (Total Debt and Market Cap in MM's)".format(self.ticker, (wacc* 100))
		for key in self.SUMMARY_DATA:
			print "{} : {}".format(key, self.SUMMARY_DATA[key])
		

	
		


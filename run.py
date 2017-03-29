from auth import consumer_key, consumer_secret, access_token, access_token_secret, api_key 
import csv
import re
import sys
sys.path.insert(0, '/Users/kaushikvisvanathan/Documents/PythonProjects/Finance/Stocksheet/modules')
from valuation_mod import Warren_Buffet
from technical_mod import Bill_Ackman

ticker = raw_input("Enter the ticker you would like to search for: ")

ticker_list = []
file1 = open('tickers/nasdaqlisted.txt')
file2 = open('tickers/otherlisted.txt')
for line in file1.readlines()[1:] + file2.readlines()[1:]:
    stock = line.strip().split('|')[0]
    if (re.match(r'^[A-Z]+$',stock)):
        ticker_list += [stock]

file1.close()
file2.close()

if ticker in ticker_list:

	try:
		warren = Warren_Buffet(0.025, 0.09, ticker)
		warren.calc_wacc()
		warren.get_cf()
	except ZeroDivisionError:
		print "Unable to calculate cost of debt for this stock"

	bill = Bill_Ackman(api_key,ticker)
	bill.run_all()

	with open("Stocksheet.csv", "w") as sfile:
		writer = csv.writer(sfile)
		writer.writerow(["Ticker", ticker])

		for key, value in warren.SUMMARY_DATA.items():
			writer.writerow([key, value])

		for key, value in sorted(bill.SUMMARY_DATA.items()):
			writer.writerow([key, value])

	sfile.close()

else:
	print "Ticker not found, check spelling and try again"
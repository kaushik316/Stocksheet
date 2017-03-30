# Stocksheet
A program to calculate valuation and technical metrics for a given stock. For a walk through on using these methods in a discounted cash flow valuation of a company, see [here](http://kaushik316-blog.logdown.com/posts/1651749-stock-valuation-with-python). 

### Setup
Your auth.py file should look like this:
```python
# Quandl API key
api_key = 'abdhsk..."
```
Dependencies:
```
Selenium
BeautifulSoup
pandas
numpy
requests
quandl
csv
```
### Usage
Exuecute ```python run.py``` and enter the ticker of the company you would like to obtain metrics for. Output will be written to stocksheet.csv.
```
# Initialize both classes
warren = Warren_Buffet(0.025, 0.09, ticker)
bill = Bill_Ackman(api_key,ticker)
```

### Module Methods

#### Warren.get_cf()
Scrapes and stores historical cash flows and growth rates in the object's SUMMMARY_DATA dictionary.
```python
Warren.get_cf()
cf_list = warren.SUMMARY_DATA["Cash Flow"]
cf_growth_rate = warren.SUMMARY_DATA["Cash Flow"]
print cf_list, cf_growth_rate
```

#### Warren.calc_wacc()
Scrapes information needed to calculate WACC and updates SUMMMARY_DATA dictionary
```python
Warren.calc_wacc()
wacc = Warren.SUMMARY_DATA["WACC"]
coe = Warren.cost_of_eq
cod = Warren.cost_of_debt

print wacc, coe, cod
```

#### Bill.run_all()
Obtains six different technical indicators and saves them in Bill.SUMMARY_DATA dictionary
```
Bill.run_all()
print Bill.SUMMARY_DATA

# stores Aroon indicator, RSI, Bollinger bands, Chaikin Money Flow,
# Chandelier entry and exits and Ulcer index indicators.
```






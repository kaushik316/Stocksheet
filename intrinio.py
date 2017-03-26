import requests
import intrinio

username = "48a049cbc5a8f9e06e5672ef32812478"
password = "8ae148aee524762ae164c4cc5af173da"


p = {'ticker':"AAPL",'statement':'income_statement','type':'QTR'}
auth = {}

url = "https://www.intrinio.com/api/fundamentals/standardized"
r = requests.get(url, params=p, auth=(username, password))

print r.text
import requests
import intrinio
from auth import username, password

p = {'ticker':"AAPL",'statement':'income_statement','type':'QTR'}
auth = {}

url = "https://www.intrinio.com/api/fundamentals/standardized"
r = requests.get(url, params=p, auth=(username, password))

print r.text
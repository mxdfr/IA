# this function just simply searches the Albert Heijn site for a product and retuns the nutriscore of the first product that shows up.

import requests
from requests import get
from bs4 import BeautifulSoup

def get_nutriscore(productname):
  url = "https://www.ah.nl/zoeken?query=" + productname
  headers = {"Accept-Language": "en-US, en;q=0.5"}
  results = requests.get(url, headers=headers)
  soup = BeautifulSoup(results.text, "html.parser")

  searchResults = soup.find_all('div', class_='search-lane-wrapper')
  products = searchResults[0].find_all('article')
  nutritag = products[0].find_all('use')[0]
  print(nutritag.get('href'))

get_nutriscore('bread')
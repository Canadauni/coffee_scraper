import requests
from bs4 import BeautifulSoup
from peewee import *

database = SqliteDatabase('coffee_scraper.db', pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = database

class Roaster(BaseModel):
    roaster = CharField(unique=True)
    country = CharField()
    region = CharField()
    city = CharField()
class Coffee(BaseModel):
    coffee = CharField(unique=True)
    price = IntegerField()
    country = CharField()
    region = CharField()
    process = CharField()
    tasting_notes = TextField()
    roaster = ForeignKeyField(Roaster, backref='coffees')

def cash_int(price):
    price_float = float(price)
    return int(price_float * 100)

def matchstick_scrape():
    matchstick = Roaster.create(roaster='Matchstick',
                         country='Canada',
                         region='British Columbia',
                         city='Vancouver')
    print(matchstick.roaster)
    r = requests.get('https://matchstickyvr.com/collections/coffee/products.json')
    r_json = r.json()
    coffees = r_json['products']
    coffee_data = []
    for coffee in coffees:
        if coffee['product_type'] == '3 x 3/4 lb bags' or coffee['title'] in ['Catalogue','The Bulldog','Decaf']:
            continue
        else:
            name = coffee['title']
            country = coffee['product_type']
            price = cash_int(coffee['variants'][0]['price'])
            desc_html = BeautifulSoup(coffee['body_html'], 'html.parser')
            desc_dict = dict()
            items = desc_html.find_all('p')
            for i in range(len(items)):
                if i == 1:
                    continue
                attribs = items[i].find_all('strong')
                for attrib in attribs:
                    if attrib.nextSibling == None or attrib.nextSibling.string == None:
                        pairs = attrib.get_text().split(":")
                        desc_dict[pairs[0].strip()] = pairs[1].strip()
                    else:
                        desc_dict[attrib.get_text().strip().replace(':','')] = attrib.nextSibling.string.replace('\xa0', ' ').strip()
            coffee_store = { 'coffee':name,
                             'price':price,
                             'country':country,
                             'region':desc_dict['Region'],
                             'process':desc_dict['Process'],
                             'tasting_notes':desc_dict['Tasting Notes'],
                             'roaster':matchstick }
            coffee_data.append(coffee_store)
    Coffee.insert_many(coffee_data).execute()

database.create_tables([Roaster, Coffee])
print('created tables')
matchstick_scrape()
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

def check_matchstick(item):
    if item['product_type'] == '3 x 3/4 lb bags' or item['title'] in ['Catalogue','The Bulldog','Decaf']:
        return True
    else:
        return False

def get_matchstick():
    try:
        matchstick = Roaster.create(roaster = 'Matchstick',
                             country='Canada',
                             region='British Columbia',
                             city='Vancouver')
    except:
        print('already made matchstick')
        matchstick = Roaster.get(Roaster.roaster == 'Matchstick')
    finally:
        r = requests.get('https://matchstickyvr.com/collections/coffee/products.json')
        r_json = r.json()
        coffees = r_json['products']
        output = [coffee for coffee in coffees if not check_matchstick(coffee)]
        return matchstick, output

def check_bows(item):
    if 'Single Origin' not in item['tags']:
        return True
    else:
        return False

def get_bowsxarrows():
    try:
        bowsxarrows = Roaster.create(roaster = 'Bows & Arrows',
                                    country='Canada',
                                    region='British Columbia',
                                    city='Vancouver')
    except:
        print('already made bows')
        bowsxarrows = Roaster.get(Roaster.roaster == 'Bows & Arrows')
    finally:
        r = requests.get('https://bowsandarrows.com/collections/coffee/products.json')
        r_json = r.json()
        coffees = r_json['products']
        output = [coffee for coffee in coffees if not check_bows(coffee)]
        return bowsxarrows, output

def read_desc(desc):
    desc_html = BeautifulSoup(desc, 'html.parser')
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
    return desc_dict

def matchstick_scrape():
    matchstick, coffees = get_matchstick()
    coffee_data = []
    for coffee in coffees:
        name = coffee['title']
        country = coffee['product_type']
        price = cash_int(coffee['variants'][0]['price'])
        desc_dict = read_desc(coffee['body_html'])
        coffee_store = { 'coffee':name,
                         'price':price,
                         'country':country,
                         'region':desc_dict['Region'],
                         'process':desc_dict['Process'],
                         'tasting_notes':desc_dict['Tasting Notes'],
                         'roaster':matchstick }
        coffee_data.append(coffee_store)
    Coffee.insert_many(coffee_data).on_conflict('replace').execute()

# database.create_tables([Roaster, Coffee])
# print('created tables')
matchstick_scrape()

# get_matchstick()
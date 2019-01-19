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

def check_bows(item):
    if 'Single Origin' not in item['tags']:
        return True
    else:
        return False

def get_shopify(input, filter):
    try:
        roast_inst = Roaster.create(roaster = input['name'],
                                country = input['country'],
                                region = input['region'],
                                city = input['city'])
    except:
        print('coffee made')
        roast_inst = Roaster.get(Roaster.roaster == input['name'])
    finally:
        r = requests.get(input['url'])
        r_json = r.json()
        coffees = r_json['products']
        output = [coffee for coffee in coffees if not filter(coffee)]
        return roast_inst, output

def read_desc(desc):
    desc_html = BeautifulSoup(desc, 'html.parser')
    desc_dict = dict()
    items = desc_html.find_all('strong')
    for i in range(len(items)):
        if len(items[i].get_text().strip().split(":")[1]) > 0:
            pairs = items[i].get_text().split(":")
            desc_dict[pairs[0].strip()] = pairs[1].strip()
        else:
            desc_dict[items[i].get_text().strip().replace(':','')] = items[i].nextSibling.string.replace('\xa0', ' ').strip()
    return desc_dict


matchstick_dict = {
    'name': 'Matchstick',
    'country': 'Canada',
    'region': 'British Columbia',
    'city': 'Vancouver',
    'url': 'https://matchstickyvr.com/collections/coffee/products.json'
}

bowsxarrows_dict = {
    'name': 'Bows & Arrows',
    'country': 'Canada',
    'region': 'British Columbia',
    'city': 'Vancouver',
    'url': 'https://bowsandarrows.com/collections/coffee/products.json'
}

def matchstick_scrape():
    matchstick, coffees = get_shopify(matchstick_dict, check_matchstick)
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



database.create_tables([Roaster, Coffee])
print('created tables')
matchstick_scrape()

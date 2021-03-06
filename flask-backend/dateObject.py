import urllib.request, json, os, csv
from os.path import exists
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 
import pytz

from unidecode import unidecode 

# # # # # Helper Functions # # # # # 

# Creating a blank file.
def touch(path):
  with open(path, 'a'):
    os.utime(path, None)

### Initialize Flask ###
if not exists('./calendar.db'):
  touch('./calendar.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite+pysqlite:///calendar.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# # # # # Classes # # # # # 
# This class creates a python object with attributes that match the values of today's 
class DateObject:

  # Some quick variables to clean up what each attribute will be calling
  repcalData = 'https://repcal.info/now.json'
  rd = 'republican_date'
  a = 'attributes'
  
  # Makes the HTTP request to pull raw json data
  def getJsonData(self,api):
    with urllib.request.urlopen(api) as url:
      data = json.loads(url.read())
      return data

  # When a new date object is created it will self-populate accurate information from the json
  def __init__(self):

    # THIS EXISTS SO WE ONLY MAKE THE REQUEST ONCE 
    # Do not just call getJsonData() a half dozen times because it will take forever
    jsonData = self.getJsonData(self.repcalData)

    self.day = jsonData[self.rd][self.a]['day']
    self.weekday = jsonData[self.rd][self.a]['weekday'].strip("('").strip("'),")
    self.month = jsonData[self.rd][self.a]['month'].strip("('").strip("'),")
    self.yearArabic = jsonData[self.rd][self.a]['year_arabic']
    self.yearRoman = jsonData[self.rd][self.a]['year_roman'].strip("('").strip("'),")
    self.formatted = jsonData[self.rd]['formatted'].strip("('").strip("'),")

# Makes a collection of days that we can build into entries for the feed.
class Calendar(db.Model):
  __tablename__ = 'calendar'
  id = db.Column(db.Integer, primary_key= True)
  day = db.Column(db.Integer)
  week = db.Column(db.Integer)
  month = db.Column( db.String)
  month_of = db.Column(db.String)
  item = db.Column(db.String)
  item_url = db.Column(db.String)

# Makes a collection of days that we can build into entries for the feed.
class  Top10(db.Model):
  __tablename__ = 'top10'
  index = db.Column(db.Integer, primary_key=True)
  day = db.Column(db.Integer)
  week = db.Column(db.Integer)
  month = db.Column(db.String)
  month_of = db.Column(db.String)
  yearArabic = db.Column(db.Integer)
  yearRoman = db.Column(db.String)
  formatted = db.Column(db.String)
  item = db.Column(db.String)
  item_url = db.Column(db.String)
  image = db.Column(db.String)
  pub_date = db.Column(db.String)

db.create_all()


check = db.session.query(Calendar).filter_by(id = 1).first()
if check == None:
  with open('./static/full_calendar.csv','r') as file:
    data = csv.DictReader(file)
    for i in data:
      dateEntry = Calendar(
        id = i['id'].strip("'").strip("',"),
        day = i['day'].strip("'").strip("',"),
        week = i['week'].strip("'").strip("',"),
        month = i['month'].strip("'").strip("',"),
        month_of = i['month_of'].strip("'").strip("',"),
        item = i['item'].strip("'").strip("',"),
        item_url =i['item_url'].strip("'").strip("',"),
      )  
      db.session.add(dateEntry)
    db.session.commit()

def carpeDiem():
  today = DateObject()
  month = unidecode(today.month); day = today.day
  query = db.session.query(Calendar).filter_by(month = month, day = day).first()

  today.id = query.id
  today.week = query.week
  today.month_of = query.month_of
  today.item = query.item
  today.item_url = query.item_url
  today.image = today.item.lower().replace('the ','').replace(' ','_')
  today.pub_date = datetime.now(pytz.timezone('US/Eastern'))

  return today    

def addDayToTop10(today):

  dateEntry = Top10(
  index = 1,
  day = today.day,
  week = today.week,
  month = today.month,
  month_of = today.month_of,
  yearArabic = today.yearArabic,
  yearRoman = today.yearRoman,
  formatted = today.formatted,
  item = today.item,
  item_url = today.item_url,
  image = today.image,
  pub_date = today.pub_date
  )

  db.session.add(dateEntry)

  db.session.commit()

def upkeepTop10():

  last = db.session.query(Top10).filter_by(index=10).first()
  if not last == None:
    db.session.delete(last)

  for i in range (9,0, -1):
    row = db.session.query(Top10).filter_by(index=i).first()
    if not row == None:
      row.index += 1
  db.session.commit()
  



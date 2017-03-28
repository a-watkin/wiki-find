from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash

import geocoder
from urllib.request import urlparse, urlopen
from urllib.parse import urljoin
import json


db = SQLAlchemy()

class User(db.Model):
  __tablename__ = 'users'
  uid = db.Column(db.Integer, primary_key = True)
  firstname = db.Column(db.String(100))
  lastname = db.Column(db.String(100))
  email = db.Column(db.String(120), unique=True)
  pwdhash = db.Column(db.String(54))

  def __init__(self, firstname, lastname, email, password):
    self.firstname = firstname.title()
    self.lastname = lastname.title()
    self.email = email.lower()
    self.set_password(password)
     
  def set_password(self, password):
    self.pwdhash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)

# p = Place()
# places = p.query("1600 Amphitheater Parkway Mountain View CA")
class Place(object):
  def meters_to_walking_time(self, meters):
    # 80 meters is one minute walking time
    return int(meters / 80)  

  def wiki_path(self, slug):
    return urljoin("http://en.wikipedia.org/wiki/", slug.replace(' ', '_'))
  
  def address_to_latlng(self, address):
    g = geocoder.google(address)
    return (g.lat, g.lng)

  def query(self, address):
    lat, lng = self.address_to_latlng(address)
    
    # gsradius is the area 100-10000, currently set to 5,000 somehow i don't believe this is 5kms
    # changing the gsradius has no effect, probably because it's going by walking distance above
    # 
    # so here you have gsradius which doesn't really come into effect because it's so large
    # but more importantly gslimit=20, so it will at most return 20 wikipedia articles, and they're all closest to the location
    # specified, so to get more you have to increase this? yes that works
    query_url = 'https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gsradius=500&gscoord={0}%7C{1}&gslimit=200&format=json'.format(lat, lng)
    g = urlopen(query_url)

    # the decode part here changes the bytes to string
    results = g.read().decode()

    # TROUBLSHOOTING
    # json package complaining that the type is bytes and not string
    # print("THE RESULTS ARE", results, "THE TYPE IS: ", type(results))
    # and here's what we get, it is indeed a byte object:
    # 
    # THE RESULTS ARE 
    # 
    # b'{"batchcomplete":"","query":{"geosearch":[{"pageid":773423,"ns
    # ":0,"title":"Googleplex","lat":37.422,"lon":-122.084,"dist":53,"primary":""},{"p
    # ageid":3603126,"ns":0,"title":"Genetic Information Research Institute","lat":37.
    # 4193,"lon":-122.088,"dist":467.1,"primary":""},{"pageid":2185055,"ns":0,"title":
    # "Shoreline Park, Mountain View","lat":37.427,"lon":-122.08537,"dist":522.6,"prim
    # ary":""},{"pageid":33456998,"ns":0,"title":"Android lawn statues","lat":37.41829
    # ,"lon":-122.08782,"dist":545.4,"primary":""},{"pageid":2169786,"ns":0,"title":"B
    # ridge School Benefit","lat":37.426666666667,"lon":-122.08083333333,"dist":571.9,
    # "primary":""},{"pageid":2550861,"ns":0,"title":"Shoreline Amphitheatre","lat":37
    # .426778,"lon":-122.080733,"dist":587.1,"primary":""},{"pageid":2185097,"ns":0,"t
    # itle":"Rengstorff House","lat":37.431455555556,"lon":-122.0871,"dist":1038.8,"pr
    # imary":""},{"pageid":33169119,"ns":0,"title":"VirtualPBX","lat":37.4201,"lon":-1
    # 22.0728,"dist":1053.6,"primary":""},{"pageid":20682,"ns":0,"title":"MIPS Technol
    # ogies","lat":37.4201,"lon":-122.0728,"dist":1053.6,"primary":""},{"pageid":11154
    # 78,"ns":0,"title":"Computer History Museum","lat":37.414371,"lon":-122.076817,"d
    # ist":1112.2,"primary":""},{"pageid":1184796,"ns":0,"title":"Intuit","lat":37.427
    # 222222222,"lon":-122.09638888889,"dist":1189.7,"primary":""},{"pageid":25031378,
    # "ns":0,"title":"Permanente Creek","lat":37.433333333333,"lon":-122.08583333333,"
    # dist":1226.2,"primary":""},{"pageid":5401226,"ns":0,"title":"Kehillah Jewish Hig
    # h School","lat":37.4249,"lon":-122.1045,"dist":1798.6,"primary":""},{"pageid":47
    # 477,"ns":0,"title":"Ames Research Center","lat":37.415229,"lon":-122.06265,"dist
    # ":2077,"primary":""},{"pageid":21375850,"ns":0,"title":"Singularity University",
    # "lat":37.415229,"lon":-122.06265,"dist":2077,"primary":""},{"pageid":10037111,"n
    # s":0,"title":"Unitary Plan Wind Tunnel (Mountain View, California)","lat":37.416
    # 916666667,"lon":-122.060475,"dist":2196.7,"primary":""},{"pageid":43300351,"ns":
    # 0,"title":"Charleston Slough","lat":37.4418837,"lon":-122.0924628,"dist":2284.5,
    # "primary":""},{"pageid":6400136,"ns":0,"title":"Saint Athanasius Parish","lat":3
    # 7.4043196,"lon":-122.0968184,"dist":2287.5,"primary":""},{"pageid":38401640,"ns"
    # :0,"title":"NASA Ames Exploration Center","lat":37.408611111111,"lon":-122.06444
    # 444444,"dist":2332.5,"primary":""},{"pageid":48002602,"ns":0,"title":"Mayfield M
    # all","lat":37.409166666667,"lon":-122.10527777778,"dist":2357.7,"primary":""}]}}
    # 
    # ' THE TYPE IS:  <class 'bytes'>
    # 
    # so i'm guessing it won't just cleanly convert to a string? I mean that would be too easy wouldn't it?

    # Converting to a string worked ok, but it not fails for other reasons:
    # json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

    g.close()

    data = json.loads(results)
    
    places = []
    for place in data['query']['geosearch']:
      name = place['title']
      meters = place['dist']
      lat = place['lat']
      lng = place['lon']

      wiki_url = self.wiki_path(name)
      walking_time = self.meters_to_walking_time(meters)

      d = {
        'name': name,
        'url': wiki_url,
        'time': walking_time,
        'lat': lat,
        'lng': lng
      }

      places.append(d)

    return places


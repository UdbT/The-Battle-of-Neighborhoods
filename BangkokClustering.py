# To add a new cell, type '#%%'
# To add a new markdown cell, type '#%% [markdown]'

#%%
import requests # library to handle requests
import pandas as pd # library for data analsysis
import numpy as np # library to handle data in a vectorized manner
import random # library for random number generation
import re
from bs4 import BeautifulSoup # For scraping table from web 

# !conda install -c conda-forge geopy --yes 
from geopy.geocoders import Nominatim # module to convert an address into latitude and longitude values
# import geocoder
import geocoder

# libraries for displaying images
from IPython.display import Image 
from IPython.core.display import HTML 
    
# tranforming json file into a pandas dataframe library
from pandas.io.json import json_normalize

import matplotlib

# !conda install -c conda-forge folium=0.5.0 --yes
import folium # plotting library
import matplotlib.cm as cm # color mapper

print('Folium installed')
print('Libraries imported.')

#%% [markdown]
# **Get Bangkok coordinate**

#%%
address = "Bangkok, TH"

# initialize your variable to None
bk_coords = None

# loop until you get the coordinates
while(bk_coords is None):
  g = geocoder.arcgis(address)
  bk_coords = g.latlng

print(bk_coords)

#%% [markdown]
# <h1>Foursquare Authentication</h1>

#%%
CLIENT_ID = 'WD4ZCT2AXCER1SL3WPCVPJOC45434AGAPRLWMROEVRXDKDQQ' # your Foursquare ID
CLIENT_SECRET = '4NLO13KRPOWNET5DYDE5K2NFMC3UQCF52RVUQ2YX22XS5DGE' # your Foursquare Secret
VERSION = '20190909'
print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)

#%% [markdown]
# <h1>Scraping Bangkok district information from Wikipedia</h1>

#%%
website_url = requests.get('https://en.wikipedia.org/wiki/List_of_districts_of_Bangkok').text
soup = BeautifulSoup(website_url,'lxml')
w_table = soup.find('table',{'class':'wikitable sortable'})
list_contents = [re.split('\n+', rl.getText().strip()) for rl in w_table.findAll('tr')]
data = pd.DataFrame(list_contents)
columns = data.iloc[0]
data = data[1:]
data.columns = columns
data.loc[:,'Population'] = data.loc[:,'Population'].apply(lambda x: x.replace(',', ''))
data.head()
# print(soup.prettify())

#%% [markdown]
# <h2>Check if there is any missing coordinate and fill it up.</h2>

#%%
data.loc[data.loc[:,'Latitude'] == 'NA']


#%%
data.loc[1, 'Latitude'], data.loc[1, 'Longitude'] = '13.663889', '100.408889'
data.loc[20, 'Latitude'], data.loc[20, 'Longitude'] = '13.8192139', '100.640444'
data.loc[45, 'Latitude'], data.loc[45, 'Longitude'] = '13.788611', '100.334167'
data.loc[47, 'Latitude'], data.loc[47, 'Longitude'] = '13.611736', '100.509556'
data.loc[48, 'Latitude'], data.loc[48, 'Longitude'] = '13.764222', '100.605611'
data

#%% [markdown]
# <h2>Rename columns.</h2>

#%%
bk_districts = data.copy()
bk_districts.drop(['No. ofSubdistricts(Khwaeng)', 'Code'], axis=1, inplace=True)
bk_districts.columns = ['District', 'Thai', 'Population', 'Latitude', 'Longitude']
bk_districts.head()

#%% [markdown]
# <h2>Scraping area for each district from Wikipedia.</h2>

#%%
def get_area(name):
    district_url = requests.get('https://th.wikipedia.org/wiki/เขต'+name).text
    soup = BeautifulSoup(district_url,'lxml')
    s_table = soup.find('table',{'class':'wikitable'})
    return s_table.findAll('tr')[-1].getText().strip().split('\n')[1] # Total district area (km^2)
# get_area()

#%% [markdown]
# **Calculating density for each district**

#%%
bk_districts.loc[:,'Area'] = bk_districts.loc[:,'Thai'].apply(get_area)
bk_districts.loc[:,'Density'] = bk_districts.loc[:,'Population'].astype(float)/bk_districts.loc[:,'Area'].astype(float)
bk_districts = bk_districts[['District', 'Thai', 'Population', 'Area', 'Density', 'Latitude', 'Longitude']]
bk_districts.head()


#%%
# bk_districts
matplotlib.cm.cmap_d.keys()

#%% [markdown]
# <h1>Visualizing Bangkok map</h1>

#%%
# Map color
pop_re = bk_districts['Population'].astype(float)/1000
minima = min(pop_re)
maxima = max(pop_re)
norm = matplotlib.colors.Normalize(vmin=minima, vmax=maxima, clip=True)
mapper = cm.ScalarMappable(norm=norm, cmap=cm.RdYlBu)

# create map of Bangkok using latitude and longitude values
map_bangkok = folium.Map(location=[bk_coords[0], bk_coords[1]], zoom_start=10, tiles='Stamen Toner')

# add markers to map
for lat, lng, district, area, density, pop in zip(bk_districts['Latitude'].astype(float)
                            ,bk_districts['Longitude'].astype(float)
                            ,bk_districts['District']
                            ,bk_districts['Area'].astype(float)/2
                            ,bk_districts['Density'].astype(float)/1000
                            ,pop_re
                            ):
    label = '{}'.format(district)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=density,
        popup=label,
        color='blue',
        weight=0.5,
        fill=True,
        fill_color=matplotlib.colors.to_hex(mapper.to_rgba(pop)[:-1]),
        fill_opacity=0.9,
        parse_html=False).add_to(map_bangkok)
map_bangkok


#%%
name = 'Watthana'
lat = 13.742222
lng = 100.585833
radius = 2000
limit = 9999
venues_list=[]
# create the API request URL
url = 'https://api.foursquare.com/v2/venues/search?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    lat, 
    lng, 
    radius, 
    limit)

try:
#     make the GET request
    results = requests.get(url).json()["response"]['venues']
except:
    print("--- Failed to extract items ---")

for v in results:
    tmp = [name, lat, lng, v['name'], v['location']['lat'], v['location']['lng']]
    try:
        tmp.append(v['categories'][0]['name'])
    except:
        tmp.append(None)
        
    venues_list.append(tmp)
    
# venues_list.append([(
#             name, 
#             lat, 
#             lng, 
#             v['name'], 
#             v['location']['lat'], 
#             v['location']['lng'],  
#             v['categories']) for v in results])
venues_list


#%%
def getNearbyVenues(names, latitudes, longitudes):
    REDIUS = 2000
    LIMIT = 9999
    non_cat = 0 # Non-categorize venues count
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name, lat, lng)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/search?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            REDIUS, 
            LIMIT)
        
        try:
            # make the GET request
            results = requests.get(url).json()["response"]['venues']
        except:
            print("--- Failed to extract items ---")
            continue
        
        # return only relevant information for each nearby venue
        for v in results:
            tmp = [name, lat, lng, v['name'], v['location']['lat'], v['location']['lng']]
            try:
                tmp.append(v['categories'][0]['name'])
            except:
                non_cat = non_cat + 1
                continue

            venues_list.append(tmp)
            
    nearby_venues = pd.DataFrame([item for item in venues_list])
    nearby_venues.columns = ['District', 
                  'Latitude', 
                  'Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    print(non_cat)
    return(nearby_venues)


#%%
bangkok_venues = getNearbyVenues(bk_districts['District'], bk_districts['Latitude'], bk_districts['Longitude'])


#%%
len(bangkok_venues['Venue Category'].unique())


#%%
bangkok_onehot = pd.get_dummies(bangkok_venues[['Venue Category']], prefix="", prefix_sep="")
bangkok_onehot['District'] = bangkok_venues['District']
fixed_columns = [bangkok_onehot.columns[-1]] + list(bangkok_onehot.columns[:-1])
bangkok_onehot = bangkok_onehot[fixed_columns]
bangkok_onehot


#%%
bangkok_onehot.groupby('District').mean()


#%%



#%%




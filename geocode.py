import geocoder as gc
import json
import os
from tqdm import tqdm
import logging
from datetime import datetime

def uniq_stops(route_file=os.path.join('data', 'trol_routes.json')):
    with open(route_file) as readfile:
        routes = json.load(readfile)
    stops = []
    for route in tqdm(routes,desc="Выделение уникальных остановок"):
        for direction in routes[route]:
            for stop in routes[route][direction]:
                if stop not in stops:
                    stops.append(stop)
    return stops

def filter_geocoded(stops, geofilepath=os.path.join('data',datetime.now().strftime("%Y_%m_&d_")+'stops_geocoded.json')):
    with open(geofilepath) as oldfile:
        geodata=json.load(oldfile)
    for item in geodata:
        if item['stop_name'] in stops:
            stops.remove(item['stop_name'])
    return stops        
    
def try_geocode(stops):
    geo_stops = []
    for stop in tqdm(stops, desc="Геокодинг остановок"):
        try:
            resp = gc.yandex('Москва, остановка ' + stop)
            if resp.ok:
                geo_stops.append({"stop_name":stop, 'lat':resp.lat, 'lng': resp.lng})
                stops.remove(stop)
        except KeyboardInterrupt:
            with open(os.path.join('data',datetime.now().strftime("%Y_%m_&d_")+'stops_geocoded.json'), "w") as geofile:
                json.dump(geo_stops, geofile, ensure_ascii=False)
            raise
        except:
            logging.error('Could not geocode %s' % stop )
    return stops, geo_stops
         
def enrich(geo_stops=[], route_file='trol_routes.json'):
    with open(os.path.join('data',route_file)) as readfile:
        routedata = json.load(readfile)
    for route in routedata:
        for direction in route:
            for stop in direction:
                stop = (item for item in geo_stops if item["stop_name"] == stop).next()
    with open(os.path.join('data', 'latlng_'+ route_file), 'w') as enriched:
        json.dump(routedata, enriched, ensure_ascii=False)
    
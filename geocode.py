import geocoder as gc
import json
import os
from tqdm import tqdm

def geocode_routes(route_file=os.path.join('data', 'trol_routes.json')):
    with open(route_file) as readfile:
        routes = json.load(readfile)
    for route in tqdm(routes,desc="Маршруты"):
        for direction in routes[route]:
            for stop in routes[route][direction]:
                resp = gc.yandex("остановка " + stop)
                stop = {'stop_name':stop, 'lat': resp.lat, 'lng': resp.lng}
    with open('new_'+route_file) as writefile:
        json.dump(routes, writefile, ensure_ascii=False)
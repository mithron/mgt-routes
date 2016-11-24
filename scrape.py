import requests
from tqdm import tqdm, trange
import os, sys, logging
import argparse
import json
from datetime import datetime
#from urllib.parse import urlencode


from bs4 import BeautifulSoup as bs

parser = "lxml"


transports = ["avto", "trol", "tram"]
directions = ["AB", "BA"]



def get_nums(trans="avto"):
    if trans=="avto" or trans=="tram" or trans=="trol" :
        resp = requests.get("http://mosgortrans.org/pass3/request.ajax.php?list=ways&type=" + trans)
        return resp.text.split("\n")
        
def get_stops(trans="avto",num="31",dow='1111100',direction="AB"):
    # Expert: source encoding: win1251 displayed as: utf8  postfilter: urlencoded
    data = {'type': trans, 'way': str(num).encode('cp1251'), 'date': dow, 'direction':direction}
    resp = requests.get("http://mosgortrans.org/pass3/request.ajax.php?list=waypoints&",params=data)
    return resp.text.split('\n')[:-1]
    
def get_dows(trans="avto",num="31"):
     # Expert: source encoding: win1251 displayed as: utf8  postfilter: urlencoded
    data = {'type': trans, 'way': str(num).encode('cp1251')}
    resp = requests.get("http://mosgortrans.org/pass3/request.ajax.php?list=days&", params=data)
    return resp.text.split('\n')[:-1]
    
def get_stop_name(body):
    pass
    

def get_rasp(trans="avto", num="31", dow='1111100', direction='BA', stop = "0"):
     # Expert: source encoding: win1251 displayed as: utf8  postfilter: urlencoded
    data = {'type': trans, 'way': str(num).encode('cp1251'), 'date': dow, 'direction':direction, 'waypoint':str(stop)}
    resp = requests.get("http://mosgortrans.org/pass3/shedule.php?", params=data)
    body = bs(resp.text, parser)
    
    try:
        tables = body.findAll("table", attrs = {"border":"0", "cellspacing":"0", "cellpadding":"0"})
    except:
        logging.error("No data found for %s %s %s %s %s" % (trans, str(num), dow, direction, str(stop)))
        return False, False
    
    if len(tables) != 2:
        logging.error("Partial data found for %s %s %s %s %s" % (trans, str(num), dow, direction, str(stop)))
        logging.error("table len is %s" % str(len(tables)))
        logging.error(resp.url)
        return False, False
   
    try:
        best_from = tables[0].findAll("h3")[2].text
    except:
        logging.warn("No start date found for %s %s %s %s %s, using now" % (trans, str(num), dow, direction, str(stop)))
        best_from = datetime.now().date().strftime("%d %B %Y")
   
    try:
        name = body.select('table > tr:nth-of-type(2) > td > h2')[0].text
    except:
        logging.warn("No name found for %s %s %s %s %s, using number" % (trans, str(num), dow, direction, str(stop)))
        name = str(stop)
    
    times = {}
    
    try:
        for tr in iter([row for row in tables[1].children if row != '\n']):
            it = iter([row for row in tr.children if row != '\n'])
            for td in it:
                hour = td.find("span", attrs = {"class": "hour"})
                if hour:
                    hour = hour.text
                    td2 = next(it,None)
                    minutes = [span.text for span in td2.findAll("span", attrs = {"class":"minutes"})]
                    if minutes:
                        times[hour]=minutes
    except:
        logging.error("Error parsing data for %s %s %s %s %s" % (trans, str(num), dow, direction, str(stop)))
        
        
    return best_from, name, times

def resume():
    for trans in tqdm(transports, desc="Transport Types"):
        points_dict = {}
        for num in tqdm(get_nums(trans), desc="Numbers", position=1):
            try:
                fname = os.path.join("data",'rasp',trans+'_'+num+'.json')
                if os.path.isfile(fname):
                    with open(fname, 'r+') as rasp_file:
                        full_rasp = json.load(rasp_file)
                        for dow in tqdm(get_dows(trans, str(num)), desc="Days of week", position=2):
                            for direction in tqdm(directions, desc="Directions", position=3):
                                points = get_stops(trans, str(num), dow, direction)
                                if num in points_dict:
                                    points_dict[num][direction] = points 
                                else:
                                    points_dict[num]={ direction:points }
                                for stop in trange(len(points), desc="Stops", position=4):
                                    (best_from, stop_name, rasp) = get_rasp(trans, num, dow, direction, str(stop))
                                    if (full_rasp[direction][stop]['best_from'] != best_from) or (full_rasp[direction][stop]['name'] != stop_name):
                                        full_rasp[direction][stop]['best_from'] = best_from
                                        full_rasp[direction][stop]['name'] = stop_name
                                        full_rasp[direction][stop] = rasp 
                        json.dump(full_rasp, rasp_file, ensure_ascii=False)                                    
                            
                else:
                    full_rasp = {}
                    for dow in tqdm(get_dows(trans, str(num)), desc="Days of week", position=2):
                        for direction in tqdm(directions, desc="Directions", position=3):
                            full_rasp[direction] = {}
                            points = get_stops(trans, str(num), dow, direction)
                            if num in points_dict:
                                points_dict[num][direction] = points 
                            else:
                                points_dict[num]={ direction:points }
                            for stop in trange(len(points), desc="Stops", position=4):
                                (best_from, stop_name, rasp) = get_rasp(trans, num, dow, direction, str(stop))
                                full_rasp[direction][stop] = rasp 
                                full_rasp[direction][stop]['best_from'] = best_from
                                full_rasp[direction][stop]['name'] = stop_name
                    with open(os.path.join("data","rasp", trans+"_"+num+".json"), "w") as rasp_file:
                        json.dump(full_rasp, rasp_file, ensure_ascii=False)
            except KeyboardInterrupt:
                with open(os.path.join("data","rasp", trans+"_"+num+".json"), "w") as rasp_file:
                    json.dump(full_rasp, rasp_file, ensure_ascii=False)
                with open(os.path.join("data",trans+"_routes.json"), "w") as routes_map:
                    json.dump(points_dict,routes_map, ensure_ascii=False)
                raise
        with open(os.path.join("data",trans+"_routes.json"), "w") as routes_map:
            json.dump(points_dict,routes_map, ensure_ascii=False)
            
def initial():
    for trans in tqdm(transports, desc="Transport Types"):
        points_dict = {}
        for num in tqdm(get_nums(trans), desc="Numbers", position=1):
            try:
                full_rasp = {}
                for dow in tqdm(get_dows(trans, str(num)), desc="Days of week", position=2):
                    for direction in tqdm(directions, desc="Directions", position=3):
                        full_rasp[direction] = {}
                        points = get_stops(trans, str(num), dow, direction)
                        if num in points_dict:
                            points_dict[num][direction] = points 
                        else:
                            points_dict[num]={ direction:points }
                        for stop in trange(len(points), desc="Stops", position=4):
                            (best_from, stop_name, rasp) = get_rasp(trans, num, dow, direction, str(stop))
                            full_rasp[direction][stop] = rasp 
                            full_rasp[direction][stop]['best_from'] = best_from
                            full_rasp[direction][stop]['name'] = stop_name
                with open(os.path.join("data","rasp", trans+"_"+num+".json"), "w") as rasp_file:
                    json.dump(full_rasp, rasp_file, ensure_ascii=False)
            except KeyboardInterrupt:
                with open(os.path.join("data","rasp", trans+"_"+num+".json"), "w") as rasp_file:
                    json.dump(full_rasp, rasp_file, ensure_ascii=False)
                with open(os.path.join("data",trans+"_routes.json"), "w") as routes_map:
                    json.dump(points_dict,routes_map, ensure_ascii=False)
                raise
        with open(os.path.join("data",trans+"_routes.json"), "w") as routes_map:
            json.dump(points_dict,routes_map, ensure_ascii=False)

   
def main():
    
    if os.path.isdir('data') and os.path.isdir(os.path.join('data', 'rasp')):
        resume()
    else:
        try:
            os.mkdir('data')
            os.mkdir(os.path.join('data', 'rasp'))
        except:
            pass
        initial() 
   
        

    
import requests
from tqdm import tqdm, trange
import os, sys, logging
import argparse
import json
from datetime import datetime
from bs4 import BeautifulSoup as bs
import grequests

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
    return body.select('table > tr:nth-of-type(2) > td > h2')[0].text
    
def get_tables(body):
    tables = body.findAll("table", attrs = {"border":"0", "cellspacing":"0", "cellpadding":"0"})
    if len(tables) != 2:
        return []
    return tables

def get_date(table):
    return table.findAll("h3")[2].text
    
def get_timetable(table):
    times = {}
    for tr in iter([row for row in table.children if row != '\n']):
        it = iter([row for row in tr.children if row != '\n'])
        for td in it:
            hour = td.find("span", attrs = {"class": "hour"})
            if hour:
                hour = hour.text
                td2 = next(it,None)
                minutes = [span.text for span in td2.findAll("span", attrs = {"class":"minutes"})]
                if minutes:
                    times[hour]=minutes
    return times

def process_resp(resp):
    body = bs(resp.text, parser)
    
    tables = get_tables(body)
    if tables:
        times = get_timetable(tables[1])
    else:
        print('No tables found')
        times = {}
    
    try:
        name = get_stop_name(body)
    except:
        name=None
    
    try:
        best_from = get_date(tables[0])
    except:
        best_from = datetime.now().date().strftime("%d %B %Y")
        
    return best_from, name, times
    
def get_rasp(trans="avto", num="31", dow='1111100', direction='BA', stop = "0"):
    
    resp = get_rasp_html(trans=trans, num=num, dow=dow, direction=direction, stop = stop)
    
    try:
        best_from, name, times = process_resp(resp)
    except:
        logging.error("Error parsing data for %s %s %s %s %s" % (trans, str(num), dow, direction, str(stop)))
    
    if not name:
        name = str(stop)
        
    return best_from, name, times
    
    

def get_rasp_html(trans="avto", num="31", dow='1111100', direction='BA', stop = "0"):
     
    data = {'type': trans, 'way': str(num).encode('cp1251'), 'date': dow, 'direction':direction, 'waypoint':str(stop)}
    resp = requests.get("http://mosgortrans.org/pass3/shedule.php?", params=data)
    return resp


def upd_dict(data, newdata):
    data.update(newdata)
    return data

def get_rasps(trans="avto", num="31", dow='1111100', direction='BA', stops = 1):
    data = {'type': trans, 'way': str(num).encode('cp1251'), 'date': dow, 'direction':direction }
    rs = (grequests.get("http://mosgortrans.org/pass3/shedule.php?",
        #callback = process_resp,
        params = upd_dict(data, {'waypoint':str(stop)})) for stop in range(stops))
    return grequests.map(rs, size=30)
    

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
                        for stop, resp in enumerate(get_rasps(trans, num, dow, direction,len(points))):
                            if resp:
                                (best_from, stop_name, rasp) = process_resp(resp)
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
        initial()
    else:
        try:
            os.mkdir('data')
            os.mkdir(os.path.join('data', 'rasp'))
        except:
            pass
        initial() 
   
        

    
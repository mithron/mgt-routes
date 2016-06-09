import requests
from tqdm import tqdm, trange
import os, sys, logging
import argparse
import json
from datetime import datetime

from bs4 import BeautifulSoup as bs
parser = "lxml"


def get_nums(trans="avto"):
    if trans=="avto" or trans=="tram" or trans=="trol" :
        resp = requests.get("http://mosgortrans.org/pass3/request.ajax.php?list=ways&type=" + trans)
        return resp.text.split("\n")
        
def get_stops(trans="avto",num="0",dow='1111100',direction="AB"):
    resp = requests.get("http://mosgortrans.org/pass3/request.ajax.php?list=waypoints&type="+trans+'&way='+str(num)+
                            '&date='+dow+'&direction='+direction)
    return resp.text.split('\n')[:-1]
    
def get_dows(trans="avto",num="0"):
    resp = requests.get("http://mosgortrans.org/pass3/request.ajax.php?list=days&type="+trans+"&way="+str(num))
    return resp.text.split('\n')[:-1]
    
def get_rasp(trans="avto", num="0", dow='1111100', direction='BA', stop = "0"):
    resp = requests.get("http://mosgortrans.org/pass3/shedule.php?type="+trans+"&way="+str(num)+"&date="+dow+"&direction="+direction+"&waypoint="+str(stop))
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
        
        
    return best_from, times
   
def main():
    transports = ["avto", "trol", "tram"]
    directions = ["AB", "BA"]
    
    for trans in tqdm(transports, desc="Transport Types"):
        points_dict = {}
        for num in tqdm(get_nums(trans), desc="Numbers", position=1):
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
                        (best_from, rasp) = get_rasp(trans, num, dow, direction, str(stop))
                        full_rasp[direction][stop] = rasp 
            with open("data/rasp/"+trans+"_"+num+".json", "w") as rasp_file:
                rasp_file.write(json.dumps(full_rasp))                    
        with open("data/"+trans+"_routes.json", "w") as routes_map:
            routes_map.write(json.dumps(points_dict))
        

    
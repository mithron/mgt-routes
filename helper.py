import json
import os, logging

def join_rasps(path = os.path.join('data', 'rasp')):
    for (dirpath, dirnames, filenames) in os.walk(path):
        with open(os.path.join('all_rasps.json'), 'w') as save_file:
            allrasps = []
            for fname in [file for file in filenames if 'json' in file and os.path.isfile(os.path.join(path,file))]:
                with open(os.path.join(path,fname), 'r') as rasp_file:
                    try:
                        data = json.load(rasp_file)
                    except Exception as exc:
                        print(fname)
                allrasps.append(data)
            json.dump(allrasps, save_file, ensure_ascii=False)        

def convert_urlencoded(fname):
    with open(fname, 'r') as convfile:
        data = json.load(convfile)
    with open(fname, 'w') as convfile:
        json.dump(data, convfile, ensure_ascii=False)
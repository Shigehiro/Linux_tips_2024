#!/usr/bin/env python3

"""
Sample API of Arkime (https://arkime.com/)
See https://arkime.com/apiv3#connectionscsv-api

Usage:
$ ./arkime_api_sample.py -u admin -p password -i 192.168.100.10
"""

import argparse
import requests
import json
from requests.auth import HTTPDigestAuth

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", type=str, required=True, help="Specify username")
parser.add_argument("-p", "--password", type=str, required=True, help="Specify credentials")
parser.add_argument("-i", "--ip", type=str, required=True, help="Specify IP address")
args = parser.parse_args()
arkime_user = args.user
arkime_password = args.password
arkime_ip = args.ip

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
arkime_port = '8005'

# sessions
res = requests.get(url=f"http://{arkime_ip}:{arkime_port}/api/sessions?length=5", headers=headers, auth=HTTPDigestAuth(arkime_user, arkime_password))
#res = requests.get(url=f"http://{arkime_ip}:{arkime_port}/api/sessions?length=5&fields=destination.port,destination.ip", headers=headers, auth=HTTPDigestAuth(arkime_user, arkime_password))
res_json = json.loads(res.content.decode('utf-8'))
#print(json.dumps(res_json))
for i in res_json['data']:
    #if 'dns' in i.keys() and i['destination']['port'] == 53 and i['destination']['ip'] == '10.2.0.10':
    if 'dns' in i.keys() and i['destination']['port'] == 53:
        print(i['dns']['host'])

# connections
res = requests.get(url=f"http://{arkime_ip}:{arkime_port}/api/connections", headers=headers, auth=HTTPDigestAuth(arkime_user, arkime_password))
res_json = json.loads(res.content.decode('utf-8'))
#print(json.dumps(res_json, indent=2))
#print(json.dumps(res_json))


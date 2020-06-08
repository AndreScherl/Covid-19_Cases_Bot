#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

cases_and_recipients = {}

# Request the RKI data for one Landkreis. Return case data of Landkreis.
def get_rki_cases(landkreis):
    url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query'
    
    params = dict (
        where='GEN LIKE \'%' + landkreis + '%\'',
        outFields='GEN,cases,deaths,last_update',
        returnGeometry='false',
        outSR='4326',
        f='json'
    )

    resp = requests.get(url, params)
    data = resp.json()['features'][0]['attributes']
    return data

# Request to search for name in Landkreise database. Retrun array of results.
def get_rki_landkreise(name, exact=False):
    url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query'
    
    if exact:
        params = dict (
            where='GEN LIKE \'' + name + '\'',
            outFields='GEN',
            returnGeometry='false',
            outSR='4326',
            f='json'
        )
    else:
        params = dict (
        where='GEN LIKE \'%' + name + '%\'',
        outFields='GEN',
        returnGeometry='false',
        outSR='4326',
        f='json'
    )

    resp = requests.get(url, params)
    return resp.json()['features']

def add_entry(lk, chatid):
    cases = get_rki_cases(lk)
    if lk in cases_and_recipients:
        if chatid not in cases_and_recipients[lk]['recipients']:
            cases_and_recipients[lk]['recipients'].append(chatid)
    else:
        newlk = {
            'cases': cases['cases'],
            'deaths': cases['deaths'],
            'last_update': cases['last_update'],
            'recipients': [chatid]
        }
        cases_and_recipients[lk] = newlk
    save_data()

def remove_entry(lk, chatid):
    if len(cases_and_recipients[lk]['recipients']) > 1:
        cases_and_recipients[lk]['recipients'].remove(chatid)
    else:
        cases_and_recipients.pop(lk)
    save_data()

def lks_of_user(chatid):
    userslks = []
    for key, value in cases_and_recipients.items():
        if chatid in value['recipients']:
            userslks.append(key)
    return userslks

def info_for_landkreis(lk):
    lkdaten = cases_and_recipients[lk]
    infotext = "*" + lk + "* \n"
    infotext += str(lkdaten['cases']) + " Fälle, "
    infotext += str(lkdaten['deaths']) + " Tote \n"
    infotext += "(" + lkdaten['last_update'] + ")"
    return infotext

def update_landkreise():
    updatedlks = []
    for key, value in cases_and_recipients.items():
        newdata = get_rki_cases(key)
        if (newdata['cases'] != value['cases']) or (newdata['deaths'] != value['deaths']):
            newdata['recipients'] = cases_and_recipients[key]['recipients']
            cases_and_recipients[key] = newdata
            updatedlks.append(key)
    save_data()
    return updatedlks

# Write data to file.
def save_data():
    jsondata = json.dumps(cases_and_recipients)
    f = open("data.json","w")
    f.write(jsondata)
    f.close()

# Read data from file.
def load_data():
    global cases_and_recipients
    with open("data.json") as datafile:
       cases_and_recipients = json.load(datafile)
#!/usr/bin/env python3

''' Gets Google Calendar's account events and prints them to stdout '''

import getopt
from urllib.parse import urlencode
import httplib2
import datetime
from dateutil.relativedelta import *
import xml.etree.ElementTree as etree
from operator import itemgetter
"""
From: https://github.com/tpopela/google_calendar_fetcher
For Python3

google\_calendar\_fetcher
=======================

Google Calendar fetcher written in Python 3. Prints events on stdout.

Usage
-----

`$cat credentials`
`username password`

`$./google_calendar_fetcher.py --filename credentials`

`Today is 04.08.2012, odd week - Dominik`
`In  6 days  10.08.2012       Event1`
`In  7 days  11.08.2012       Event2`
`In  8 days  12.08.2012       Event3`
`In 18 days  22.08.2012       Event4`
`In 19 days  23.08.2012       Event5`
"""

__events__ = {}


def login(username, password):
    ''' Logins to Google Account '''

    values = {'accountType': 'GOOGLE',
              'Email': username,
              'Passwd': password,
              'source': 'google_calendar_fetcher',
              'service': 'cl'}

    url_login = 'https://www.google.com/accounts/ClientLogin'

    response, content = httplib2.Http().request(url_login,
        'POST',
        urlencode(values),
        headers={'Content-Type': 'application/x-www-form-urlencoded'})

    if response.status == 403:
        print('Bad username or password')

    assert response.status == 200,\
        "Can't log in (network error?)"

    reply = content.decode().split('\n')
    token = reply[2].split('=')[1]

    return token


def get_calendars(token):
    ''' Gets calendars list '''

    token_header = "GoogleLogin auth=" + str(token)
    url_calendars = 'https://www.google.com/calendar'
    url_calendars += '/feeds/default/allcalendars/full'

    response, content = httplib2.Http().request(url_calendars,
        headers={'Authorization': token_header})

    assert response.status == 200,\
        "Can't get calendars list (network error?)"

    parse_calendars(content, token_header)

    return content


def parse_calendars(xml_calendars, token_header):
    ''' Parses calendars list '''

    tree = etree.XML(xml_calendars)
    calendars = tree.findall('{http://www.w3.org/2005/Atom}entry')
    for calendar in calendars:
        calendar_content = calendar.find('{http://www.w3.org/2005/Atom}content')
        calendar_id = calendar_content.get('src')
        get_calendar_entries(calendar_id, token_header)


def get_calendar_entries(calendar_id, token_header):
    ''' Get entries (until one month) from calendar '''

    now = datetime.date.today()
    now_plus_month = now + relativedelta(months=+1)
    values = {'start-min': now.strftime("%Y-%m-%d") + "T00:00:00",
              'start-max': now_plus_month.strftime("%Y-%m-%d") + "T23:59:59"}

    url = "%s?%s" % (calendar_id, urlencode(values))

    response, content = httplib2.Http().request(url,
        headers={'Authorization': token_header, 'cache-control': 'no-cache'})

    assert response.status == 200,\
        "Can't get entries from calendar (network error?)"

    parse_events(content)


def parse_events(raw_xml):
    ''' Parses events '''

    tree = etree.XML(raw_xml)
    entries = tree.findall('{http://www.w3.org/2005/Atom}entry')
    for entry in entries:
        title = entry.find('{http://www.w3.org/2005/Atom}title')
        when = entry.find('{http://schemas.google.com/g/2005}when')
        if title.text is None:
            __events__['No subject'] = when.get('startTime')
        else:
            __events__[title.text] = when.get('startTime')


def get_name_day():
    ''' Gets name day '''
    url_name_day = 'http://svatky.adresa.info/txt'
    response, content = httplib2.Http().request(url_name_day)

    assert response.status == 200,\
        "Can't get name day (network error?)"

    if content.decode() == "":
        return ""

    temp_name_day = content.decode().split(";")
    name_day = temp_name_day[1].split("\n")

    return " - " + name_day[0]


def print_header():
    ''' Prints header to stdout '''

    now = datetime.datetime.now()
    output = ""

    output = "Today is " + now.strftime("%d.%m.%Y") + ", "
    if (int(now.strftime("%W"))) % 2 == 0:
        output += "even week"
    else:
        output += "odd week"

    output += get_name_day()

    print(output)


def print_output():
    ''' Prints events to stdout '''

    print_header()

    output_line = ""

    now = datetime.datetime.now()

    events_sorted = sorted(__events__.items(), key=itemgetter(1))

#    for key, value in events_sorted:
#       print(key + " " + value)

    for key, value in events_sorted:

        if len(value) == 10:
            event_start_time = datetime.datetime.strptime(value, "%Y-%m-%d")
            time = False
        else:
            date_time = value.split('.')
            event_start_time = datetime.datetime.strptime(date_time[0],
                                                          "%Y-%m-%dT%H:%M:%S")
            time = True

        delta = event_start_time - now
        if (delta.seconds < 0):
            continue

        print(key + " " + value + " " + str(delta.seconds) + " " + str(delta) + "            " + str(delta.seconds // 3600))

        if (time is True and (delta.days == 0 or delta.days == -1)):
            if (delta.days >= 0):
                diff = delta.seconds // 3600
                if (now.day == event_start_time.day):
                    if (diff == 0):
                        output_line += "Now         "
                    elif (diff == 1):
                        output_line += "In  1 hour  "
                    else:
                        if (diff < 10):
                            output_line += "In  " + str(diff) + " hours "
                        else:
                            output_line += "In " + str(diff) + " hours "
                else:
                    output_line += "Tomorrow    "
            else:
                continue
        else:
            if (delta.days < 0):
                output_line += "Today       "
            elif (delta.days == 0):
                output_line += "Tomorrow    "
            else:
                if (delta.days > 8):
                    output_line += "In "
                else:
                    output_line += "In  "
                output_line += str(delta.days + 1) + " days  "

        if (time is True):
            output_line += event_start_time.strftime("%d.%m.%Y %H:%M ")
        else:
            if (delta.days <= -1):
                output_line += now.strftime("%d.%m.%Y       ")
            else:
                output_line += event_start_time.strftime("%d.%m.%Y       ")

        output_line += key

        if (output_line != ""):
            print(output_line)

        output_line = ""
        time = False


def main(username, password):
    ''' Entry point '''

    token = login(username, password)
    get_calendars(token)
    print_output()

if __name__ == '__main__':
    import sys

    try:
        opts, args = getopt.getopt(sys.argv[1:], "f", ["filename="])
    except getopt.GetoptError as err:
        print("Only argument is -f or --filename followed by name of file "
                "that contains your Google username and password "
                "on one line separated by space!")
        sys.exit(2)

    # TODO; get the username and password from somewhere secret.
    # TODO; setup MooreWorksTest, t3st.ts3t, email account?
    username = "MooreWorksService"
    password = "s3rvic3.M3"
    #username = None
    #password = None

    for option, argument in opts:
        if option in ("-f", "--filename"):
            try:
                with open(argument, mode='r', encoding='utf-8') as credentials:
                    username, password = credentials.read().split()
            except IOError:
                print("File not found!")
                sys.exit(2)

    main(username, password)

    sys.exit()

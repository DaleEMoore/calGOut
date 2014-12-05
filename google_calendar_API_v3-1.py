# From https://raw.githubusercontent.com/insanum/gcalcli/master/gcalcli
# I'm going to butcher this to do what I want!
#!/usr/bin/env python

# ** The MIT License **
#
# Copyright (c) 2007 Eric Davis (aka Insanum)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Dude... just buy us a beer. :-)
#

# XXX Todo/Cleanup XXX
# threading is currently broken when getting event list
# if threading works then move pageToken processing from GetAllEvents to thread
# support different types of reminders plus multiple ones (popup, sms, email)
# add caching, should be easy (dump all calendar JSON data to file)
# add support for multiline description input in the 'add' and 'edit' commands
# maybe add support for freebusy ?

#############################################################################
#                                                                           #
#                                      (           (     (                  #
#               (         (     (      )\ )   (    )\ )  )\ )               #
#               )\ )      )\    )\    (()/(   )\  (()/( (()/(               #
#              (()/(    (((_)((((_)(   /(_))(((_)  /(_)) /(_))              #
#               /(_))_  )\___ )\ _ )\ (_))  )\___ (_))  (_))                #
#              (_)) __|((/ __|(_)_\(_)| |  ((/ __|| |   |_ _|               #
#                | (_ | | (__  / _ \  | |__ | (__ | |__  | |                #
#                 \___|  \___|/_/ \_\ |____| \___||____||___|               #
#                                                                           #
# Author: Eric Davis <http://www.insanum.com>                               #
#         Brian Hartvigsen <http://github.com/tresni>                       #
# Home: https://github.com/insanum/gcalcli                                  #
#                                                                           #
# Requirements:                                                             #
#  - Python 2                                                               #
#        http://www.python.org                                              #
#  - Google APIs Client Library for Python 2                                #
#        https://developers.google.com/api-client-library/python            #
#  - dateutil Python 2 module                                               #
#        http://www.labix.org/python-dateutil                               #
#                                                                           #
# Optional:                                                                 #
#  - vobject Python module (needed for importing ics/vcal files)            #
#        http://vobject.skyhouseconsulting.com                              #
#  - parsedatetime Python module (needed for fuzzy date parsing)            #
#        https://github.com/bear/parsedatetime                              #
#                                                                           #
# Everything you need to know (Google API Calendar v3): http://goo.gl/HfTGQ #
#                                                                           #
#############################################################################

__program__         = 'gcalcli'
__version__         = 'v4.1'
#__version__         = 'v3.1'
__author__          = 'Dale E. Moore, Eric Davis, Brian Hartvigsen'
__doc__             = '''
Usage:

%s [options] command [command args or options]

 Commands:

  list                     list all calendars

  search <text>            search for events
                           - case insensitive search terms to find events that
                             match these terms in any field, like traditional
                             Google search with quotes, exclusion, etc.
                           - for example to get just games: "soccer -practice"

  agenda [start] [end]     get an agenda for a time period
                           - start time default is 12am today
                           - end time default is 5 days from start
                           - example time strings:
                              '9/24/2007'
                              '24/09/2007'
                              '24/9/07'
                              'Sep 24 2007 3:30pm'
                              '2007-09-24T15:30'
                              '2007-09-24T15:30-8:00'
                              '20070924T15'
                              '8am'

  calw <weeks> [start]     get a week based agenda in a nice calendar format
                           - weeks is the number of weeks to display
                           - start time default is beginning of this week
                           - note that all events for the week(s) are displayed

  calm [start]             get a month agenda in a nice calendar format
                           - start time default is the beginning of this month
                           - note that all events for the month are displayed
                             and only one month will be displayed

  quick <text>             quick add an event to a calendar
                           - a single --cal must specified
                           - the --detail-url option will show the event link
                           - example text:
                              'Dinner with Eric 7pm tomorrow'
                              '5pm 10/31 Trick or Treat'

  add                      add a detailed event to a calendar
                           - a single --cal must specified
                           - the --detail-url option will show the event link
                           - example:
                              gcalcli --cal 'Eric Davis'
                                      --title 'Analysis of Algorithms Final'
                                      --where UCI
                                      --when '12/14/2012 10:00'
                                      --duration 60
                                      --descr 'It is going to be hard!'
                                      --reminder 30
                                      add

  delete <text>            delete event(s)
                           - case insensitive search terms to find and delete
                             events, just like the 'search' command
                           - deleting is interactive
                             use the --iama-expert option to auto delete
                             THINK YOU'RE AN EXPERT? USE AT YOUR OWN RISK!!!
                           - use the --detail options to show event details

  edit <text>              edit event(s)
                           - case insensitive search terms to find and edit
                             events, just like the 'search' command
                           - editing is interactive

  import [file]            import an ics/vcal file to a calendar
                           - a single --cal must specified
                           - if a file is not specified then the data is read
                             from standard input
                           - if -v is given then each event in the file is
                             displayed and you're given the option to import
                             or skip it, by default everything is imported
                             quietly without any interaction
                           - if -d is given then each event in the file is
                             displayed and is not imported, a --cal does not
                             need to be specified for this option

  remind <mins> <command>  execute command if event occurs within <mins>
                           minutes time ('%%s' in <command> is replaced with
                           event start time and title text)
                           - <mins> default is 10
                           - default command:
                              'notify-send -u critical -a gcalcli %%s'
'''

__API_CLIENT_ID__ = '232867676714.apps.googleusercontent.com'
__API_CLIENT_SECRET__ = '3tZSxItw6_VnZMezQwC8lUqy'

# These are standard libraries and should never fail
from Tkinter import * # Python2
import sys, os, re, shlex, time, calendar
import locale, textwrap, signal
from Queue import Queue
from datetime import datetime, timedelta, date
from unicodedata import east_asian_width
import traceback

# Required 3rd partie libraries
try:
    from dateutil.tz import *
    from dateutil.parser import *
    from dateutil.rrule import *
    import gflags
    import httplib2
    from apiclient.discovery import build
    from oauth2client.file import Storage
    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client.tools import run
except ImportError as e:
    print "ERROR: Missing module - %s" % e.args[0]
    sys.exit(1)

# cPickle is a standard library, but in case someone did something really
# dumb, fall back to pickle.  If that's not their, your python is fucked
try:
    import cPickle as pickle
except ImportError:
    import pickle

# simplejson is the upstream version of the json standard library.  Use it if
# it's available, otherwise, just use the standard library
try:
    from simplejson import json
except ImportError:
    import json

# If they have parsedatetime, we'll use it for fuzzy datetime comparison.  If
# not, we just return a fake failure every time and use only dateutil.
try:
    from parsedatetime import parsedatetime
except:
    class parsedatetime:
        class Calendar:
            def parse(self, string):
                return ([], 0)

def Version():
    sys.stdout.write(__program__+' '+__version__+' ('+__author__+')\n')
    sys.exit(1)

def Usage(expanded=False):
    sys.stdout.write(__doc__ % sys.argv[0])
    if expanded:
        print FLAGS.MainModuleHelp()
    sys.exit(1)

# build up fields for at-end output:
oCalendar = 'Calendar'
oDate = '1/1/1001'
oTime = '1:1:1'
oDuration = 1
oDescription = u'Description'
start_date = '1/1/1001'
end_date = '1/1/1001'
search_string = u'bill'
destination_file = "t1.csv"
# TODO; build up fields for entry by operator:
# TODO; pull tkinter from main.py then pass those fields into controlling this CSV execution.

class CLR:

    useColor = True
    conky    = False

    def __str__(self):
        return self.color if self.useColor else ""

class CLR_NRM(CLR):   color = "\033[0m"
class CLR_BLK(CLR):   color = "\033[0;30m"
class CLR_BRBLK(CLR): color = "\033[30;1m"
class CLR_RED(CLR):   color = "\033[0;31m"
class CLR_BRRED(CLR): color = "\033[31;1m"
class CLR_GRN(CLR):   color = "\033[0;32m"
class CLR_BRGRN(CLR): color = "\033[32;1m"
class CLR_YLW(CLR):   color = "\033[0;33m"
class CLR_BRYLW(CLR): color = "\033[33;1m"
class CLR_BLU(CLR):   color = "\033[0;34m"
class CLR_BRBLU(CLR): color = "\033[34;1m"
class CLR_MAG(CLR):   color = "\033[0;35m"
class CLR_BRMAG(CLR): color = "\033[35;1m"
class CLR_CYN(CLR):   color = "\033[0;36m"
class CLR_BRCYN(CLR): color = "\033[36;1m"
class CLR_WHT(CLR):   color = "\033[0;37m"
class CLR_BRWHT(CLR): color = "\033[37;1m"


def SetConkyColors():
    # XXX these colors should be configurable
    CLR.conky       = True
    CLR_NRM.color   = ""
    CLR_BLK.color   = "${color black}"
    CLR_BRBLK.color = "${color black}"
    CLR_RED.color   = "${color red}"
    CLR_BRRED.color = "${color red}"
    CLR_GRN.color   = "${color green}"
    CLR_BRGRN.color = "${color green}"
    CLR_YLW.color   = "${color yellow}"
    CLR_BRYLW.color = "${color yellow}"
    CLR_BLU.color   = "${color blue}"
    CLR_BRBLU.color = "${color blue}"
    CLR_MAG.color   = "${color magenta}"
    CLR_BRMAG.color = "${color magenta}"
    CLR_CYN.color   = "${color cyan}"
    CLR_BRCYN.color = "${color cyan}"
    CLR_WHT.color   = "${color white}"
    CLR_BRWHT.color = "${color white}"


class ART:

    useArt = True
    fancy  = ''
    plain  = ''

    def __str__(self):
        return self.fancy if self.useArt else self.plain

class ART_HRZ(ART): fancy = '\033(0\x71\033(B' ; plain = '-'
class ART_VRT(ART): fancy = '\033(0\x78\033(B' ; plain = '|'
class ART_LRC(ART): fancy = '\033(0\x6A\033(B' ; plain = '+'
class ART_URC(ART): fancy = '\033(0\x6B\033(B' ; plain = '+'
class ART_ULC(ART): fancy = '\033(0\x6C\033(B' ; plain = '+'
class ART_LLC(ART): fancy = '\033(0\x6D\033(B' ; plain = '+'
class ART_CRS(ART): fancy = '\033(0\x6E\033(B' ; plain = '+'
class ART_LTE(ART): fancy = '\033(0\x74\033(B' ; plain = '+'
class ART_RTE(ART): fancy = '\033(0\x75\033(B' ; plain = '+'
class ART_BTE(ART): fancy = '\033(0\x76\033(B' ; plain = '+'
class ART_UTE(ART): fancy = '\033(0\x77\033(B' ; plain = '+'


def PrintErrMsg(msg):
    PrintMsg(CLR_BRRED(), msg)

def PrintMsg(color, msg):
    if isinstance(msg, unicode):
        msg = msg.encode(locale.getpreferredencoding() or "UTF-8", "ignore")

    if CLR.useColor:
        sys.stdout.write(str(color))
        sys.stdout.write(msg)
        sys.stdout.write(str(CLR_NRM()))
    else:
        sys.stdout.write(msg)

def DebugPrint(msg):
    return
    PrintMsg(CLR_YLW(), msg)

def dprint(obj):
    try:
        from pprint import pprint
        pprint(obj)
    except ImportError, e:
        print obj


class DateTimeParser:
    def __init__(self):
        self.pdtCalendar = parsedatetime.Calendar()

    def fromString(self, eWhen, useMidnight=True):
        if useMidnight:
            defaultDateTime = datetime.now(tzlocal()).replace(hour=0,
                                                     minute=0,
                                                     second=0,
                                                     microsecond=0)
        else:
            defaultDateTime = datetime.now(tzlocal())

        try:
            eTimeStart = parse(eWhen, default=defaultDateTime)
        except:
            struct, result = self.pdtCalendar.parse(eWhen)
            if not result:
                raise ValueError("Date and time is invalid")
            eTimeStart = datetime.fromtimestamp(time.mktime(struct), tzlocal())


        return eTimeStart

def DaysSinceEpoch(dt):
    # Because I hate magic numbers
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__

def GetTimeFromStr(eWhen, eDuration=0):
    dtp = DateTimeParser()

    try:
        eTimeStart = dtp.fromString(eWhen)
    except:
        PrintErrMsg('Date and time is invalid!\n')
        sys.exit(1)

    try:
        eTimeStop = eTimeStart + timedelta(minutes=float(eDuration))
    except:
        PrintErrMsg('Duration time (minutes) is invalid\n')
        sys.exit(1)

    sTimeStart = eTimeStart.isoformat()
    sTimeStop = eTimeStop.isoformat()

    return sTimeStart, sTimeStop


class gcalcli:

    cache         = {}
    refreshCache  = False
    useCache      = True
    allCals       = []
    allEvents     = []
    cals          = []
    now           = datetime.now(tzlocal())
    agendaLength  = 5
    authHttp      = None
    calService    = None
    urlService    = None
    military      = False
    ignoreStarted = False
    calWidth      = 10
    calMonday     = False
    command       = 'notify-send -u critical -a gcalcli %s'
    tsv           = False
    dateParser    = DateTimeParser()

    detailCalendar   = False
    detailLocation   = False
    detailLength     = False
    detailReminders  = False
    detailDescr      = False
    detailDescrWidth = 80
    detailUrl        = None

    calOwnerColor    = CLR_CYN()
    calWriterColor   = CLR_GRN()
    calReaderColor   = CLR_MAG()
    calFreeBusyColor = CLR_NRM()
    dateColor        = CLR_YLW()
    nowMarkerColor   = CLR_BRRED()
    borderColor      = CLR_WHT()

    ACCESS_OWNER    = 'owner'
    ACCESS_WRITER   = 'writer'
    ACCESS_READER   = 'reader'
    ACCESS_FREEBUSY = 'freeBusyReader'

    def __init__(self,
                 calNames=[],
                 calNameColors=[],
                 military=False,
                 detailCalendar=False,
                 detailLocation=False,
                 detailLength=False,
                 detailReminders=False,
                 detailDescr=False,
                 detailDescrWidth=80,
                 detailUrl=None,
                 ignoreStarted=False,
                 calWidth=10,
                 calMonday=False,
                 calOwnerColor=CLR_CYN(),
                 calWriterColor=CLR_GRN(),
                 calReaderColor=CLR_MAG(),
                 calFreeBusyColor=CLR_NRM(),
                 dateColor=CLR_YLW(),
                 nowMarkerColor=CLR_BRRED(),
                 borderColor=CLR_WHT(),
                 tsv=False,
                 refreshCache=False,
                 useCache=True,
                 configFolder=None,
                 client_id=__API_CLIENT_ID__,
                 client_secret=__API_CLIENT_SECRET__):

        self.military      = military
        self.ignoreStarted = ignoreStarted
        self.calWidth      = calWidth
        self.calMonday     = calMonday
        self.tsv           = tsv
        self.refreshCache  = refreshCache
        self.useCache      = useCache

        self.detailCalendar   = detailCalendar
        self.detailLocation   = detailLocation
        self.detailLength     = detailLength
        self.detailReminders  = detailReminders
        self.detailDescr      = detailDescr
        self.detailDescrWidth = detailDescrWidth
        self.detailUrl        = detailUrl

        self.calOwnerColor    = calOwnerColor
        self.calWriterColor   = calWriterColor
        self.calReaderColor   = calReaderColor
        self.calFreeBusyColor = calFreeBusyColor
        self.dateColor        = dateColor
        self.nowMarkerColor   = nowMarkerColor
        self.borderColor      = borderColor

        self.configFolder     = configFolder

        self.client_id        = client_id
        self.client_secret    = client_secret

        self._GetCached()

        for cal in self.allCals:
            if len(calNames):
                for i in xrange(len(calNames)):
                    if re.search(calNames[i].lower(), cal['summary'].lower()):
                        self.cals.append(cal)
                        cal['colorSpec'] = calNameColors[i]
            else:
                self.cals = self.allCals

    @staticmethod
    def _LocalizeDateTime(dt):
        if not hasattr(dt, 'tzinfo'):
            return dt
        if dt.tzinfo == None:
            return dt.replace(tzinfo=tzlocal())
        else:
            return dt.astimezone(tzlocal())


    def _GoogleAuth(self):
        if not self.authHttp:
            if self.configFolder:
                storage = Storage(os.path.expanduser("%s/oauth" % self.configFolder))
            else:
                storage = Storage(os.path.expanduser('~/.gcalcli_oauth'))
            credentials = storage.get()

            if credentials is None or credentials.invalid == True:
                credentials = run(
                    OAuth2WebServerFlow(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scope=['https://www.googleapis.com/auth/calendar',
                               'https://www.googleapis.com/auth/urlshortener'],
                        user_agent=__program__+'/'+__version__),
                    storage)

            self.authHttp = credentials.authorize(httplib2.Http())

        return self.authHttp


    def _CalService(self):
        if not self.calService:
            self.calService = \
                 build(serviceName='calendar',
                       version='v3',
                       http=self._GoogleAuth())

        return self.calService


    def _UrlService(self):
        if not self.urlService:
            self._GoogleAuth()
            self.urlService = \
                 build(serviceName='urlshortener',
                       version='v1',
                       http=self._GoogleAuth())

        return self.urlService


    def _GetCached(self):
        if self.configFolder:
            cacheFile = os.path.expanduser("%s/cache" % self.configFolder)
        else:
            cacheFile = os.path.expanduser('~/.gcalcli_cache')

        if self.refreshCache:
            try:
                os.remove(cacheFile)
            except OSError:
                pass
                # fall through

        self.cache     = {}
        self.allCals   = []

        if self.useCache:
            # note that we need to use pickle for cache data since we stuff
            # various non-JSON data in the runtime storage structures
            try:
                with open(cacheFile, 'rb') as _cache_:
                    self.cache     = pickle.load(_cache_)
                    self.allCals   = self.cache['allCals']
                # XXX assuming data is valid, need some verification check here
                return
            except IOError:
                pass
                # fall through

        calList = self._CalService().calendarList().list().execute()

        while True:
            for cal in calList['items']:
                self.allCals.append(cal)
            pageToken = calList.get('nextPageToken')
            if pageToken:
                calList = self._CalService().calendarList().\
                          list(pageToken = pageToken).execute()
            else:
                break

        # gcalcli defined way to order calendars
        order = { self.ACCESS_OWNER    : 1,
                  self.ACCESS_WRITER   : 2,
                  self.ACCESS_READER   : 3,
                  self.ACCESS_FREEBUSY : 4 }

        self.allCals.sort(lambda x, y:
                           cmp(order[x['accessRole']],
                               order[y['accessRole']]))

        if self.useCache:
            self.cache['allCals']   = self.allCals
            with open(cacheFile, 'wb') as _cache_:
                pickle.dump(self.cache, _cache_)


    def _ShortenURL(self, url):
        if self.detailUrl != "short":
            return url
        # Note that when authenticated to a google account different shortUrls
        # can be returned for the same longUrl. See: http://goo.gl/Ya0A9
        shortUrl = self._UrlService().url().insert(body={'longUrl':url}).execute()
        return shortUrl['id']


    def _CalendarColor(self, cal):

        if cal == None:
            return CLR_NRM()
        elif 'colorSpec' in cal and cal['colorSpec'] != None:
            return cal['colorSpec']
        elif cal['accessRole'] == self.ACCESS_OWNER:
            return self.calOwnerColor
        elif cal['accessRole'] == self.ACCESS_WRITER:
            return self.calWriterColor
        elif cal['accessRole'] == self.ACCESS_READER:
            return self.calReaderColor
        elif cal['accessRole'] == self.ACCESS_FREEBUSY:
            return self.calFreeBusyColor
        else:
            return CLR_NRM()


    def _ValidTitle(self, event):
        if 'summary' in event and event['summary'].strip():
            return event['summary']
        else:
            return "(No title)"


    def _GetWeekEventStrings(self, cmd, curMonth,
                             startDateTime, endDateTime, eventList):

        weekEventStrings = [ '', '', '', '', '', '', '' ]

        nowMarkerPrinted = False
        if self.now < startDateTime or self.now > endDateTime:
            # now isn't in this week
            nowMarkerPrinted = True

        for event in eventList:

            if cmd == 'calm' and curMonth != event['s'].strftime("%b"):
                continue

            dayNum = int(event['s'].strftime("%w"))
            if self.calMonday:
                dayNum -= 1
                if dayNum < 0:
                    dayNum = 6

            if event['s'] >= startDateTime and event['s'] < endDateTime:

                forceEventColorAsMarker = False

                if event['s'].hour == 0 and event['s'].minute == 0 and \
                   event['e'].hour == 0 and event['e'].minute == 0:
                    tmpTimeStr = ''
                else:
                    if not nowMarkerPrinted:
                        if DaysSinceEpoch(self.now) < DaysSinceEpoch(event['s']):
                          nowMarkerPrinted = True
                          weekEventStrings[dayNum-1] += \
                                ("\n" +
                                 str(self.nowMarkerColor) +
                                 (self.calWidth * '-'))
                        elif self.now <= event['s']:
                            # add a line marker before next event
                            nowMarkerPrinted = True
                            weekEventStrings[dayNum] += \
                                ("\n" +
                                 str(self.nowMarkerColor) +
                                 (self.calWidth * '-'))
                        elif self.now >= event['s'] and self.now <= event['e']:
                            # line marker is during the event (recolor event)
                            nowMarkerPrinted = True
                            forceEventColorAsMarker = True

                    if self.military:
                        tmpTimeStr = event['s'].strftime("%H:%M")
                    else:
                        tmpTimeStr = \
                            event['s'].strftime("%I:%M").lstrip('0') + \
                            event['s'].strftime('%p').lower()

                if forceEventColorAsMarker:
                    eventColor = self.nowMarkerColor
                else:
                    eventColor = self._CalendarColor(event['gcalcli_cal'])

                # newline and empty string are the keys to turn off coloring
                weekEventStrings[dayNum] += \
                    "\n" + \
                    str(eventColor) + \
                    tmpTimeStr.strip() + \
                    " " + \
                    self._ValidTitle(event).strip()

        return weekEventStrings


    UNIWIDTH = {'W': 2, 'F': 2, 'N': 1, 'Na': 1, 'H': 1, 'A': 1}


    def _PrintLen(self, string):
        # We need to treat everything as unicode for this to actually give
        # us the info we want.  Date string were coming in as `str` type
        # so we convert them to unicode and then check their size. Fixes
        # the output issues we were seeing around non-US locale strings
        if not isinstance(string, unicode):
            string = unicode(string, locale.getpreferredencoding() or "UTF-8")
        printLen = 0
        for tmpChar in string:
            printLen += self.UNIWIDTH[east_asian_width(tmpChar)]
        return printLen


    # return print length before cut, cut index, and force cut flag
    def _NextCut(self, string, curPrintLen):
        idx = 0
        printLen = 0
        if not isinstance(string, unicode):
            string = unicode(string, locale.getpreferredencoding() or "UTF-8")
        for tmpChar in string:
            if (curPrintLen + printLen) >= self.calWidth:
                return (printLen, idx, True)
            if tmpChar in (' ', '\n'):
                return (printLen, idx, False)
            idx += 1
            printLen += self.UNIWIDTH[east_asian_width(tmpChar)]
        return (printLen, -1, False)


    def _GetCutIndex(self, eventString):

        printLen = self._PrintLen(eventString)

        if printLen <= self.calWidth:
            if '\n' in eventString:
                idx = eventString.find('\n')
                printLen = self._PrintLen(eventString[:idx])
            else:
                idx = len(eventString)

            DebugPrint("------ printLen=%d (end of string)\n" % idx)
            return (printLen, idx)

        cutWidth, cut, forceCut = self._NextCut(eventString, 0)
        DebugPrint("------ cutWidth=%d cut=%d \"%s\"\n" %
                   (cutWidth, cut, eventString))

        if forceCut:
            DebugPrint("--- forceCut cutWidth=%d cut=%d\n" % (cutWidth, cut))
            return (cutWidth, cut)

        DebugPrint("--- looping\n")

        while cutWidth < self.calWidth:

            DebugPrint("--- cutWidth=%d cut=%d \"%s\"\n" %
                       (cutWidth, cut, eventString[cut:]))

            while cut < self.calWidth and \
                  cut < printLen and \
                  eventString[cut] == ' ':
                DebugPrint("-> skipping space <-\n")
                cutWidth += 1
                cut += 1

            DebugPrint("--- cutWidth=%d cut=%d \"%s\"\n" %
                       (cutWidth, cut, eventString[cut:]))

            nextCutWidth, nextCut, forceCut = \
                self._NextCut(eventString[cut:], cutWidth)

            if forceCut:
                DebugPrint("--- forceCut cutWidth=%d cut=%d\n" % (cutWidth, cut))
                break

            cutWidth += nextCutWidth
            cut += nextCut

            if eventString[cut] == '\n':
                break

            DebugPrint("--- loop cutWidth=%d cut=%d\n" % (cutWidth, cut))

        return (cutWidth, cut)


    def _GraphEvents(self, cmd, startDateTime, count, eventList):

        # ignore started events (i.e. that start previous day and end start day)
        while (len(eventList) and eventList[0]['s'] < startDateTime):
            eventList = eventList[1:]

        dayWidthLine = (self.calWidth * str(ART_HRZ()))

        topWeekDivider = (str(self.borderColor) +
                          str(ART_ULC()) + dayWidthLine +
                          (6 * (str(ART_UTE()) + dayWidthLine)) +
                          str(ART_URC()) + str(CLR_NRM()))

        midWeekDivider = (str(self.borderColor) +
                          str(ART_LTE()) + dayWidthLine +
                          (6 * (str(ART_CRS()) + dayWidthLine)) +
                          str(ART_RTE()) + str(CLR_NRM()))

        botWeekDivider = (str(self.borderColor) +
                          str(ART_LLC()) + dayWidthLine +
                          (6 * (str(ART_BTE()) + dayWidthLine)) +
                          str(ART_LRC()) + str(CLR_NRM()))

        empty       = self.calWidth * ' '

        # Get the localized day names... January 1, 2001 was a Monday
        dayNames = [ date(2001, 1, i+1).strftime('%A') for i in range(7) ]
        dayNames = dayNames[6:] + dayNames[:6]

        dayHeader = str(self.borderColor) + str(ART_VRT()) + str(CLR_NRM())
        for i in xrange(7):
            if self.calMonday:
                if i == 6:
                    dayName = dayNames[0]
                else:
                    dayName = dayNames[i+1]
            else:
                dayName = dayNames[i]
            dayName += ' ' * (self.calWidth - self._PrintLen(dayName))
            dayHeader += str(self.dateColor) + dayName + str(CLR_NRM())
            dayHeader += str(self.borderColor) + str(ART_VRT()) + str(CLR_NRM())

        if cmd == 'calm':
            topMonthDivider = (str(self.borderColor) +
                               str(ART_ULC()) + dayWidthLine +
                               (6 * (str(ART_HRZ()) + dayWidthLine)) +
                               str(ART_URC()) + str(CLR_NRM()))
            PrintMsg(CLR_NRM(), "\n" + topMonthDivider + "\n")

            m = startDateTime.strftime('%B %Y')
            mw = (self.calWidth * 7) + 6
            m += ' ' * (mw - self._PrintLen(m))
            PrintMsg(CLR_NRM(),
                     str(self.borderColor) +
                     str(ART_VRT()) +
                     str(CLR_NRM()) +
                     str(self.dateColor) +
                     m +
                     str(CLR_NRM()) +
                     str(self.borderColor) +
                     str(ART_VRT()) +
                     str(CLR_NRM()) +
                     '\n')

            botMonthDivider = (str(self.borderColor) +
                               str(ART_LTE()) + dayWidthLine +
                               (6 * (str(ART_UTE()) + dayWidthLine)) +
                               str(ART_RTE()) + str(CLR_NRM()))
            PrintMsg(CLR_NRM(), botMonthDivider + "\n")

        else: # calw
            PrintMsg(CLR_NRM(), "\n" + topWeekDivider + "\n")

        PrintMsg(CLR_NRM(), dayHeader + "\n")
        PrintMsg(CLR_NRM(), midWeekDivider + "\n")

        curMonth = startDateTime.strftime("%b")

        # get date range objects for the first week
        if cmd == 'calm':
            dayNum = int(startDateTime.strftime("%w"))
            if self.calMonday:
                dayNum -= 1
                if dayNum < 0:
                    dayNum = 6
            startDateTime = (startDateTime - timedelta(days=dayNum))
        startWeekDateTime = startDateTime
        endWeekDateTime = (startWeekDateTime + timedelta(days=7))

        for i in xrange(count):

            # create/print date line
            line = str(self.borderColor) + str(ART_VRT()) + str(CLR_NRM())
            for j in xrange(7):
                if cmd == 'calw':
                    d = (startWeekDateTime +
                         timedelta(days=j)).strftime("%d %b")
                else: # (cmd == 'calm'):
                    d = (startWeekDateTime +
                         timedelta(days=j)).strftime("%d")
                    if curMonth != (startWeekDateTime + \
                                    timedelta(days=j)).strftime("%b"):
                        d = ''
                tmpDateColor = self.dateColor

                if self.now.strftime("%d%b%Y") == \
                   (startWeekDateTime + timedelta(days=j)).strftime("%d%b%Y"):
                    tmpDateColor = self.nowMarkerColor
                    d += " **"

                d += ' ' * (self.calWidth - self._PrintLen(d))
                line += str(tmpDateColor) + \
                        d + \
                        str(CLR_NRM()) + \
                        str(self.borderColor) + \
                        str(ART_VRT()) + \
                        str(CLR_NRM())
            PrintMsg(CLR_NRM(), line + "\n")

            weekColorStrings = [ '', '', '', '', '', '', '' ]
            weekEventStrings = self._GetWeekEventStrings(cmd, curMonth,
                                                         startWeekDateTime,
                                                         endWeekDateTime,
                                                         eventList)

            # convert the strings to unicode for various string ops
            # XXX event strings are already in unicode for Calendar v3 APIs
            #for j in xrange(7):
            #    weekEventStrings[j] = unicode(weekEventStrings[j],
            #                                  locale.getpreferredencoding())

            # get date range objects for the next week
            startWeekDateTime = endWeekDateTime
            endWeekDateTime = (endWeekDateTime + timedelta(days=7))

            while 1:

                done = True
                line = str(self.borderColor) + str(ART_VRT()) + str(CLR_NRM())

                for j in xrange(7):

                    if weekEventStrings[j] == '':
                        weekColorStrings[j] = ''
                        line += (empty +
                                 str(self.borderColor) +
                                 str(ART_VRT()) +
                                 str(CLR_NRM()))
                        continue

                    # get/skip over a color sequence
                    if ((not CLR.conky and weekEventStrings[j][0] == '\033') or
                        (    CLR.conky and weekEventStrings[j][0] == '$')):
                        weekColorStrings[j] = ''
                        while ((not CLR.conky and weekEventStrings[j][0] != 'm') or
                               (    CLR.conky and weekEventStrings[j][0] != '}')):
                            weekColorStrings[j] += weekEventStrings[j][0]
                            weekEventStrings[j] = weekEventStrings[j][1:]
                        weekColorStrings[j] += weekEventStrings[j][0]
                        weekEventStrings[j] = weekEventStrings[j][1:]

                    if weekEventStrings[j][0] == '\n':
                        weekColorStrings[j] = ''
                        weekEventStrings[j] = weekEventStrings[j][1:]
                        line += (empty +
                                 str(self.borderColor) +
                                 str(ART_VRT()) +
                                 str(CLR_NRM()))
                        done = False
                        continue

                    weekEventStrings[j] = weekEventStrings[j].lstrip()

                    printLen, cut = self._GetCutIndex(weekEventStrings[j])
                    padding = ' ' * (self.calWidth - printLen)

                    line += (weekColorStrings[j] +
                             weekEventStrings[j][:cut] +
                             padding +
                             str(CLR_NRM()))
                    weekEventStrings[j] = weekEventStrings[j][cut:]

                    done = False
                    line += (str(self.borderColor) +
                             str(ART_VRT()) +
                             str(CLR_NRM()))

                if done:
                    break

                PrintMsg(CLR_NRM(), line + "\n")

            if i < range(count)[len(range(count))-1]:
                PrintMsg(CLR_NRM(), midWeekDivider + "\n")
            else:
                PrintMsg(CLR_NRM(), botWeekDivider + "\n")


    def _tsv(self, startDateTime, eventList):
        for event in eventList:
            if 'htmlLink' in event:
                tmpLink = self._ShortenURL(event['htmlLink'])
            else:
                tmpLink = ""
            if 'hangoutLink' in event:
                hangoutLink = self._ShortenURL(event['hangoutLink'])
            else:
                hangoutLink = ""
            tmpDayStr  = event['s'].strftime('%F')
            tmpDayStp  = event['e'].strftime('%F')
            tmpTimeStr = event['s'].strftime("%H:%M")
            tmpTimeStp = event['e'].strftime("%H:%M")
            tmpWhere = ''
            if 'location' in event and event['location'].strip():
                tmpWhere = event['location'].strip()
            tmpContent = ''
            if 'description' in event and event['description'].strip():
                tmpContent = event['description'].strip()
            xstr = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                tmpDayStr,
                tmpTimeStr,
                tmpDayStp,
                tmpTimeStp,
                tmpLink,
                hangoutLink,
                self._ValidTitle(event).strip(),
                tmpWhere,
                tmpContent
            )
            xstr2 = "%s\n" % xstr.replace('\n', '''\\n''')
            sys.stdout.write(xstr2.encode(locale.getpreferredencoding() or "UTF-8", "ignore"))


    def _PrintEvent(self, event, prefix):

        def _formatDescr(descr, indent, box):
            wrapper = textwrap.TextWrapper()
            if box:
                wrapper.initial_indent = (indent + '  ')
                wrapper.subsequent_indent = (indent + '  ')
                wrapper.width = (self.detailDescrWidth - 2)
            else:
                wrapper.initial_indent = indent
                wrapper.subsequent_indent = indent
                wrapper.width = self.detailDescrWidth
            new_descr = ""
            for line in descr.split("\n"):
                if box:
                    tmpLine = wrapper.fill(line)
                    for singleLine in tmpLine.split("\n"):
                        singleLine = singleLine.ljust(self.detailDescrWidth,' ')
                        new_descr += singleLine[:len(indent)] + \
                                     str(ART_VRT()) + \
                                     singleLine[(len(indent)+1) :
                                                (self.detailDescrWidth-1)] + \
                                     str(ART_VRT()) + '\n'
                else:
                    new_descr += wrapper.fill(line) + "\n"
            return new_descr.rstrip()

        indent = 10 * ' '
        detailsIndent = 19 * ' '

        if self.military:
            timeFormat = '%-5s'
            tmpTimeStr = event['s'].strftime("%H:%M")
        else:
            timeFormat = '%-7s'
            tmpTimeStr = \
                event['s'].strftime("%I:%M").lstrip('0').rjust(5) + \
                event['s'].strftime('%p').lower()

        if not prefix:
            prefix = indent

        PrintMsg(self.dateColor, prefix)
        if event['s'].hour == 0 and event['s'].minute == 0 and \
           event['e'].hour == 0 and event['e'].minute == 0:
            fmt = '  ' + timeFormat + '  %s\n'
            PrintMsg(self._CalendarColor(event['gcalcli_cal']), fmt %
                     ('', self._ValidTitle(event).strip()))
        else:
            fmt = '  ' + timeFormat + '  %s\n'
#            if 'summary' not in event:
#                dprint(event)
            PrintMsg(self._CalendarColor(event['gcalcli_cal']), fmt %
                     (tmpTimeStr, self._ValidTitle(event).strip()))

        if self.detailCalendar:
            xstr = "%s  Calendar: %s\n" % (
                detailsIndent,
                event['gcalcli_cal']['summary']
            )
            PrintMsg(CLR_NRM(), xstr)

        if self.detailUrl and 'htmlLink' in event:
            hLink = self._ShortenURL(event['htmlLink'])
            xstr = "%s  Link: %s\n" % (detailsIndent, hLink)
            PrintMsg(CLR_NRM(), xstr)

        if self.detailUrl and 'hangoutLink' in event:
            hLink = self._ShortenURL(event['hangoutLink'])
            xstr = "%s  Hangout Link: %s\n" % (detailsIndent, hLink)
            PrintMsg(CLR_NRM(), xstr)

        if self.detailLocation and \
           'location' in event and \
           event['location'].strip():
            xstr = "%s  Location: %s\n" % (
                detailsIndent,
                event['location'].strip()
            )
            PrintMsg(CLR_NRM(), xstr)

        if self.detailLength:
            diffDateTime = (event['e'] - event['s'])
            xstr = "%s  Length: %s\n" % (detailsIndent, diffDateTime)
            PrintMsg(CLR_NRM(), xstr)

        if self.detailReminders and 'reminders' in event:
            if event['reminders']['useDefault'] == True:
                xstr = "%s  Reminder: (default)\n" % (detailsIndent)
                PrintMsg(CLR_NRM(), xstr)
            elif 'overrides' in event['reminders']:
                for rem in event['reminders']['overrides']:
                    xstr = "%s  Reminder: %s %d minutes\n" % \
                           (detailsIndent, rem['method'], rem['minutes'])
                    PrintMsg(CLR_NRM(), xstr)

        if self.detailDescr and \
           'description' in event and \
           event['description'].strip():
            descrIndent = detailsIndent + '  '
            box = True # leave old non-box code for option later
            if box:
                topMarker = (descrIndent +
                             str(ART_ULC()) +
                             (str(ART_HRZ()) *
                              ((self.detailDescrWidth - len(descrIndent)) -
                               2)) +
                             str(ART_URC()))
                botMarker = (descrIndent +
                             str(ART_LLC()) +
                             (str(ART_HRZ()) *
                              ((self.detailDescrWidth - len(descrIndent)) -
                               2)) +
                             str(ART_LRC()))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    topMarker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    botMarker
                )
            else:
                marker = descrIndent + '-' * \
                         (self.detailDescrWidth - len(descrIndent))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    marker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    marker
                )
            PrintMsg(CLR_NRM(), xstr)


    def csvPrintEvent(self, event, prefix):
        # build up fields for at-end output:                      Calendar, Date, Time, Duration, Description
        global oCalendar #= 'Calendar'
        global oDate #= '1/1/1001'
        global oTime #= '1:1:1'
        global oDuration #= 1
        global oDescription #= 'Description'
        global start_date
        global end_date
        global search_string
        global destination_file #= "t1.csv"

        def _formatDescr(descr, indent, box):
            wrapper = textwrap.TextWrapper()
            if box:
                wrapper.initial_indent = (indent + '  ')
                wrapper.subsequent_indent = (indent + '  ')
                wrapper.width = (self.detailDescrWidth - 2)
            else:
                wrapper.initial_indent = indent
                wrapper.subsequent_indent = indent
                wrapper.width = self.detailDescrWidth
            new_descr = ""
            for line in descr.split("\n"):
                if box:
                    tmpLine = wrapper.fill(line)
                    for singleLine in tmpLine.split("\n"):
                        singleLine = singleLine.ljust(self.detailDescrWidth,' ')
                        new_descr += singleLine[:len(indent)] + \
                                     str(ART_VRT()) + \
                                     singleLine[(len(indent)+1) :
                                                (self.detailDescrWidth-1)] + \
                                     str(ART_VRT()) + '\n'
                else:
                    new_descr += wrapper.fill(line) + "\n"
            return new_descr.rstrip()

        indent = 10 * ' '
        detailsIndent = 19 * ' '

        if self.military:
            timeFormat = '%-5s'
            tmpTimeStr = event['s'].strftime("%H:%M")
        else:
            timeFormat = '%-7s'
            tmpTimeStr = \
                event['s'].strftime("%I:%M").lstrip('0').rjust(5) + \
                event['s'].strftime('%p').lower()

        if not prefix:
            prefix = indent

        #PrintMsg(self.dateColor, prefix)
        if event['s'].hour == 0 and event['s'].minute == 0 and \
           event['e'].hour == 0 and event['e'].minute == 0:
            fmt = '  ' + timeFormat + '  %s\n'
            #PrintMsg(self._CalendarColor(event['gcalcli_cal']), fmt % ('', self._ValidTitle(event).strip()))
        else:
            fmt = '  ' + timeFormat + '  %s\n'
#            if 'summary' not in event:
#                dprint(event)
            #PrintMsg(self._CalendarColor(event['gcalcli_cal']), fmt % (tmpTimeStr, self._ValidTitle(event).strip()))

        if self.detailCalendar:
            oCalendar = event['gcalcli_cal']['summary']
            xstr = "%s  Calendar: %s\n" % (
                detailsIndent,
                event['gcalcli_cal']['summary']
            )
            #PrintMsg(CLR_NRM(), xstr)

        if self.detailUrl and 'htmlLink' in event:
            hLink = self._ShortenURL(event['htmlLink'])
            xstr = "%s  Link: %s\n" % (detailsIndent, hLink)
            #PrintMsg(CLR_NRM(), xstr)

        if self.detailUrl and 'hangoutLink' in event:
            hLink = self._ShortenURL(event['hangoutLink'])
            xstr = "%s  Hangout Link: %s\n" % (detailsIndent, hLink)
            #PrintMsg(CLR_NRM(), xstr)

        if self.detailLocation and \
           'location' in event and \
           event['location'].strip():
            xstr = "%s  Location: %s\n" % (
                detailsIndent,
                event['location'].strip()
            )
            #PrintMsg(CLR_NRM(), xstr)

        if self.detailLength:
            diffDateTime = (event['e'] - event['s'])
            xstr = "%s  Length: %s\n" % (detailsIndent, diffDateTime)
            #PrintMsg(CLR_NRM(), xstr)

        if self.detailReminders and 'reminders' in event:
            if event['reminders']['useDefault'] == True:
                xstr = "%s  Reminder: (default)\n" % (detailsIndent)
                #PrintMsg(CLR_NRM(), xstr)
            elif 'overrides' in event['reminders']:
                for rem in event['reminders']['overrides']:
                    xstr = "%s  Reminder: %s %d minutes\n" % \
                           (detailsIndent, rem['method'], rem['minutes'])
                    #PrintMsg(CLR_NRM(), xstr)

        if self.detailDescr and \
           'description' in event and \
           event['description'].strip():
            descrIndent = detailsIndent + '  '
            box = True # leave old non-box code for option later
            if box:
                topMarker = (descrIndent +
                             str(ART_ULC()) +
                             (str(ART_HRZ()) *
                              ((self.detailDescrWidth - len(descrIndent)) -
                               2)) +
                             str(ART_URC()))
                botMarker = (descrIndent +
                             str(ART_LLC()) +
                             (str(ART_HRZ()) *
                              ((self.detailDescrWidth - len(descrIndent)) -
                               2)) +
                             str(ART_LRC()))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    topMarker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    botMarker
                )
            else:
                marker = descrIndent + '-' * \
                         (self.detailDescrWidth - len(descrIndent))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    marker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    marker
                )
            #PrintMsg(CLR_NRM(), xstr)

        # fill in oCalendar, oDate, oTime, oDuration, oDescription
        #print(dir(event))
        #Calendar = event.gcalcli_cal['summary']
        # UnboundLocalError: local variable 'oCalendar' referenced before assignment
        #sys.stdout.write ('Debugging,' + oCalendar + "," + str(event['start']) + "," + str(event['end']) + "," + str(event['summary']) + '\n')
        #PrintMsg(CLR_BLK(), 'Debugging,' + Calendar + "," + str(event['start']) + "," + str(event['end']) + "," + str(event['summary']))
        #PrintMsg(CLR_BLK(), 'Debugging,' + Calendar + "," + str(event['start']) + "," + str(event['end']) + "," + str(event['summary']) + "," + Description)
        try:
            ds1 = event['start']['dateTime']
        except:
            ds1 = event['start']['date']
        #ds1 = event['start'].itervalues().next()
        try:
            de1 = event['end']['dateTime']
        except:
            de1 = event['end']['date']
        #de1 = event['end'].itervalues().next()
        from dateutil.parser import parse
        # get around %z not working in strptime
        # per http://stackoverflow.com/questions/2609259/converting-string-to-datetime-object-in-python
        ds = parse(ds1)
        de = parse(de1)
        # is event['creator']['displayName'] == name of calendar?
        # Or use ListAllCalendars()? to get calendars' name.
        # fill in oCalendar, oDate, oTime, oDuration, oDescription
        oCalendar = event['creator']['displayName']
        oDate = ds.date()
        oTime = ds.time()
        oDuration = de - ds
        oDescription = event['summary']
        # does oDescription contain search_string?
        if search_string.upper() in oDescription.upper():
            # TODO; does this event exist in the start_date and end_date range?
            # can't compare offset-naive and offset-aware datetimes
            # And once I fix the offset-naive versus offset-aware datetimes comparison...
            # What's the math for events that pass through my start_date and end_date?
            # start date is set when we query Google Calendar for the events.
            #if start_date.replace(tzinfo=None) <= ds.replace(tzinfo=None) <= end_date.replace(tzinfo=None):
                    #or start_date <= de <= end_date
                    #or ds <= start_date <= de
                    # ds <= end_date <= de
            sys.stdout.write (oCalendar + "," + str(oDate) + "," + str(oTime) + "," + str(oDuration) + "," + str(oDescription) + '\n')
            fOut = open(destination_file, 'a')
            fOut.write(oCalendar + "," + str(oDate) + "," + str(oTime) + "," + str(oDuration) + "," + str(oDescription) + '\n')
            fOut.close()
            #sys.stdout.write (oCalendar + "," + str(event['start']) + "," + str(event['end']) + "," + str(event['summary']) + '\n')
            #PrintMsg(CLR_BLK(), Calendar + "," + str(Date) + "," + str(Time) + "," + str(Duration) + "," + Description)
            #print oCalendar, oDate, oTime, oDuration, oDescription




    def _DeleteEvent(self, event):

        if self.iamaExpert:
            self._CalService().events().\
                 delete(calendarId = event['gcalcli_cal']['id'],
                        eventId = event['id']).execute()
            PrintMsg(CLR_RED(), "Deleted!\n")
            return

        PrintMsg(CLR_MAG(), "Delete? [N]o [y]es [q]uit: ")
        val = raw_input()

        if not val or val.lower() == 'n':
            return

        elif val.lower() == 'y':
            self._CalService().events().\
                 delete(calendarId = event['gcalcli_cal']['id'],
                        eventId = event['id']).execute()
            PrintMsg(CLR_RED(), "Deleted!\n")

        elif val.lower() == 'q':
            sys.stdout.write('\n')
            sys.exit(0)

        else:
            PrintErrMsg('Error: invalid input\n')
            sys.stdout.write('\n')
            sys.exit(1)


    def _EditEvent(self, event):

        while True:

            PrintMsg(CLR_MAG(), "Edit?\n" +
                                "[N]o [s]ave [q]uit " +
                                "[t]itle [l]ocation " +
                                "[w]hen len[g]th " +
                                "[r]eminder [d]escr: ")
            val = raw_input()

            if not val or val.lower() == 'n':
                return

            elif val.lower() == 's':
                # copy only editable event details for patching
                modEvent = {}
                keys = ['summary', 'location', 'start', 'end',
                        'reminders', 'description']
                for k in keys:
                    if k in event:
                        modEvent[k] = event[k]

                self._CalService().events().\
                     patch(calendarId = event['gcalcli_cal']['id'],
                           eventId = event['id'],
                           body = modEvent).execute()
                PrintMsg(CLR_RED(), "Saved!\n")
                return

            elif not val or val.lower() == 'q':
                sys.stdout.write('\n')
                sys.exit(0)

            elif val.lower() == 't':
                PrintMsg(CLR_MAG(), "Title: ")
                val = raw_input()
                if val.strip():
                    event['summary'] = \
                        unicode(val.strip(), locale.getpreferredencoding() or "UTF-8")

            elif val.lower() == 'l':
                PrintMsg(CLR_MAG(), "Location: ")
                val = raw_input()
                if val.strip():
                    event['location'] = \
                        unicode(val.strip(), locale.getpreferredencoding() or "UTF-8")

            elif val.lower() == 'w':
                PrintMsg(CLR_MAG(), "When: ")
                val = raw_input()
                if val.strip():
                    td = (event['e'] - event['s'])
                    length = ((td.days * 1440) + (td.seconds / 60))
                    newStart, newEnd = GetTimeFromStr(val.strip(), length)
                    event['s'] = parse(newStart)
                    event['e'] = parse(newEnd)
                    event['start'] = \
                        { 'dateTime' : newStart,
                          'timeZone' : event['gcalcli_cal']['timeZone'] }
                    event['end'] = \
                        { 'dateTime' : newEnd,
                          'timeZone' : event['gcalcli_cal']['timeZone'] }

            elif val.lower() == 'g':
                PrintMsg(CLR_MAG(), "Length (mins): ")
                val = raw_input()
                if val.strip():
                    newStart, newEnd = \
                        GetTimeFromStr(event['start']['dateTime'], val.strip())
                    event['s'] = parse(newStart)
                    event['e'] = parse(newEnd)
                    event['start'] = \
                        { 'dateTime' : newStart,
                          'timeZone' : event['gcalcli_cal']['timeZone'] }
                    event['end'] = \
                        { 'dateTime' : newEnd,
                          'timeZone' : event['gcalcli_cal']['timeZone'] }

            elif val.lower() == 'r':
                PrintMsg(CLR_MAG(), "Reminder (mins): ")
                val = raw_input()
                if val.strip().isdigit():
                    event['reminders'] = \
                        {'useDefault' : False,
                         'overrides'  : [{'minutes' : int(val.strip()),
                                          'method'  : 'popup'}]}

            elif val.lower() == 'd':
                PrintMsg(CLR_MAG(), "Description: ")
                val = raw_input()
                if val.strip():
                    event['description'] = \
                        unicode(val.strip(), locale.getpreferredencoding() or "UTF-8")

            else:
                PrintErrMsg('Error: invalid input\n')
                sys.stdout.write('\n')
                sys.exit(1)

            self._PrintEvent(event, event['s'].strftime('\n%F'))


    def _IterateEvents(self, startDateTime, eventList,
                       yearDate=False, work=None):

        if len(eventList) == 0:
            PrintMsg(CLR_YLW(), "\nNo Events Found...\n")
            return

        # 10 chars for day and length must match 'indent' in _PrintEvent
        dayFormat = '\n%F' if yearDate else '\n%a %b %d'
        day = ''

        for event in eventList:

            if self.ignoreStarted and (event['s'] < startDateTime):
                continue

            tmpDayStr = event['s'].strftime(dayFormat)
            prefix    = None
            if yearDate or tmpDayStr != day:
                day = prefix = tmpDayStr

            self.csvPrintEvent(event, prefix)
            #if sysargv0 == 'csv':
            #    self.csvPrintEvent(event, prefix)
            #else:
            #    self._PrintEvent(event, prefix)

            if work:
                work(event)


    def _GetAllEvents(self, cal, events, end):

        eventList = []

        while 1:
            if 'items' not in events:
                break

            for event in events['items']:

                event['gcalcli_cal'] = cal

                if 'status' in event and event['status'] == 'cancelled':
                    continue

                if 'dateTime' in event['start']:
                    event['s'] = parse(event['start']['dateTime'])
                else:
                    event['s'] = parse(event['start']['date']) # all date events

                event['s'] = self._LocalizeDateTime(event['s'])

                if 'dateTime' in event['end']:
                    event['e'] = parse(event['end']['dateTime'])
                else:
                    event['e'] = parse(event['end']['date']) # all date events

                event['e'] = self._LocalizeDateTime(event['e'])

                # For all-day events, Google seems to assume that the event time
                # is based in the UTC instead of the local timezone.  Here we
                # filter out those events start beyond a specified end time.
                if end and (event['s'] >= end):
                    continue

                # http://en.wikipedia.org/wiki/Year_2038_problem
                # Catch the year 2038 problem here as the python dateutil module
                # can choke throwing a ValueError exception. If either the start
                # or end time for an event has a year '>= 2038' dump it.
                if event['s'].year >= 2038 or event['e'].year >= 2038:
                    continue

                eventList.append(event)

            pageToken = events.get('nextPageToken')
            if pageToken:
                events = self._CalService().events().\
                         list(calendarId = cal['id'],
                              pageToken = pageToken).execute()
            else:
                break

        return eventList


    def _SearchForCalEvents(self, start, end, searchText):

        eventList = []

        queue = Queue()
        threads = []

        def worker(cal, work):
            events = work.execute()
            queue.put((cal, events))

        for cal in self.cals:

            work = self._CalService().events().\
                   list(calendarId = cal['id'],
                        timeMin = start.isoformat() if start else None,
                        timeMax = end.isoformat() if end else None,
                        q = searchText if searchText else None,
                        singleEvents = True)

            #th = threading.Thread(target=worker, args=(cal, work))
            #threads.append(th)
            #th.start()
            events = work.execute()
            queue.put((cal, events))

        #for th in threads:
        #    th.join()

        while not queue.empty():
            cal, events = queue.get()
            eventList.extend(self._GetAllEvents(cal, events, end))

        eventList.sort(lambda x, y: cmp(x['s'], y['s']))

        return eventList


    def ListAllCalendars(self):

        accessLen = 0

        for cal in self.allCals:
            length = len(cal['accessRole'])
            if length > accessLen: accessLen = length

        if accessLen < len('Access'): accessLen = len('Access')

        format = ' %0' + str(accessLen) + 's  %s\n'

        PrintMsg(CLR_BRYLW(), format % ('Access', 'Title'))
        PrintMsg(CLR_BRYLW(), format % ('------', '-----'))

        for cal in self.allCals:
            PrintMsg(self._CalendarColor(cal),
                     format % (cal['accessRole'], cal['summary']))


    def TextQuery(self, searchText=''):

        # the empty string would get *ALL* events...
        if searchText == '':
            return

        if self.ignoreStarted:
            start = self.now
        else:
            start = None

        eventList = self._SearchForCalEvents(start, None, searchText)

        self._IterateEvents(self.now, eventList, yearDate=True)


    def AgendaQuery(self, startText='', endText=''):
        if startText == '':
            if self.ignoreStarted:
                start = self.now
            else:
                # convert now to midnight this morning and use for default
                start = self.now.replace(hour=0,
                                         minute=0,
                                         second=0,
                                         microsecond=0)
        else:
            try:
                from dateutil.parser import parse
                #start = parse(startText) # AttributeError datetime.datetime object has no attribute 'read'
                start = self.dateParser.fromString(startText, not self.ignoreStarted) # ValueError Date and time is invalid
                #start = startText # Bad Request
            except:
                PrintErrMsg('Error: failed to parse start time\n')
                return

        if endText == '':
            end = (start + timedelta(days=self.agendaLength))
        else:
            try:
                #end = endText # Bad Request
                end = self.dateParser.fromString(endText, not self.ignoreStarted)
            except:
                PrintErrMsg('Error: failed to parse end time\n')
                return

        eventList = self._SearchForCalEvents(start, end, None)

        if self.tsv:
            self._tsv(start, eventList)
        else:
            self._IterateEvents(start, eventList, yearDate=False)


    def CalQuery(self, cmd, startText='', count=1):

        if startText == '':
            # convert now to midnight this morning and use for default
            start = self.now.replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0)
        else:
            try:
                start = self.dateParser.fromString(startText)
                start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            except:
                PrintErrMsg('Error: failed to parse start time\n')
                return

        # convert start date to the beginning of the week or month
        if cmd == 'calw':
            dayNum = int(start.strftime("%w"))
            if self.calMonday:
                dayNum -= 1
                if dayNum < 0:
                    dayNum = 6
            start = (start - timedelta(days=dayNum))
            end = (start + timedelta(days=(count * 7)))
        else: # cmd == 'calm':
            start = (start - timedelta(days=(start.day - 1)))
            endMonth = (start.month + 1)
            endYear = start.year
            if endMonth == 13:
                endMonth = 1
                endYear += 1
            end = start.replace(month=endMonth, year=endYear)
            daysInMonth = (end - start).days
            offsetDays = int(start.strftime('%w'))
            if self.calMonday:
                offsetDays -= 1
                if offsetDays < 0:
                    offsetDays = 6
            totalDays = (daysInMonth + offsetDays)
            count = (totalDays / 7)
            if totalDays % 7:
                count += 1

        eventList = self._SearchForCalEvents(start, end, None)

        self._GraphEvents(cmd, start, count, eventList)


    def QuickAddEvent(self, eventText, reminder=None):

        if eventText == '':
            return

        if len(self.cals) != 1:
            PrintErrMsg("Must specify a single calendar\n")
            return

        newEvent = self._CalService().events().\
                   quickAdd(calendarId = self.cals[0]['id'],
                            text = eventText).execute()

        if reminder:
            rem = {}
            rem['reminders'] = {'useDefault' : False,
                                'overrides'  : [{'minutes' : reminder,
                                                 'method'  : 'popup'}]}

            newEvent = self._CalService().events().\
                       patch(calendarId = self.cals[0]['id'],
                             eventId = newEvent['id'],
                             body = rem).execute()

        if self.detailUrl:
            hLink = self._ShortenURL(newEvent['htmlLink'])
            PrintMsg(CLR_GRN(), 'New event added: %s\n' % hLink)


    def AddEvent(self, eTitle, eWhere, eStart, eEnd, eDescr, reminder):

        if len(self.cals) != 1:
            PrintErrMsg("Must specify a single calendar\n")
            return

        event = {}
        event['summary'] = unicode(eTitle, locale.getpreferredencoding() or "UTF-8")
        event['start']   = { 'dateTime' : eStart,
                             'timeZone' : self.cals[0]['timeZone'] }
        event['end']     = { 'dateTime' : eEnd,
                             'timeZone' : self.cals[0]['timeZone'] }
        if eWhere:
            event['location'] = unicode(eWhere, locale.getpreferredencoding() or "UTF-8")
        if eDescr:
            event['description'] = unicode(eDescr, locale.getpreferredencoding() or "UTF-8")
        if reminder:
            event['reminders'] = {'useDefault' : False,
                                  'overrides'  : [{'minutes' : reminder,
                                                   'method'  : 'popup'}]}

        newEvent = self._CalService().events().\
                   insert(calendarId = self.cals[0]['id'],
                          body = event).execute()

        if self.detailUrl:
            hLink = self._ShortenURL(newEvent['htmlLink'])
            PrintMsg(CLR_GRN(), 'New event added: %s\n' % hLink)


    def DeleteEvents(self, searchText='', expert=False):

        # the empty string would get *ALL* events...
        if searchText == '':
            return

        eventList = self._SearchForCalEvents(None, None, searchText)

        self.iamaExpert = expert
        self._IterateEvents(self.now, eventList,
                            yearDate=True, work=self._DeleteEvent)


    def EditEvents(self, searchText=''):

        # the empty string would get *ALL* events...
        if searchText == '':
            return

        eventList = self._SearchForCalEvents(None, None, searchText)

        self._IterateEvents(self.now, eventList,
                            yearDate=True, work=self._EditEvent)


    def Remind(self, minutes=10, command=None):

        if command == None:
            command = self.command

        # perform a date query for now + minutes + slip
        start = self.now
        end   = (start + timedelta(minutes=(minutes + 5)))

        eventList = self._SearchForCalEvents(start, end, None)

        message = ''

        for event in eventList:

            # skip this event if it already started
            # XXX maybe add a 2+ minute grace period here...
            if event['s'] < self.now:
                continue

            if self.military:
                tmpTimeStr = event['s'].strftime('%H:%M')
            else:
                tmpTimeStr = \
                    event['s'].strftime('%I:%M').lstrip('0') + \
                    event['s'].strftime('%p').lower()

            message += '%s  %s\n' % \
                       (tmpTimeStr, self._ValidTitle(event).strip())

        if message == '':
            return

        cmd = shlex.split(command)

        for i, a in zip(xrange(len(cmd)), cmd):
            if a == '%s':
                cmd[i] = message

        pid = os.fork()
        if not pid:
            os.execvp(cmd[0], cmd)


    def ImportICS(self, verbose=False, dump=False, reminder=None, icsFile=None):

        def CreateEventFromVOBJ(ve):

            event = {}

            if verbose:
                print "+----------------+"
                print "| Calendar Event |"
                print "+----------------+"

            if hasattr(ve, 'summary'):
                DebugPrint("SUMMARY: %s\n" % ve.summary.value)
                if verbose:
                    print "Event........%s" % ve.summary.value
                event['summary'] = ve.summary.value

            if hasattr(ve, 'location'):
                DebugPrint("LOCATION: %s\n" % ve.location.value)
                if verbose:
                    print "Location.....%s" % ve.location.value
                event['location'] = ve.location.value

            if not hasattr(ve, 'dtstart') or not hasattr(ve, 'dtend'):
                PrintErrMsg("Error: event does not have a dtstart and dtend!\n")
                return None

            if ve.dtstart.value:
                DebugPrint("DTSTART: %s\n" % ve.dtstart.value.isoformat())
            if ve.dtend.value:
                DebugPrint("DTEND: %s\n" % ve.dtend.value.isoformat())
            if verbose:
                if ve.dtstart.value:
                    print "Start........%s" % ve.dtstart.value.isoformat()
                if ve.dtend.value:
                    print "End..........%s" % ve.dtend.value.isoformat()
                if ve.dtstart.value:
                    print "Local Start..%s" % self._LocalizeDateTime(ve.dtstart.value)
                if ve.dtend.value:
                    print "Local End....%s" % self._LocalizeDateTime(ve.dtend.value)

            if hasattr(ve, 'rrule'):

                DebugPrint("RRULE: %s\n" % ve.rrule.value)
                if verbose:
                    print "Recurrence...%s" % ve.rrule.value

                event['recurrence'] = [ "RRULE:" + ve.rrule.value ]

            if hasattr(ve, 'dtstart') and ve.dtstart.value:
                # XXX
                # Timezone madness! Note that we're using the timezone for the
                # calendar being added to. This is OK if the event is in the
                # same timezone. This needs to be changed to use the timezone
                # from the DTSTART and DTEND values. Problem is, for example,
                # the TZID might be "Pacific Standard Time" and Google expects
                # a timezone string like "America/Los_Angeles". Need to find
                # a way in python to convert to the more specific timezone
                # string.
                # XXX
                # print ve.dtstart.params['X-VOBJ-ORIGINAL-TZID'][0]
                # print self.cals[0]['timeZone']
                # print dir(ve.dtstart.value.tzinfo)
                # print vars(ve.dtstart.value.tzinfo)

                start = ve.dtstart.value.isoformat()
                if isinstance(ve.dtstart.value, datetime):
                    event['start'] = { 'dateTime' : start,
                                       'timeZone' : self.cals[0]['timeZone'] }
                                       #'timeZone' : ve.dtstart.value.tzinfo._tzid }
                else:
                    event['start'] = { 'date': start }

                if reminder:
                    event['reminders'] = {'useDefault' : False,
                                          'overrides'  : [{'minutes' : reminder,
                                                           'method'  : 'popup'}]}

                # Can only have an end if we have a start, but not the other way
                # around apparently...  If there is no end, use the start date
                if hasattr(ve, 'dtend') and ve.dtend.value:
                    end   = ve.dtend.value.isoformat()
                    if isinstance(ve.dtend.value, datetime):
                        event['end']   = { 'dateTime' : end,
                                           'timeZone' : self.cals[0]['timeZone'] }
                                           #'timeZone' : ve.dtend.value.tzinfo._tzid }
                    else:
                        event['end'] = { 'date': end }

                else:
                    event['end'] = event['start']

            if hasattr(ve, 'description') and ve.description.value.strip():
                descr = ve.description.value.strip()
                DebugPrint("DESCRIPTION: %s\n" % descr)
                if verbose:
                    print "Description:\n%s" % descr
                event['description'] = descr

            if hasattr(ve, 'organizer'):
                DebugPrint("ORGANIZER: %s\n" % ve.organizer.value)

                if ve.organizer.value.startswith("MAILTO:"):
                    email = ve.organizer.value[7:]
                else:
                    email = ve.organizer.value
                if verbose:
                    print "organizer:\n %s" % email
                event['organizer'] = { 'displayName' : ve.organizer.name,
                                       'email'       : email }

            if hasattr(ve, 'attendee_list'):
                DebugPrint("ATTENDEE_LIST : %s\n" % ve.attendee_list)
                if verbose:
                    print "attendees:"
                event['attendees'] = []
                for attendee in ve.attendee_list:
                    if attendee.value.upper().startswith("MAILTO:"):
                        email = attendee.value[7:]
                    else:
                        email = attendee.value
                    if verbose:
                        print " %s" % email

                    event['attendees'].append({ 'displayName' : attendee.name,
                                                'email'       : email })

            return event

        try:
            import vobject
        except:
            PrintErrMsg('Python vobject module not installed!\n')
            sys.exit(1)

        if dump:
            verbose = True

        if not dump and len(self.cals) != 1:
            PrintErrMsg("Must specify a single calendar\n")
            return

        f = sys.stdin

        if icsFile:
            try:
                f = file(icsFile)
            except Exception, e:
                PrintErrMsg("Error: " + str(e) + "!\n")
                sys.exit(1)

        while True:

            try:
                v = vobject.readComponents(f).next()
            except StopIteration:
                break

            #v.prettyPrint()

            for ve in v.vevent_list:

                event = CreateEventFromVOBJ(ve)

                if not event:
                    continue

                if dump:
                    continue

                if not verbose:
                    newEvent = self._CalService().events().\
                               insert(calendarId = self.cals[0]['id'],
                                      body = event).execute()
                    hLink = self._ShortenURL(newEvent['htmlLink'])
                    PrintMsg(CLR_GRN(), 'New event added: %s\n' % hLink)
                    continue

                #dprint(event)
                PrintMsg(CLR_MAG(), "\n[S]kip [i]mport [q]uit: ")
                val = raw_input()
                if not val or val.lower() == 's':
                    continue
                if val.lower() == 'i':
                    newEvent = self._CalService().events().\
                               insert(calendarId = self.cals[0]['id'],
                                      body = event).execute()
                    hLink = self._ShortenURL(newEvent['htmlLink'])
                    PrintMsg(CLR_GRN(), 'New event added: %s\n' % hLink)
                elif val.lower() == 'q':
                    sys.exit(0)
                else:
                    PrintErrMsg('Error: invalid input\n')
                    sys.exit(1)

def GetColor(value):
    colors = { 'default'       : CLR_NRM(),
               'black'         : CLR_BLK(),
               'brightblack'   : CLR_BRBLK(),
               'red'           : CLR_RED(),
               'brightred'     : CLR_BRRED(),
               'green'         : CLR_GRN(),
               'brightgreen'   : CLR_BRGRN(),
               'yellow'        : CLR_YLW(),
               'brightyellow'  : CLR_BRYLW(),
               'blue'          : CLR_BLU(),
               'brightblue'    : CLR_BRBLU(),
               'magenta'       : CLR_MAG(),
               'brightmagenta' : CLR_BRMAG(),
               'cyan'          : CLR_CYN(),
               'brightcyan'    : CLR_BRCYN(),
               'white'         : CLR_WHT(),
               'brightwhite'   : CLR_BRWHT(),
               None            : CLR_NRM() }

    if value in colors:
        return colors[value]
    else:
        return None

def GetCalColors(calNames):
    calColors = {}
    for calName in calNames:
        calNameParts = calName.split("#")
        calNameSimple = calNameParts[0]
        calColor = calColors.get(calNameSimple)
        if len(calNameParts) > 0:
            calColorRaw = calNameParts[-1]
            calColorNew = GetColor(calColorRaw)
            if calColorNew is not None:
                calColor = calColorNew
        calColors[calNameSimple] = calColor
    return calColors


FLAGS = gflags.FLAGS
# allow mixing of commands and options
FLAGS.UseGnuGetOpt()

gflags.DEFINE_bool("help", None, "Show this help")
gflags.DEFINE_bool("helpshort", None, "Show command help only")
gflags.DEFINE_bool("version", False, "Show the version and exit")

gflags.DEFINE_string("client_id", __API_CLIENT_ID__, "API client_id")
gflags.DEFINE_string("client_secret", __API_CLIENT_SECRET__, "API client_secret")

gflags.DEFINE_string("configFolder", None, "Optional directory to load/store all configuration information")
gflags.DEFINE_bool("includeRc", False, "Whether to include ~/.gcalclirc when using configFolder")
gflags.DEFINE_multistring("calendar", [], "Which calendars to use")
gflags.DEFINE_bool("military", False, "Use 24 hour display")

# Single --detail that allows you to specify what parts you want
gflags.DEFINE_multistring("details", [], "Which parts to display, can be: "
                          "'all', 'calendar', 'location', 'length', "
                          "'reminders', 'description', 'longurl', 'shorturl', "
                          "'url'")
# old style flags for backwards compatibility
gflags.DEFINE_bool("detail_all", False, "Display all details")
gflags.DEFINE_bool("detail_calendar", False, "Display calendar name")
gflags.DEFINE_bool("detail_location", False, "Display event location")
gflags.DEFINE_bool("detail_length", False, "Display length of event")
gflags.DEFINE_bool("detail_reminders", False, "Display reminders")
gflags.DEFINE_bool("detail_description", False, "Display description")
gflags.DEFINE_integer("detail_description_width", 80, "Set description width")
gflags.DEFINE_enum("detail_url", None, ["long", "short"], "Set URL output")

gflags.DEFINE_bool("tsv", False, "Use Tab Seperated Value output")
gflags.DEFINE_bool("started", True, "Show events that have started")
gflags.DEFINE_integer("width", 10, "Set output width", short_name="w")
gflags.DEFINE_bool("monday", False, "Start the week on Monday")
gflags.DEFINE_bool("color", True, "Enable/Disable all color output")
gflags.DEFINE_bool("lineart", True, "Enable/Disable line art")
gflags.DEFINE_bool("conky", False, "Use Conky color codes")

gflags.DEFINE_string("color_owner", "cyan", "Color for owned calendars")
gflags.DEFINE_string("color_writer", "green", "Color for writable calendars")
gflags.DEFINE_string("color_reader", "magenta", "Color for read-only calendars")
gflags.DEFINE_string("color_freebusy", "default", "Color for free/busy calendars")
gflags.DEFINE_string("color_date", "yellow", "Color for the date")
gflags.DEFINE_string("color_now_marker", "brightred", "Color for the now marker")
gflags.DEFINE_string("color_border", "white", "Color of line borders")

gflags.DEFINE_string("locale", None, "System locale")

gflags.DEFINE_integer("reminder", None, "Reminder minutes")
gflags.DEFINE_string("title", None, "Event title")
gflags.DEFINE_string("where", None, "Event location")
gflags.DEFINE_string("when", None, "Event time")
gflags.DEFINE_integer("duration", None, "Event duration")
gflags.DEFINE_string("description", None, "Event description")
gflags.DEFINE_bool("prompt", True, "Prompt for missing data when adding events")

gflags.DEFINE_bool("iamaexpert", False, "Probably not")
gflags.DEFINE_bool("refresh", False, "Delete and refresh cached data")
gflags.DEFINE_bool("cache", True, "Execute command without using cache")

gflags.DEFINE_bool("verbose", False, "Be verbose on imports", short_name="v")
gflags.DEFINE_bool("dump", False, "Print events and don't import", short_name="d")

gflags.RegisterValidator("details",
                        lambda value: all(x in ["all", "calendar",
                           "location", "length", "reminders", "descr",
                           "longurl", "shorturl", "url"] for x in value))
gflags.RegisterValidator("color_owner",
                         lambda value: GetColor(value) != None)
gflags.RegisterValidator("color_writer",
                         lambda value: GetColor(value) != None)
gflags.RegisterValidator("color_reader",
                         lambda value: GetColor(value) != None)
gflags.RegisterValidator("color_freebusy",
                         lambda value: GetColor(value) != None)
gflags.RegisterValidator("color_date",
                         lambda value: GetColor(value) != None)
gflags.RegisterValidator("color_now_marker",
                         lambda value: GetColor(value) != None)
gflags.RegisterValidator("color_border",
                         lambda value: GetColor(value) != None)

gflags.ADOPT_module_key_flags(gflags)

def BowChickaWowWow():
    try:
        argv = sys.argv
        if os.path.exists(os.path.expanduser('~/.gcalclirc')):
            # We want .gcalclirc to be sourced before any other --flagfile params
            # Since we may be told to use a specific config folder, we need to
            # store generated argv in temp variable
            tmpArgv = [argv[0], "--flagfile=~/.gcalclirc"] + argv[1:]
        else:
            tmpArgv = argv
        args = FLAGS(tmpArgv)
    except gflags.FlagsError, e:
        PrintErrMsg(str(e))
        Usage(True)
        sys.exit(1)

    if FLAGS.configFolder:
        if not os.path.exists(os.path.expanduser(FLAGS.configFolder)):
            os.makedirs(os.path.expanduser(FLAGS.configFolder))
        if os.path.exists(os.path.expanduser("%s/gcalclirc" % FLAGS.configFolder)):
            if not FLAGS.includeRc:
                tmpArgv = argv + ["--flagfile=%s/gcalclirc" % FLAGS.configFolder, ]
            else:
                tmpArgv += ["--flagfile=%s/gcalclirc" % FLAGS.configFolder, ]

        FLAGS.Reset()
        args = FLAGS(tmpArgv)

    argv = tmpArgv

    if FLAGS.version:
        Version()

    if FLAGS.help:
        Usage(True)
        sys.exit()

    if FLAGS.helpshort:
        Usage()
        sys.exit()

    if not FLAGS.color:
        CLR.useColor = False

    if not FLAGS.lineart:
        ART.useArt = False

    if FLAGS.conky:
        SetConkyColors()

    if FLAGS.locale:
        try:
            locale.setlocale(locale.LC_ALL, FLAGS.locale)
        except Exception, e:
            PrintErrMsg("Error: " + str(e) + "!\n" +
                        "Check supported locales of your system.\n")
            sys.exit(1)


    # pop executable off the stack
    args = args[1:]
    if len(args) == 0:
        PrintErrMsg('Error: no command\n')
        sys.exit(1)

    # No sense instaniating gcalcli for nothing
    if not args[0] in ['list', 'search', 'agenda', 'csv', 'calw', 'calm', 'quick',
        'add', 'delete', 'edit', 'remind', 'import', 'help']:
        PrintErrMsg('Error: %s is an invalid command' % args[0])
        sys.exit(1)

    # all other commands require gcalcli be brought up
    if args[0] == 'help':
        Usage()
        sys.exit(0)

    calNames = []
    calNameColors = []
    calColors = GetCalColors(FLAGS.calendar)
    calNamesFiltered = []
    for calName in FLAGS.calendar:
        calNameSimple = calName.split("#")[0]
        calNamesFiltered.append(calNameSimple)
        calNameColors.append(calColors[calNameSimple])
    calNames = calNamesFiltered

    if 'all' in FLAGS.details or FLAGS.detail_all:
        if not FLAGS['detail_calendar'].present: FLAGS['detail_calendar'].value = True
        if not FLAGS['detail_location'].present: FLAGS['detail_location'].value = True
        if not FLAGS['detail_length'].present: FLAGS['detail_length'].value = True
        if not FLAGS['detail_reminders'].present: FLAGS['detail_reminders'].value = True
        if not FLAGS['detail_description'].present: FLAGS['detail_description'].value = True
        if not FLAGS['detail_url'].present: FLAGS['detail_url'].value = "long"
    else:
        if 'calendar' in FLAGS.details:
            FLAGS['detail_calendar'].value = True
        if 'location' in FLAGS.details:
            FLAGS['detail_location'].value = True
        if 'length' in FLAGS.details:
            FLAGS['detail_length'].value = True
        if 'reminders' in FLAGS.details:
            FLAGS['detail_reminders'].value = True
        if 'description' in FLAGS.details:
            FLAGS['detail_description'].value = True
        if 'longurl' in FLAGS.details or 'url' in FLAGS.details:
            FLAGS['detail_url'].value = 'long'
        elif 'shorturl' in FLAGS.details:
            FLAGS['detail_url'].value = 'short'

    gcal = gcalcli(calNames=calNames,
                   calNameColors=calNameColors,
                   military=FLAGS.military,
                   detailCalendar=FLAGS.detail_calendar,
                   detailLocation=FLAGS.detail_location,
                   detailLength=FLAGS.detail_length,
                   detailReminders=FLAGS.detail_reminders,
                   detailDescr=FLAGS.detail_description,
                   detailDescrWidth=FLAGS.detail_description_width,
                   detailUrl=FLAGS.detail_url,
                   ignoreStarted=not FLAGS.started,
                   calWidth=FLAGS.width,
                   calMonday=FLAGS.monday,
                   calOwnerColor=GetColor(FLAGS.color_owner),
                   calWriterColor=GetColor(FLAGS.color_writer),
                   calReaderColor=GetColor(FLAGS.color_reader),
                   calFreeBusyColor=GetColor(FLAGS.color_freebusy),
                   dateColor=GetColor(FLAGS.color_date),
                   nowMarkerColor=GetColor(FLAGS.color_now_marker),
                   borderColor=GetColor(FLAGS.color_border),
                   tsv=FLAGS.tsv,
                   refreshCache=FLAGS.refresh,
                   useCache=FLAGS.cache,
                   configFolder=FLAGS.configFolder,
                   client_id=FLAGS.client_id,
                   client_secret=FLAGS.client_secret
                   )

    if args[0] == 'list':
        gcal.ListAllCalendars()

    elif args[0] == 'search':
        if len(args) != 2:
            PrintErrMsg('Error: invalid search string\n')
            sys.exit(1)

        # allow unicode strings for input
        gcal.TextQuery(unicode(args[1], locale.getpreferredencoding() or "UTF-8"))

        sys.stdout.write('\n')

    elif args[0] == 'agenda':
        if len(args) == 3: # start and end
            # TODO; get the start_date from tkinter
            gcal.AgendaQuery(startText=start_date, endText=end_date)
            gcal.AgendaQuery(startText=args[1], endText=args[2])
        elif len(args) == 2: # start
            #gcal.AgendaQuery(startText=start_date)
            gcal.AgendaQuery(startText=args[1])
        elif len(args) == 1: # defaults
            gcal.AgendaQuery()
        else:
            PrintErrMsg('Error: invalid agenda arguments\n')
            sys.exit(1)

        if not FLAGS.tsv:
            sys.stdout.write('\n')

    elif args[0] == 'csv':
        if len(args) == 3: # start and end
            # get the end_date from tkinter
            gcal.AgendaQuery(startText=str(start_date), endText=str(end_date))
            #gcal.AgendaQuery(startText=args[1], endText=args[2])
        else:
            PrintErrMsg('Error: invalid csv arguments\n')
            sys.exit(1)


    elif args[0] == 'calw':
        if not FLAGS.width:
            PrintErrMsg('Error: invalid width, don\'t be an idiot!\n')
            sys.exit(1)

        if len(args) >= 2:
            try:
                count = int(args[1])
            except:
                PrintErrMsg('Error: invalid calw arguments\n')
                sys.exit(1)

        if len(args) == 3: # weeks and start
            gcal.CalQuery(args[0], count=int(args[1]), startText=args[2])
        elif len(args) == 2: # weeks
            gcal.CalQuery(args[0], count=int(args[1]))
        elif len(args) == 1: # defaults
            gcal.CalQuery(args[0])
        else:
            PrintErrMsg('Error: invalid calw arguments\n')
            sys.exit(1)

        sys.stdout.write('\n')

    elif args[0] == 'calm':
        if not FLAGS.width:
            PrintErrMsg('Error: invalid width, don\'t be an idiot!\n')
            sys.exit(1)

        if len(args) == 2: # start
            gcal.CalQuery(args[0], startText=args[1])
        elif len(args) == 1: # defaults
            gcal.CalQuery(args[0])
        else:
            PrintErrMsg('Error: invalid calm arguments\n')
            sys.exit(1)

        sys.stdout.write('\n')

    elif args[0] == 'quick':
        if len(args) != 2:
            PrintErrMsg('Error: invalid event text\n')
            sys.exit(1)

        # allow unicode strings for input
        gcal.QuickAddEvent(unicode(args[1], locale.getpreferredencoding() or "UTF-8"),
                           reminder=FLAGS.reminder)

    elif (args[0] == 'add'):
        if FLAGS.title == None and FLAGS.prompt:
            PrintMsg(CLR_MAG(), "Title: ")
            FLAGS.title = raw_input()
        if FLAGS.where == None and FLAGS.prompt:
            PrintMsg(CLR_MAG(), "Location: ")
            FLAGS.where = raw_input()
        if FLAGS.when == None and FLAGS.prompt:
            PrintMsg(CLR_MAG(), "When: ")
            FLAGS.when = raw_input()
        if FLAGS.duration == None and FLAGS.prompt:
            PrintMsg(CLR_MAG(), "Duration (mins): ")
            FLAGS.duration = raw_input()
        if FLAGS.description == None and FLAGS.prompt:
            PrintMsg(CLR_MAG(), "Description: ")
            FLAGS.description = raw_input()
        if FLAGS.reminder == None and FLAGS.prompt:
            PrintMsg(CLR_MAG(), "Reminder (mins): ")
            FLAGS.reminder = raw_input()

        # calculate "when" time:
        eStart, eEnd = GetTimeFromStr(FLAGS.when, FLAGS.duration)

        gcal.AddEvent(FLAGS.title, FLAGS.where, eStart, eEnd, FLAGS.description, FLAGS.reminder)

    elif args[0] == 'delete':
        if len(args) != 2:
            PrintErrMsg('Error: invalid search string\n')
            sys.exit(1)

        # allow unicode strings for input
        gcal.DeleteEvents(unicode(args[1], locale.getpreferredencoding() or "UTF-8"),
                          FLAGS.iamaexpert)

        sys.stdout.write('\n')

    elif args[0] == 'edit':
        if len(args) != 2:
            PrintErrMsg('Error: invalid search string\n')
            sys.exit(1)

        # allow unicode strings for input
        gcal.EditEvents(unicode(args[1], locale.getpreferredencoding() or "UTF-8"))

        sys.stdout.write('\n')

    elif args[0] == 'remind':
        if len(args) == 3: # minutes and command
            gcal.Remind(int(args[1]), args[2])
        elif len(args) == 2: # minutes
            gcal.Remind(int(args[1]))
        elif len(args) == 1: # defaults
            gcal.Remind()
        else:
            PrintErrMsg('Error: invalid remind arguments\n')
            sys.exit(1)

    elif args[0] == 'import':
        if len(args) == 1: # stdin
            gcal.ImportICS(FLAGS.verbose, FLAGS.dump, FLAGS.reminder)
        elif len(args) == 2: # ics file
            gcal.ImportICS(FLAGS.verbose, FLAGS.dump, FLAGS.reminder, args[1])
        else:
            PrintErrMsg('Error: invalid import arguments\n')
            sys.exit(1)

def makeent(root, field, showAss=False):
    row = Frame(root)
    # TODO; if name includes "Date" make it a date field. tkinter doesn't have date picker I might roll my own.
    # TODO; if name is "Message" make it multi-line.
    #user = makeentry(parent, "User name:", 10)
    #password = makeentry(parent, "Password:", 10, show="*")
    lab = Label(row, width=22, text=field+": ", anchor='w')
    if showAss:
        ent = Entry(row, width=50, show='*')
    else:
        ent = Entry(row, width=50)
    #s1 = "Entry(row, width=50" + entryOpt + ")"
    #s2 = exec("print(s1)")
    #ent = exec(s1)
    #ent = Entry(row, width=50)
    ent.insert(0,"")
    row.pack(side=TOP, fill=X, padx=5, pady=5)
    lab.pack(side=LEFT)
    ent.pack(side=RIGHT, expand=YES, fill=X)
    return ent

def update_status(entries, status_description):
    entries['Status'].delete(0,END)
    entries['Status'].insert(0, status_description )
    print("Status: %s" % status_description)

def update_message(entries, message_description):
    entries['Message'].delete(0,END)
    entries['Message'].insert(0, message_description)
    print("Message: %s" % message_description)

def get_events(entries):
    global start_date
    global end_date
    global search_string
    global destination_file #= "t1.csv"

    update_status(ents, "Processing...")
    # TODO; status isn't updated until this is done, this should be multiprocessing?
    # Like: http://stackoverflow.com/questions/16699682/python-tkinter-status-bar-not-updating-correctly
    try:
        # get values from user
        account = entries['Google Account'].get()
        password = entries['Google Account Password'].get()
        #show_password = entries['Show Password'].get()
        d1 = entries['Start Date'].get()
        start_date = datetime.strptime(d1, '%Y-%m-%d')
        #start_date = datetime.datetime.strptime(d1, '%Y-%m-%d')
        #start_date = datetime.datetime.strptime(d1, '%m/%d/%Y')
        d1 = entries['End Date'].get()
        # change end_date to day+1 or time to 23:59:59
        end_date = datetime.strptime(d1, '%Y-%m-%d')+timedelta(days=1)
        #end_date = datetime.datetime.strptime(d1, '%Y-%m-%d')+datetime.timedelta(days=1)
        #end_date = datetime.datetime.strptime(d1+datetime.timedelta(days=1), '%Y-%m-%d')
        #end_date = datetime.datetime.strptime(d1, '%m/%d/%Y')
        search_string = unicode(entries['Search String'].get())
        destination_file = entries['Destination File'].get()
        print (account, start_date, end_date, search_string, destination_file)
        #print (account, password, show_password, start_date, end_date, search_string, destination_file)

        BowChickaWowWow()

        # validate date fields since I don't have a date picker yet.
        # get events from Google
        #token = google_calendar_fetcher.login(account,password)
        #try:
        #    google_calendar_fetcher.get_calendars(token, start_date, end_date, search_string, destination_file)
        #    # filter events by Start Date, End Date and Search String.
        #    google_calendar_fetcher.printOut(destination_file)
        #   #google_calendar_fetcher.print_output()
        #except:
        #    exc_type, exc_value, exc_traceback = sys.exc_info()
        #    update_message(entries, exc_value)
        #    traceback.print_exc()

        #client = gdata.calendar.client.CalendarClient(source='yourCo-yourAppName-v1')
        #client.ClientLogin(account, password, client.source)
        #PrintUserCalendars(client)
        # TODO; show events to user
        pass
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        update_message(entries, exc_value)
        traceback.print_exc()
        #print exc_type
        #print exc_value
        #print exc_traceback
    update_status(ents, "Waiting for entry...")

def makeform(root):
    account_password_dates_fields = ('Status',
        'Message',
        'Start Date',
        'End Date',
        'Search String',
        'Destination File',
        'Google Account',
    )
    #    'Google Account Password',
    entries = {}
    for field in account_password_dates_fields:
        entries[field] = makeent(root, field)
    s1 = 'Google Account Password'
    entries[s1] = makeent(root,s1, showAss=True)
    return entries

def func(event):
    #print("You hit return.")
    get_events(ents)

def SIGINT_handler(signum, frame):
    PrintErrMsg('Signal caught, bye!\n')
    sys.exit(1)

signal.signal(signal.SIGINT, SIGINT_handler)

if __name__ == '__main__':
    # isn't there a more generic way to do this? Then this could be in google_calendar_API-V3.py.
    dE = date.today() - timedelta(days=1)
    dS = dE - timedelta(days=6)
    sys.argv = [sys.argv[0], 'csv', str(dS), str(dE)] # Force csv output.
    # Check date ranges; '2014-11-24', '2014-11-30' got 22nd through 29th
    print (sys.argv[0], 'csv', str(dS), str(dE)) # Force csv output.
    CLR.useColor = False # Don't output any colors.

    # TODO; Is there a button accelerator key for tkinter buttons?
    #       I was not able to get Alt-G or Alt-Q to bind. Something funny is going on.
    #test1=raw_input("gimme something")
    #test2=raw_input("gimme more")
    root = Tk()
    ents = makeform(root)
    #root.bind('<Return>', (get_events(root)))
    # Catch ENTER from form and don't generate an error.
    root.bind('<Return>', func)
    # ENTER goes to tkinter.__init__.CallWrapper.__call__ when not bound to something.
    #root.bind('<Return>', (lambda event, e=ents: e.get()))
    #root.bind('<Return>', (lambda event, e=ents: fetch(e)))
    update_status(ents, "Starting...")
    b1 = Button(root, text='Get Events', command=(lambda e=ents: get_events(e)))
    #b1 = Button(root, text='Get Events', command=(lambda e=ents: get_events(e)), underline=0)
    b1.pack(side=LEFT, padx=5, pady=5)
    #root.bind('<Alt-G>', func1)
    #root.bind('<Shift-G>', func1)
    #root.bind('<Control-G>', func1)
    #b2 = Button(root, text='Monthly Payment', command=(lambda e=ents: monthly_payment(e)))
    #b2.pack(side=LEFT, padx=5, pady=5)
    b3 = Button(root, text='Quit', command=root.quit)
    #b3 = Button(root, text='Quit', command=root.quit, underline=0)
    b3.pack(side=LEFT, padx=5, pady=5)
    #root.bind('<Alt-Q>', func2)
    update_status(ents, "Waiting for entry...")
    update_message(ents, "Enter dates as yyyy-mm-dd!")
    # TODO; figure out a way to keep the Google account password secret.
    s1 = """
          google pycharm security passwords
            python master password database
                http://stackoverflow.com/questions/12042724/securely-storing-passwords-for-use-in-python-script
                http://stackoverflow.com/questions/7014953/i-need-to-securely-store-a-username-and-password-in-python-what-are-my-options
                https://docs.python.org/2/library/getpass.html
                https://charlesleifer.com/blog/creating-a-personal-password-manager/
            python Creating a personal password manager
            PyCharm password database
        Something creates a sqlite db and that could be my answer if encrypted.
            Django project.
    """
    ents['Google Account'].delete(0,END)
    ents['Google Account'].insert(0, "DaleEMoore")
    #ents['Google Account'].insert(0, "MooreWorksService")
    ents['Google Account Password'].delete(0,END)
    #ents['Google Account Password'].insert(0,END, "password")
    #ents['Show Password'].delete(0,END)
    #ents['Show Password'].insert(0, "No")
    ents['Start Date'].delete(0,END)
    # Start Date endDate - 6 days.
    ents['End Date'].delete(0,END)

    # End Date is yesterday.
    dE = date.today() - timedelta(days=1)
    dS = dE - timedelta(days=6)
    #dE = datetime.date.today() - datetime.timedelta(days=1)
    #dow = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ##       0         1          2            3           4         5           6
    ## date.weekday(); Monday is 0 and Sunday is 6
    #dS = dE - datetime.timedelta(days=6)
    ents['End Date'].insert(0, dE)
    ents['Start Date'].insert(0, dS)
    ents['Search String'].delete(0,END)
    ents['Search String'].insert(0, "Bill")
    ents['Destination File'].delete(0,END)
    ents['Destination File'].insert(0, "t1.csv")

    ents['Google Account Password'].focus()

    root.mainloop() # get_events() called when button pushed

    #BowChickaWowWow()
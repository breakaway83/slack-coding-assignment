import sys
import os
import httplib
from datetime import datetime
import logging
import socket
import re
from optparse import OptionParser
"""
Meta
====
    $Id: //splunk/current/test/lib/util/LogGen.py#13 $
    $DateTime: 2012/07/19 04:12:29 $
    $Author: hchin $
    $Change: 131161 $
"""

# don't change the way we import time, otherwise we'll 
# get errors because of the way mambo imports it
from time import *

class LogGen():
    """
    Generate Log data for real-time testing.
    """
    logger = logging.getLogger('LogGen')

    def __init__(self, log_fh, frequency=1, iterations=None):
        self.log_fh = log_fh
        self.frequency = frequency
        self.iterations = iterations

    def start(self):
        FH = self.log_fh
        print "Starting event writing loop at %s events per second..." % self.frequency
        i = 1
        while self.iterations is None or i <= self.iterations:
            time_str = strftime('%m/%d/%Y %H:%M:%S')
            # Fix SPL-51637: On solaris, error message: [Errno 12] Not enough space
            #events = []
            for j in range(0, int(self.frequency)):
                FH.write("%s event number outer=%s inner=%s\n" % (time_str, i, j))
                #events.append("%s event number outer=%s inner=%s\n" % (time_str, i, j))
                #j+=1
            #FH.write("".join(events))
            i+=1
            sleep(1)
            FH.flush()

class TcpLogGen():
    """
    Send tcp Log data for real-time testing.
    """
    logger = logging.getLogger('LogGen')

    def __init__(self, sendHost, sendPort):
        self.sendHost = sendHost
        self.sendPort = sendPort

    def sendEvents(self, numRandHosts, numEvents, startYear=None, startMonth=None, startDay=None, startHours=None, startMinutes=None, startSeconds=None):
        self.logger.info("Sending %s events to %s:%s" % (numEvents, self.sendHost, self.sendPort))
        if startYear == None:
            s = os.popen('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=tcp -d sendHost=%s -d sendPort=%s http://localhost/~shaoyuliang/datagen/cgi-bin/gen.cgi' % (datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second, numRandHosts, numEvents, self.sendHost, self.sendPort))
            self.logger.info('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=tcp -d sendHost=%s -d sendPort=%s http://localhost/~shaoyuliang/datagen/cgi-bin/gen.cgi' % (datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second, numRandHosts, numEvents, self.sendHost, self.sendPort))
        else:
            s = os.popen('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=tcp -d sendHost=%s -d sendPort=%s http://localhost/~shaoyuliang/datagen/cgi-bin/gen.cgi' % (startYear, startMonth, startDay, startHours, startMinutes, startSeconds, numRandHosts, numEvents, self.sendHost, self.sendPort))
            self.logger.info('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=tcp -d sendHost=%s -d sendPort=%s http://localhost/~shaoyuliang/datagen/cgi-bin/gen.cgi' % (startYear, startMonth, startDay, startHours, startMinutes, startSeconds, numRandHosts, numEvents, self.sendHost, self.sendPort))
        exit = s.read()
        if not exit==None:
             self.logger.info("%s" % exit)
        

    def start(self, frequency, numRandHosts, numEvents, iterations=None):
        self.logger.info("Starting event sending loop at %s events per second..." % frequency)
        i = 1
        while iterations is None or i <= iterations:
            for j in range(0, int(frequency)):
                self.sendEvents(1, 1)
                j+=1
            i+=1
            sleep(1)

class UDPLogGen():
    """
    Send udp Log data for real-time testing.
    """
    logger = logging.getLogger('LogGen')
    
    def __init__(self, sendHost, sendPort):
        self.sendHost = sendHost
        self.sendPort = sendPort
    
    def sendEvents(self, numRandHosts, numEvents, startYear=None, startMonth=None, startDay=None, startHours=None, startMinutes=None, startSeconds=None):
        self.logger.info("Sending %s events to %s:%s" % (numEvents, self.sendHost, self.sendPort))
        if startYear == None:
            s = os.popen('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=udp -d sendHost=%s -d sendPort=%s http://192.168.1.16/~shaoyuliang/datagen/cgi-bin/gen.cgi' % (datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second, numRandHosts, numEvents, self.sendHost, self.sendPort))
            self.logger.info('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=udp -d sendHost=%s -d sendPort=%s http://192.168.1.16/~shaoyuliang/datagen/cgi-bin/gen.cgi' % (datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second, numRandHosts, numEvents, self.sendHost, self.sendPort))
        else:
            s = os.popen('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=udp -d '
            'sendHost=%s -d sendPort=%s http://datagen.splunk.com/cgi-bin/gen.cgi' % (startYear, startMonth, startDay, startHours, startMinutes, startSeconds, numRandHosts, numEvents, self.sendHost, self.sendPort)) 
            self.logger.info('curl -d startYear=%s -d startMonth=%s -d startDay=%s -d startHours=%s -d startMinutes=%s -d startSeconds=%s -d numRandHosts=%s -d numEvents=%s -d encoding=ASCII -d output=udp -d sendHost=%s -d sendPort=%s http://datagen.splunk.com/cgi-bin/gen.cgi' % (startYear, startMonth, startDay, startHours, startMinutes, startSeconds, numRandHosts, numEvents, self.sendHost, self.sendPort))
        exit = s.read()
        if not exit==None:
             self.logger.info("%s" % exit)


    def start(self, frequency, numRandHosts, numEvents, iterations=None):
        self.logger.info("Starting event sending loop at %s events per second..." % frequency)
        i = 1
        while iterations is None or i <= iterations:
            for j in range(0, int(frequency)):
                self.sendEvents(1, 1)
                j+=1
            i+=1
            sleep(1)

class LogReplay():
    """ replays logs for real-time testing """
    logger = logging.getLogger("LogReplay")

    def __init__(self, pattern='~~~%s~~~'):
        self.strPattern = pattern
        self.regexPattern = pattern.replace('%s', r'(\d+)')

    def replayInRealtime(self, dataPath, host, port, timeFormat):
        """ take a data template and replay it in real time, with replaced
        timestamps """

        # connect to tcp output
#        af, socktype, proto, cannonname, sa = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        sock = socket.socket()
        
        try:
            sock.connect((host, port))
            self.logger.info("Established connection to (%s, %s)" % (host, port))

            try:
                template = open(dataPath, 'rb')
                seq = 0
                eventlist = ""
                eventtime = localtime()
                for i, line in enumerate(template):
                    mo = re.search(self.regexPattern, line)
                    if not mo:
                        # assume we're still in the middle of an event, part of the current
                        # seq number, just add to the eventlist
                        eventlist += line
                        continue
                    
                    if int(mo.group(1)) == seq:
                        eventlist += line.replace(mo.group(0), strftime(timeFormat, eventtime))
                    elif int(mo.group(1)) > seq:
                        # send the events if we're on to the next seq
                        if len(eventlist) > 0:
                            sock.sendall(eventlist)
                        # update eventtime, eventlist
                        sleep(int(mo.group(1)) - seq)
                        seq = int(mo.group(1))
                        eventtime = localtime()
                        eventlist = line.replace(mo.group(0), strftime(timeFormat, eventtime))
                    else:
                        # it's out of order add it to the queue
                        delta = seq - int(mo.group(1))
                        eventlist += line.replace(mo.group(0), strftime(timeFormat, localtime(mktime(eventtime)-delta)))
                else:
                    # send any leftover events
                    if len(eventlist) > 0:
                        sock.sendall(eventlist)
            except Exception:
                raise
            finally:
                template.close()
        except Exception:
            raise
        finally:
            sock.close()

    def createTemplate(self, orig, template, dtRegex, timeFormat):
        """ take a log file and use it to create a data template which can
        be replayed with replayInRealtime.  dtRegex is a regex with
        matching group named datetime for the date time portion of the
        regex (shouldn't include milliseconds)
        ex. Date: (?P<datetime>\d{4}-\d{2}-\d{2}:\d{2}:\d{2}:\d{2}).\d{3}
        timeFormat is the strptime format (also without milliseconds)
        """

        try:
            origFH = open(orig, 'rb')
            templateFH = open(template, 'wb')
            seq = 0
            currentDt = 0
            for i, line in enumerate(origFH):
                mo = re.search(dtRegex, line)
                if not mo:
                    # assume we're still in the middle of an event, part of the
                    # current seq number
                    templateFH.write(line)
                    continue

                eventtime = mktime(strptime(mo.group("datetime"), timeFormat))
                if currentDt == 0:
                    currentDt = eventtime
                
                if (eventtime == currentDt):
                    templateFH.write(line.replace(mo.group("datetime"), self.strPattern % seq))

                elif (eventtime > currentDt):
                    seq += int(eventtime - currentDt)
                    templateFH.write(line.replace(mo.group("datetime"), self.strPattern % seq))
                    currentDt = eventtime
                else:
                    # out of order, add it anyways but don't update seq
                    # or currentDt
                    oooSeq = seq - (currentDt - eventtime)
                    templateFH.write(line.replace(mo.group("datetime"), self.strPattern % oooSeq))
            else:
                templateFH.flush()
        except Exception:
            raise
        finally:
            if origFH:
                origFH.close()
            if templateFH:
                templateFH.close()
        self.logger.info("Template file created: %s" % template)

        
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-t', '--type', dest="loggen_type", default="regular", help="type of log generation, regular or replay. defaults to regular")
    parser.add_option('-f', '--frequency', dest='frequency', default=1, help="number of events per second")
    parser.add_option('-T', '--template', dest='template', help="template file to use")
    parser.add_option('-H', '--host', dest='host', help="tcp host for replaying data")
    parser.add_option('-p', '--port', dest='port', help="tcp port for replaying data")
    parser.add_option('-x', '--timeformat', dest='timeformat', help='strptime format to be used during replay of data')
                     

    (options, args) = parser.parse_args()

    if options.loggen_type.lower() == 'regular':
        filename = 'realtime.log'
        frequency = int(options.frequency)
        print "\nWriting events to file: '%s'" % filename
        try:
            FH = open(filename, 'a')
            lg = LogGen(FH, frequency)
            lg.start()
        except (KeyboardInterrupt, SystemExit):
            print "\nCTR-C detected."
        except Exception, e:
            print "\nException detected."
            print e.message
        finally:
            print "\nClosing file...\n"
            FH.close()
    elif options.loggen_type.lower() == 'replay':
        template = options.template
        host = options.host
        port = int(options.port)
        tformat = options.timeformat
        lr = LogReplay()
        
        try:
            while True:
                lr.replayInRealtime(template, host, port, tformat)
        except (KeyboardInterrupt, SystemExit):
            print "\nCTR-C detected."
        except Exception, e:
            print "\nException detected."
            print e
    else:
        sys.exit("Log generation type must be either regular or replay: loggen_type=%s" % options.loggen_type.lower())

        
    


import datetime
import gzip
import math
import re
import threading
import time
import tworkers
import workers


class LogReplay(object):

    def __init__(self):
        self.report_data = {}
        self.report_data['GOOD'] = 0
        self.report_data['BAD'] = 0
        self.initial = 0
        self.regex = re.compile("")
        self.FILES = ()

    def parse_args(self):
        raise NotImplementedError()

    def collect_data(self, line):
        raise NotImplementedError()

    def go(self):
        self.loadLogs()
        self.startTime = time.time()
        self.replayLog()
        self.report()

    def loadLogs(self):
        for log in self.FILES:
            print "Reading: " + log
            if re.match("^.*\.gz$", log):
                f = gzip.open(log, 'r').readlines()
            else:
                f = open(log, 'r').readlines()
            for line in f:
                self.collect_data(line)
            print "Done reading"

    def replayLog(self):
        raise NotImplementedError()

    def report(self):
        raise NotImplementedError()


class TwistedTest(LogReplay):

    def __init__(self, options):
        super(TwistedTest, self).__init__()
        self.report_data['start_end_times'] = []
        self.log_entries = []
        self.THREADCOUNT = options.t
        self.HOST = options.H
        self.FILES = options.f
        self.PREFIX = options.p
        self.IP = options.i
        self.PORT = options.port
        self.AUTH = options.P
        self.regex = re.compile("(\d\d/\w{3}/\d{4}:\d\d:\d\d:\d\d).*\"GET (/.*?) HTTP.*?\"")

    def report(self):
        self.report_data['start_end_times'].sort(cmp=lambda x, y: cmp(x[1] - x[0], y[1] - y[0]))
        self.report_data['start_end_times'] = self.report_data['start_end_times'][:int(len(self.report_data['start_end_times']) * .95)]
        requesttimes = [(j - i) * 1000 for i, j in self.report_data['start_end_times']]
        total_requests = len(requesttimes)
        start_time = min(i for i, j in self.report_data['start_end_times'])
        end_time = max(j for i, j in self.report_data['start_end_times'])
        max_time = max(requesttimes)
        min_time = min(requesttimes)
        avg_time = sum(requesttimes) / total_requests
        std_dev = math.sqrt(sum((i - avg_time) ** 2 for i in requesttimes) / total_requests)
        print "Good: " + str(self.report_data['GOOD'])
        print "Max/Avg/Min/StdDev: %dms/%dms/%dms/%dms" % (max_time, avg_time, min_time, std_dev)
        print "Bad: " + str(self.report_data['BAD'])
        print "Total Time: " + str(end_time - start_time)
        print "Req/s: " + str(total_requests / (end_time - start_time))

    def collect_data(self, line):
        try:
            line_search = self.regex.search(line)
        except:
            pass
        if not line_search:
            return
        self.log_entries.append(self.PREFIX + line_search.group(2))
        return

    def replayLog(self):
        f = tworkers.QuickTesterFactory(
            ip=self.IP, port=self.PORT, url="http://" + self.HOST + "/",
            requests=self.log_entries, report=self.report_data,
            auth=self.AUTH)
        try:
            f.start(self.THREADCOUNT)
        except KeyboardInterrupt:
            f.stop()
        self.endTime = time.time()


class DefaultTest(LogReplay):

    def __init__(self, options):
        # Just get the URL
        super(DefaultTest, self).__init__()
        self.log_entries = {}
        self.THREADCOUNT = options.t
        self.HOST = options.H
        self.FILES = options.f
        self.IP = options.i
        self.PORT = options.port
        self.regex = re.compile("(\d\d/\w{3}/\d{4}:\d\d:\d\d:\d\d).*\"(GET /.* HTTP.*?)\"")

    def report(self):
        print "Good: " + str(self.report_data['GOOD'])
        print "Bad: " + str(self.report_data['BAD'])
        print "Total Time: " + str(self.endTime - self.startTime)
        print "Req/s: " + str(float(self.report_data['GOOD']) / (self.endTime - self.startTime))

    def collect_data(self, line):
        try:
            line_search = self.regex.search(line)
        except:
            pass
        if not line_search:
            return
        time_tuple = time.strptime(line_search.group(1), "%d/%b/%Y:%H:%M:%S")
        date_and_time = datetime.datetime(*time_tuple[:6])
        if self.initial == 0:
            self.initial = date_and_time

        delta = date_and_time - self.initial
        self.log_entries.setdefault(delta.seconds, []).append(line_search.group(2))
        return

    def replayLog(self):
        for i in range(0, max(self.log_entries.keys()) + 1):
            try:
                for a in self.log_entries[i]:
                    while(threading.activeCount() > self.THREADCOUNT):
                        time.sleep(.1)
                    workers.DefaultWorker(a, self.report_data, self.HOST, self.IP, self.PORT).start()
            except KeyError:
                pass
            time.sleep(1)
        while(threading.activeCount() > 1):
            time.sleep(1)
        self.endTime = time.time()


class QuickTest(LogReplay):

    def __init__(self, options):
        # Just get the URL
        super(QuickTest, self).__init__()
        self.log_entries = []
        self.THREADCOUNT = options.t
        self.HOST = options.H
        self.FILES = options.f
        self.PREFIX = options.p
        self.IP = options.i
        self.PORT = options.port
        self.regex = re.compile("(\d\d/\w{3}/\d{4}:\d\d:\d\d:\d\d).*\"GET (/.*) HTTP.*?\"")

    def report(self):
        print "Good: " + str(self.report_data['GOOD'])
        print "Bad: " + str(self.report_data['BAD'])
        print "Total Time: " + str(self.endTime - self.startTime)
        print "Req/s: " + str(float(self.report_data['GOOD']) / (self.endTime - self.startTime))

    def collect_data(self, line):
        try:
            line_search = self.regex.search(line)
        except:
            pass
        if not line_search:
            return
        self.log_entries.append(self.PREFIX + line_search.group(2))
        return

    def replayLog(self):
        try:
                for i in range(0, len(self.log_entries), 10):
                    while(threading.activeCount() > self.THREADCOUNT):
                        time.sleep(.1)
                    workers.DefaultWorker(self.log_entries[i:i + 10], self.report_data, self.HOST, self.IP, self.PORT).start()
                while(threading.activeCount() > 1):
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        self.endTime = time.time()


class NutchTest(LogReplay):

    def __init__(self, options):
        super(NutchTest, self).__init__()
        self.log_entries = []
        self.regex = re.compile("(\w*)")
        self.THREADCOUNT = options.t
        self.HOST = options.H
        self.FILES = options.f

    def report(self):
        print "Good: " + str(self.report_data['GOOD'])
        print "Bad: " + str(self.report_data['BAD'])
        print "Total Time: " + str(self.endTime - self.startTime)
        print "Req/s: " + str(float(self.report_data['GOOD']) / (self.endTime - self.startTime))

    def collect_data(self, line):
        try:
            line_search = self.regex.search(line)
        except:
            pass
        if not line_search:
            return
        self.log_entries.append(line_search.group(1))
        return

    def replayLog(self):
        try:
                for i in range(0, len(self.log_entries), 10):
                    while(threading.activeCount() > self.THREADCOUNT):
                        time.sleep(.1)
                    urls = ["/opensearch?query=site:www.mozilla.com+%s&hitsPerPage=10&hitsPerSite=0&start=0" % t for t in self.log_entries[i:i + 10]]
                    workers.DefaultWorker(urls, self.report_data, self.HOST, self.IP, self.PORT).start()
                while(threading.activeCount() > 1):
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        self.endTime = time.time()

import httplib
import threading


class logWorker(threading.Thread): 

    def __init__(self, addr, rt):
        self.addrs = addr
        self.status = 1
        self.connects = 0
        self.rt = rt
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def make_connection(self):
        raise NotImplementedError()

    def close_connection(self):
        raise NotImplementedError()

    def send_data(self,ad):
        raise NotImplementedError()

    def good(self):
        raise NotImplementedError()

    def bad(self):
        raise NotImplementedError()

    def run(self):
        self.make_connection()
        for ad in self.addrs:
            try:
                self.send_data(ad)
                self.good()
            except:
                self.bad()
                self.close_connection()
        self.close_connection()

class DefaultWorker(logWorker):
    def __init__(self, addr, return_type, host, ip, port):
        self.HOST = host
        self.PORT = port
        if ip:
            self.IP = ip
        else:
            self.IP = host
        self.headers = {"Host": host, "Keep-Alive": 300, "Connection": "keep-alive"}
        logWorker.__init__(self, addr, return_type)

    def make_connection(self):
        self.connects += 1
        self.s = httplib.HTTPConnection(self.IP, self.PORT)

    def close_connection(self):
        self.s.close() 

    def send_data(self,ad):
        self.s.request("GET", ad, None, self.headers)
        response = self.s.getresponse()
        response.read()

    def good(self):
        self.rt['GOOD'] += 1

    def bad(self):
        self.rt['BAD'] += 1
        self.status = 0

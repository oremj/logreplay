import re
import threading
import socket
import httplib
import time, datetime
import sys
import gzip


class logWorker(threading.Thread): 
    def __init__(self,addr,rt):
        self.addrs = addr
        self.status = 1
        self.connects = 0
        self.rt = rt
        threading.Thread.__init__ ( self )
        self.setDaemon(True)
    def make_connection(self): pass
    def close_connection(self): pass
    def send_data(self,ad): pass
    def good(self): pass
    def bad(self): pass
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
    def __init__(self,addr,return_type,host):
        self.HOST = host
        self.headers = {"Host" : host, "Keep-Alive": 300, "Connection" : "keep-alive"}
        logWorker.__init__(self,addr,return_type)
    def make_connection(self):
        self.connects += 1
        self.s = httplib.HTTPConnection(self.HOST)
    def close_connection(self):
        self.s.close() 
    def send_data(self,ad):
        self.s.request("GET",ad,None,self.headers)
        response = self.s.getresponse()
        response.read()

    def good(self):
        self.rt[1] += 1
    def bad(self):
        self.rt[0] += 1
        self.status = 0

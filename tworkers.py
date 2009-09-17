import time
from twisted.web.client import HTTPClientFactory
from twisted.web.http import HTTPClient
from twisted.internet import reactor


class QuickTester(HTTPClient):
    def connectionMade(self):
        self.sendCommand(self.factory.method, self.factory.path)
        self.sendHeader('Host', self.factory.headers.get("host", self.factory.host))
        self.sendHeader('User-Agent', self.factory.agent)
        self.endHeaders()
        self.headers = {}
        self.startTime = time.time()

        data = getattr(self.factory, 'postdata', None)
        if data is not None:
            self.transport.write(data)

    def rawDataReceived(self, line):
        pass

    def handleResponse(self, data):
        end_time = time.time()
        self.factory.report['start_end_times'].append((self.startTime, end_time))
        self.factory.report[1] += 1
        self.factory.nextRequest()



class QuickTesterFactory(HTTPClientFactory):
    protocol = QuickTester

    def __init__(self, **kwargs):
        self.reqs = kwargs['requests']
        self.report = kwargs['report'] 
        self.activecons = 0
        del kwargs['requests']
        del kwargs['report']
        HTTPClientFactory.__init__(self, **kwargs)

    def start(self, num_concurrent):
        for n in range(num_concurrent):
            self.nextRequest() 
        self.report['begin_time'] = time.time()
        reactor.run()

    def startedConnecting(self, connector):
        self.activecons += 1

    def clientConnectionLost(self, connector, reason):
        self.activecons -= 1

    def clientConnectionFailed(self, connector, reason):
        self.activecons -= 1

    def nextRequest(self):
        try:
            self.path = self.reqs.pop() 
            reactor.connectTCP(self.host, 80, self)
        except:
            if self.activecons <= 1:
                self.report['end_time'] = time.time()
                reactor.stop()

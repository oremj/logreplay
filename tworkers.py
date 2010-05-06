import base64
import time

from twisted.web.client import HTTPClientFactory
from twisted.web.http import HTTPClient
from twisted.internet import defer, protocol, reactor


class QuickTester(HTTPClient):
    quietLoss = False

    def connectionMade(self):
        self.path = self.factory.next_path()
        self.sendCommand(self.factory.method, self.path)
        self.sendHeader('Host', self.factory.headers.get("host", self.factory.host))
        self.sendHeader('User-Agent', self.factory.agent)
        self.sendHeader('Authorization', 'Basic %s' % base64.b64encode('support:stage'))
        self.sendHeader('Cookie', 'authtoken=106672_634081562190564790_3c4bf020219c7d1b3df1cd78a49043dc')
        self.endHeaders()
        self.headers = {}
        self.startTime = time.time()
        self.status = None

        data = getattr(self.factory, 'postdata', None)
        if data is not None:
            self.transport.write(data)

    def rawDataReceived(self, line):
        pass

    def handleStatus(self, version, status, message):
        self.status = int(status)

    def handleResponse(self, data):
        if self.quietLoss:
            return
        self.deferred.callback('page')
        end_time = time.time()
        if self.status is None or self.status >= 400:
            self.factory.report['BAD'] += 1
        else:
            self.factory.report['start_end_times'].append((self.startTime, end_time))
            self.factory.report['GOOD'] += 1
        self.factory.nextRequest()

    def timeout(self):
        self.deferred.callback('timeout')
        self.quietLoss = True
        self.factory.report['BAD'] += 1
        self.factory.nextRequest()
        self.transport.loseConnection()


class QuickTesterFactory(HTTPClientFactory):
    protocol = QuickTester

    def __init__(self, **kwargs):
        self.reqs = kwargs.pop('requests')
        self.report = kwargs.pop('report')
        self.ip = kwargs.pop('ip')
        self.host_port = kwargs.pop('port')
        self.activecons = 0
        self.total_reqs = len(self.reqs)
        HTTPClientFactory.__init__(self, timeout=15, **kwargs)

    def start(self, num_concurrent):
        for n in range(num_concurrent):
            self.nextRequest()
        self.report['begin_time'] = time.time()
        reactor.run()

    def stop(self):
        self.report['end_time'] = time.time()
        reactor.stop()

    def buildProtocol(self, addr):
        p = protocol.ClientFactory.buildProtocol(self, addr)
        if self.timeout:
            timeoutCall = reactor.callLater(self.timeout, p.timeout)
            p.deferred = defer.Deferred()
            p.deferred.addBoth(self._cancelTimeout, timeoutCall)
        return p

    def startedConnecting(self, connector):
        self.activecons += 1

    def clientConnectionLost(self, connector, reason):
        self.activecons -= 1

    def clientConnectionFailed(self, connector, reason):
        self.activecons -= 1

    def next_path(self):
        return self.reqs.pop()

    def nextRequest(self):
        if self.total_reqs > 0:
            self.total_reqs -= 1
            reactor.connectTCP(self.ip, self.host_port, self)
        elif self.activecons <= 1:
            self.stop()

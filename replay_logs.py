#!/usr/bin/env python
import tests
import optparse

test_dict = {
    'twisted': tests.TwistedTest,
    'default': tests.QuickTest,
    'nutch': tests.NutchTest,
}

opt_parser = optparse.OptionParser(
    usage=("usage: %prog"
           "--test=twisted -f log_file -t 100 [-H www.foo.com -p /foobar/]"))

opt_parser.add_option("--test",
    default="twisted", help="Test to be run (%s)" % ",".join(test_dict.keys()))
opt_parser.add_option("-f", "--file",
    action="append", help="Files to be replayed")
opt_parser.add_option("-H", "--host",
    help="To go in the host header")
opt_parser.add_option("-i", "--ip",
    help="IP Address of host. If unset will use Host instead")
opt_parser.add_option("--port",
    default=80,
    type="int",
    help="Port (default=80)")
opt_parser.add_option("-t", "--threadlimit",
    type="int", help="Thread Limit", default=40)
opt_parser.add_option("-p", "--urlprefix",
    help="URL Prefix", default="")
opt_parser.add_option("-P", '--auth',
    help="HTTP Basic Auth (as 'username:password')", default="")


def main():
    (options, args) = opt_parser.parse_args()
    if not options.ip:
        options.ip = options.host

    lr = test_dict[options.test](options)
    lr.go()


if __name__ == "__main__":
    main()

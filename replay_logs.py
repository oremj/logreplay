#!/usr/bin/env python
import tests
import optparse

test_dict = {
             'twisted': tests.TwistedTest,
             'default' : tests.QuickTest,
             'nutch' : tests.NutchTest
             }

opt_parser = optparse.OptionParser(usage="usage: %prog --test=twisted -f log_file -t 100 [-H www.foo.com -p /foobar/]")
opt_parser.add_option("--test", default="default", help="Test to be run (%s)" % (",".join(test_dict.keys() ,)))
opt_parser.add_option("-f", action="append",help="Files to be replayed")
opt_parser.add_option("-H", help="To go in the host header")
opt_parser.add_option("-i", help="IP Address of host to replay against.  If unset will use Host instead")
opt_parser.add_option("--port", default=80, type="int", help="Port (default=80)")
opt_parser.add_option("-t", type="int",help="Thread Limit",default=40)
opt_parser.add_option("-p", help="URL Prefix", default="")
opt_parser.add_option("-P", help="HTTP Basic Auth (as 'username:password')", default="")

def main():
    (options, args) = opt_parser.parse_args()
    if not options.i:
        options.i = options.H

    lr = test_dict[options.test](options)
    lr.go()


if __name__ == "__main__":
    main()

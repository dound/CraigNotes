#!/usr/bin/env python
# Parses parts of HTML from http://www.craigslist.org/about/sites to extract
# state and city information for use in our city dropdown box.

import re
RE_STATES = re.compile(r'<div class="state_delimiter">([^<]+)</div>(.+?)</ul>')
RE_CITIES = re.compile(r'<li><a href="http://([^.]+).craigslist.[^"]+">([^>]+)</a></li>')

def parse(s):
    d = {}
    blocks = RE_STATES.findall(s.replace('\n', ''))
    for b in blocks:
        state, data = b[0], b[1]
        d[state] = RE_CITIES.findall(data)
    return d

if __name__ == '__main__':
    import sys
    d = parse(sys.stdin.read())
    a = []
    for state, cities in d.iteritems():
        a.append( (state, cities) )
    a.sort()
    for state,cities in a:
        print '						<option disabled="" value="%s">%s</option>' % (state,state.title())
	for city in cities:
		print '							<option value="%s">%s</option>' % (city[0], city[1].title())

#!/usr/bin/env python3
import re

with \
        open('controller.csv', 'w') as foController, \
        open('rtlong.csv', 'w') as foRtLong, \
        open('rubis-control-tier-0.log') as fi:
    for line in fi:
        m = re.match('.*\[pyController0\] (.*)', line)
        if m:
            print(m.group(1), file=foController)

        m = re.match('.*\[pyController0-tommi\] (.*)', line)
        if m:
            print(m.group(1), file=foRtLong)



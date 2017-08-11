#!/bin/sh
curl http://www8.cs.umu.se/~cklein/bigfiles/brownout-rubis-data.tar.xz | tar -xv --xz --strip-components=1 -C /var/lib/mysql

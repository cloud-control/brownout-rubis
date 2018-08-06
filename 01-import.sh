#!/bin/sh
curl http://cklein.people.cs.umu.se/bigfiles/brownout-rubis-data.tar.xz | tar -xv --xz --strip-components=1 -C /var/lib/mysql

#!/usr/bin/env python
from __future__ import print_function, division

import time
from time import sleep
import os
import socket

def avg(a):
	if len(a) == 0:
		return float('NaN')
	return sum(a) / len(a)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("localhost", 2712))

while True:
	data, address = s.recvfrom(4096)
	print(data)

s.close()

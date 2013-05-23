#!/usr/bin/env python
from __future__ import print_function, division

import datetime
import logging
import os
import select
import socket
from sys import stderr
from time import sleep
import time

CONTROL_INTERVAL = 1 # second

# Controller logic
def execute_controller(ctl_type, average_partial_service_times, set_point, ctl_probability):
	# control algorithm

	# control algorithm mm
	if ctl_type == 1:
		c_est = average_partial_service_times / ctl_probability # very rough estimate
		pole = 0.1
		safety_margin = 0.01
		error = (set_point - safety_margin) - average_partial_service_times
		ctl_probability = ctl_probability + (1/c_est) * (1 - pole) * error

	# control algorithm ck
	if ctl_type == 2:
		if average_partial_service_times > set_point:
			ctl_probability -= 0.1
		else:
			ctl_probability += 0.01

	# saturation, it's a probability
	ctl_probability = max(ctl_probability, 0.0)
	ctl_probability = min(ctl_probability, 1.0)
	return ctl_probability
# end controller logic

def now():
	return time.time()

def avg(a):
	if len(a) == 0:
		return float('NaN')
	return sum(a) / len(a)

def main():
	logging.basicConfig(level = logging.DEBUG)

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("localhost", 2712))

	poll = select.poll()
	poll.register(s, select.POLLIN)
	lastControl = now()
	latencies = []
	probability = 0.5
	while True: # controller never dies
		waitFor = (CONTROL_INTERVAL - (now() - lastControl)) * 1000

		events = poll.poll(waitFor)
		if events:
			data, address = s.recvfrom(4096)
			latencies.append(float(data))
		if now() - lastControl > CONTROL_INTERVAL:
			if latencies:
				probability = execute_controller(
					ctl_type = 1,
					average_partial_service_times = avg(latencies),
					set_point = 0.5,
					ctl_probability = probability,
				)

				logging.info("Avg. latency {0}, setting service level to {1}".format(avg(latencies), probability))
				with open('recommenderValve.tmp', 'w') as f:
					print(probability*100, file = f)
				os.rename('recommenderValve.tmp', 'recommenderValve')
			else:
				logging.info("No traffic since last control interval.")
			lastControl = now()
			latencies = []
	s.close()

if __name__ == "__main__":
	main()

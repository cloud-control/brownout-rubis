#!/usr/bin/env python
from __future__ import print_function, division

import datetime
import logging
from math import ceil
from optparse import OptionParser
import os
import select
import socket
from sys import stderr
from time import sleep
import time

CONTROL_INTERVAL = 1 # second
MEASURE_INTERVAL = 5 # second

# Controller logic
def execute_controller(ctl_type, pole, average_partial_service_times, set_point, ctl_probability):
	# control algorithm

	# control algorithm mm
	if ctl_type == 1:
		c_est = average_partial_service_times / ctl_probability # very rough estimate
		# NOTE: control knob allowing to smooth service times
		# To enable this, you *must* add a new state variable (c_est) to the controller.
		#c_est = 0.5 * c_est + 0.5 * average_partial_service_times / ctl_probability # very rough estimate
		safety_margin = 0.01
		error = (set_point - safety_margin) - average_partial_service_times
		# NOTE: control knob allowing slow increase
		if error > 0:
			error *= 0.1
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
		return float('nan')
	return sum(a) / len(a)

def median(a):
	# assumes a is sorted
	n = len(a)
	if n == 0:
		return float('nan')
	if n % 2 == 0:
		return (a[n//2-1] + a[n//2]) / 2
	else:
		return a[n//2]

def quartiles(a):
	n = len(a)
	if n == 0:
		return [ float('nan') ] * 6
	if n == 1:
		return [ a[0] ] * 6

	a = sorted(a)
	ret = []
	ret.append(a[0])
	ret.append(median(a[:n//2]))
	ret.append(median(a))
	ret.append(median(a[n//2:]))
	ret.append(a[-1])
	ret.append(avg(a))

	return ret

class UnixTimeStampFormatter(logging.Formatter):
	def formatTime(self, record, datefmt = None):
		return "{0:.6f}".format(record.created)

def main():
	logChannel = logging.StreamHandler()
	logChannel.setFormatter(UnixTimeStampFormatter("%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"))
	logging.getLogger().addHandler(logChannel)
	logging.getLogger().setLevel(logging.DEBUG)

	# Parse command-line
	parser = OptionParser()
	parser.add_option("--pole", type="float", dest="pole", help="use this pole value (default: %default)", default = 0.9)
	(options, args) = parser.parse_args()

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("localhost", 2712))

	poll = select.poll()
	poll.register(s, select.POLLIN)
	lastControl = now()
	lastTotalRequests = 0
	timestampedLatencies = [] # tuples of timestamp, latency
	totalRequests = 0
	probability = 0.5
	while True: # controller never dies
		waitFor = max(ceil((lastControl + CONTROL_INTERVAL - now()) * 1000), 1)
		events = poll.poll(waitFor)

		_now = now() # i.e., all following operations are "atomic" with respect to time
		if events:
			data, address = s.recvfrom(4096, socket.MSG_DONTWAIT)
			timestampedLatencies.append((_now, float(data)))
			totalRequests += 1
		if _now - lastControl >= CONTROL_INTERVAL:
			timestampedLatencies = [ (t, l) for t, l in timestampedLatencies if t > _now - MEASURE_INTERVAL ]
			latencies = [ l for t,l in timestampedLatencies ]
			if latencies:
				probability = execute_controller(
					ctl_type = 1,
					pole = options.pole,
					average_partial_service_times = max(latencies),
					set_point = 1,
					ctl_probability = probability,
				)

				latencyStat = quartiles(latencies)
				logging.info("latency={0:.0f}:{1:.0f}:{2:.0f}:{3:.0f}:{4:.0f}:({5:.0f})ms throughput={6:.0f}rps rr={7:.2f}% total={8}".format(
					latencyStat[0] * 1000,
					latencyStat[1] * 1000,
					latencyStat[2] * 1000,
					latencyStat[3] * 1000,
					latencyStat[4] * 1000,
					latencyStat[5] * 1000,
					(totalRequests - lastTotalRequests) / (_now-lastControl),
					probability * 100,
					totalRequests
				))
				with open('/tmp/recommenderValve.tmp', 'w') as f:
					print(probability, file = f)
				os.rename('/tmp/recommenderValve.tmp', '/tmp/recommenderValve')
			else:
				logging.info("No traffic since last control interval.")
			lastControl = _now
			lastTotalRequests = totalRequests
	s.close()

if __name__ == "__main__":
	main()

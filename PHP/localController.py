#!/usr/bin/env python
from __future__ import print_function, division

import datetime
import logging
from math import ceil
import numpy as np
from optparse import OptionParser
import os
import select
import socket
import sys
from time import sleep
import time

## Computes average
# @param numbers list of number to compute average for
# @return average or NaN if list is empty
def avg(numbers):
	if len(numbers) == 0:
		return float('nan')
	return sum(numbers)/len(numbers)

## Computes maximum
# @param numbers list of number to compute maximum for
# @return maximum or NaN if list is empty
# @note Similar to built-in function max(), but returns NaN instead of throwing
# exception when list is empty
def maxOrNan(numbers):
	if len(numbers) == 0:
		return float('nan')
	return max(numbers)

# Controller logic
class Controller:
	## Constructor.
	# @param initialTheta initial dimmer value
	# @param controlPeriod control period of brownout controller (0 = disabled)
	# @param setPoint where to keep latencies
	def __init__(self, initialTheta = 0.5, controlPeriod = 5, setPoint = 1, pole = 0.99):
		## control period (controller parameter)
		self.controlPeriod = controlPeriod # second
		## setpoint (controller parameter)
		self.setPoint = setPoint
		## initialization for the RLS estimator (controller variable)
		self.rlsP = 1000
		## RLS forgetting factor (controller parameter)
		self.rlsForgetting = 0.95
		## Current alpha (controller variable)
		self.alpha = 1
		## Pole (controller parameter)
		self.pole = pole
		## latencies measured during last control period (controller input)
		self.latestLatencies = []
		## dimmer value (controller output)
		self.theta = initialTheta
		## matching value (controller output)
		self.matchingValue = 0

	## Runs the control loop.
	# Basically retrieves self.lastestLatencies and computes a new self.theta.
	# Ask Martina for details. :P
	def runControlLoop(self):
		if self.latestLatencies:
			# Possible choices: max or avg latency control
			# serviceTime = avg(self.latestLatencies) # avg latency
			# serviceTime = max(self.latestLatencies) # max latency
			serviceTime = np.percentile(self.latestLatencies, 95) # 95 percentile
			serviceLevel = self.theta

			# choice of the estimator:
			# ------- bare estimator
			# self.alpha = serviceTime / serviceLevel # very rough estimate
			# ------- RLS estimation algorithm
			a = self.rlsP*serviceLevel
			g = 1 / (serviceLevel*a + self.rlsForgetting)
			k = g*a
			e = serviceTime - serviceLevel*self.alpha
			self.alpha = self.alpha + k*e
			self.rlsP  = (self.rlsP - g * a*a) / self.rlsForgetting
			# end of the estimator - in the end self.alpha should be set

			error = self.setPoint - serviceTime
			# NOTE: control knob allowing slow increase
			#if error > 0:
			#	error *= 0.1
			variation = (1 / self.alpha) * (1 - self.pole) * error
			serviceLevel += self.controlPeriod * variation

			# saturation, it's a probability
			self.theta = min(max(serviceLevel, 0.0), 1.0)

			# compute matching value
			self.matchingValue = min([ 1 - latency / self.setPoint for latency in self.latestLatencies ])
		else:
			self.matchingValue = 0

		utilization = float('nan') # XXX: not implemented (does it make sense for the real environment?)

		# Report
		valuesToOutput = [ \
			now(), \
			avg(self.latestLatencies), \
			maxOrNan(self.latestLatencies), \
			self.theta, \
			utilization, \
			self.matchingValue, \
		]
		print(','.join(["{0:.5f}".format(value) \
			for value in valuesToOutput]))
		sys.stdout.flush()

		# Re-run later
		self.latestLatencies = []

	def reportLatency(self, latency):
		self.latestLatencies.append(latency)

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
	# Set up logging
	logChannel = logging.StreamHandler()
	logChannel.setFormatter(UnixTimeStampFormatter("%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"))
	logging.getLogger().addHandler(logChannel)
	logging.getLogger().setLevel(logging.DEBUG)

	# Parse command-line
	parser = OptionParser()
	parser.add_option("--pole"    , type="float", help="use this pole value (default: %default)", default = 0.9)
	parser.add_option("--setPoint", type="float", help="keep maximum latency around this value (default: %default)", default = 1)
	parser.add_option("--initialTheta", type="float", help="set the initial dimmer value; useful when no control is present (default: %default)", default = 0.5)
	parser.add_option("--controlPeriod", type="float", help="time between control iterations (default: %default)", default = 0.5)
	parser.add_option("--rmIp", type="string", help="send matching values to this IP (default: %default)", default = "192.168.122.1")
	parser.add_option("--rmPort", type="int", help="send matching values to this UDP port (default: %default)", default = 2712)
	(options, args) = parser.parse_args()

	# Setup socket to listen for latency reports
	appSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	appSocket.bind(("localhost", 2712))

	# Setup socket to send matching values
	rmSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Initialize control loop
	poll = select.poll()
	poll.register(appSocket, select.POLLIN)
	lastControl = now()
	totalRequests = 0

	# Output initial service level
	with open('/tmp/serviceLevel.tmp', 'w') as f:
		print(options.initialTheta, file = f)
	os.rename('/tmp/serviceLevel.tmp', '/tmp/serviceLevel')

	# Control loop
	controller = Controller( \
		initialTheta = options.initialTheta, \
		setPoint = options.setPoint, \
		pole = options.pole, \
		controlPeriod = options.controlPeriod)

	while True:
		# Wait for next control iteration or message from application
		waitFor = max(ceil((lastControl + options.controlPeriod - now()) * 1000), 1)
		events = poll.poll(waitFor)

		_now = now() # i.e., all following operations are "atomic" with respect to time
		# If we received a latency report, record it
		if events:
			data, address = appSocket.recvfrom(4096, socket.MSG_DONTWAIT)
			controller.reportLatency(float(data))

		# Run control algorithm if it's time for it
		if _now - lastControl >= options.controlPeriod:
			controller.runControlLoop()

			# Report performance to RM
			rmSocket.sendto(str(controller.matchingValue), (options.rmIp, options.rmPort))

			# Output service level
			with open('/tmp/serviceLevel.tmp', 'w') as f:
				print(controller.theta, file = f)
			os.rename('/tmp/serviceLevel.tmp', '/tmp/serviceLevel')

			# Prepare for next control action
			lastControl = _now
	s.close()

if __name__ == "__main__":
	main()

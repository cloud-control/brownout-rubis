#!/usr/bin/env python
from __future__ import print_function, division

from collections import namedtuple
import datetime
import logging
from math import ceil
import numpy as np
from optparse import OptionParser
import os
import select
import shlex
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
		## EWMA arrival rate
		self.ewma_arrival_rate = 0

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
		arrival_rate = len(self.latestLatencies) / self.controlPeriod
		self.ewma_arrival_rate = self.ewma_arrival_rate * 0.5 \
			+ arrival_rate * 0.5

		# Report
		valuesToOutput = [ \
			now(), \
			avg(self.latestLatencies), \
			maxOrNan(self.latestLatencies), \
			self.theta, \
			utilization, \
			self.matchingValue, \
			arrival_rate, \
			self.ewma_arrival_rate, \
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

Revenue = namedtuple('Revenue', ['gamma', 'k', 'beta'])

def compute_optimal_cb_cd(rev, pb, pd, fc, xc):
	# assuming a uniform distribution if no pdf is given
	cmin = min(xc)
	cmax = max(xc)
	if fc is None:
		cb_o = cmin + (pb/pd)*(cmax-cmin);
	else:
		price_ratio = (pb/pd);
		for i in reversed(range(len(fc))):
			if sum(fc[i:])>price_ratio:
				break
		cb_o = xc[i]

	# assuming a uniform distribution if no pdf is given
	if fc is None:
		xc = np.linspace(cmin, cmax, 100)
		fc = 0.01*np.ones(100)
	y = np.zeros(len(xc))
	for i in range(len(xc)):
		cd = xc[i]
		y[i] = rev.k*rev.gamma*cd**(rev.k)*sum((xc[i:]**(rev.beta-rev.k))*fc[i:]) \
			- cd*pd*sum(fc[i:])
	i = np.argmin(np.abs(y))
	cd_o = xc[i]

	if cd_o < cb_o:
		cb_o = cd_o
	
	return cb_o, cd_o

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
	parser.add_option("--capacityControlPeriod", type="float",
			help="time between capacity control iterations (default: %default)", default = 5)
	parser.add_option("--rmIp", type="string", help="send matching values to this IP (default: %default)", default = "192.168.122.1")
	parser.add_option("--rmPort", type="int", help="send matching values to this UDP port (default: %default)", default = 2712)
	(options, args) = parser.parse_args()

	# Setup socket to listen for latency reports
	appSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	appSocket.bind(("localhost", 2712))

	# Setup socket to negotiate capacity
	rmSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	rmSocket.bind(("0.0.0.0", 2713))

	# Initialize control loop
	poll = select.poll()
	poll.register(appSocket, select.POLLIN)
	poll.register(rmSocket, select.POLLIN)
	lastControl = now()
	lastCapacityControl = now()
	totalRequests = 0

	# Economic stuff
	p_b = 1.42401458191e-06
	p_d = 1.99362041467e-06
	capacity_scaling_factor=3.03810674805e-05
	revenue = Revenue(gamma=2.28e-6/capacity_scaling_factor, k=0.7, beta=1)

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

	c_b = 1 # initial guess
	c_d = 10 # initial guess
	c_i_s = []
	newPrices = False
	arrivalsSinceLastCapacityControl = 0
	while True:
		# Wait for next control iteration or message from application
		waitFor = max(ceil((lastControl + options.controlPeriod - now()) * 1000), 1)
		events = poll.poll(waitFor)

		_now = now() # i.e., all following operations are "atomic" with respect to time
		# If we received a latency report, record it
		for fd, event in events:
			if fd == appSocket.fileno():
				data, address = appSocket.recvfrom(4096, socket.MSG_DONTWAIT)
				controller.reportLatency(float(data))
				arrivalsSinceLastCapacityControl += 1
			elif fd == rmSocket.fileno():
				data, address = rmSocket.recvfrom(4096, socket.MSG_DONTWAIT)
				req = dict(token.split('=') for token in shlex.split(data))
				logging.debug('Got RM request: %s', req)
				p_b = getattr(req, 'p_b', p_b)
				p_d = getattr(req, 'p_d', p_d)
				newPrices = True

		# Run control algorithm if it's time for it
		if _now - lastControl >= options.controlPeriod:
			controller.runControlLoop()

			# Output service level
			with open('/tmp/serviceLevel.tmp', 'w') as f:
				print(controller.theta, file = f)
			os.rename('/tmp/serviceLevel.tmp', '/tmp/serviceLevel')

			# Prepare for next control action
			lastControl = _now

		if _now - lastCapacityControl >= options.capacityControlPeriod:
			arrivalRate = arrivalsSinceLastCapacityControl / options.capacityControlPeriod
			# Ask required capacity
			c_i = arrivalRate / 10 # profiled offline
			c_i_s.append(c_i) # store value before trimming
			c_i = max(c_b, min(c_i, c_d))
			rmSocket.sendto('c_i={0}'.format(c_i), (options.rmIp,
				options.rmPort))

			arrivalsSinceLastCapacityControl = 0
			lastCapacityControl = _now

		# Request new base and dynamic capacities
		if newPrices:
			if c_i_s:
				f_c, x_c = np.histogram(c_i_s, bins=100)
				sum_f_c = sum(f_c)
				f_c = map(lambda x: x / sum_f_c, f_c)
				x_c = (x_c[:-1] + x_c[1:]) / 2
			else:
				f_c, x_c = None, [1, 30]

			c_b, c_d = compute_optimal_cb_cd(revenue, p_b, p_d, f_c, x_c)
			if c_b < 1:
				c_b = 1
			if c_d < c_b:
				c_d = c_b

			rmSocket.sendto('c_b={0} c_d={1}'.format(c_b, c_d), (options.rmIp,
				options.rmPort))

			newPrices = False
			c_i_s = []

if __name__ == "__main__":
	main()

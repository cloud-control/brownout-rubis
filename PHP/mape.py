#!/usr/bin/env python
from __future__ import print_function, division

import httplib2
import time
from time import sleep
import os
import socket

def avg(a):
	if len(a) == 0:
		return float('NaN')
	return sum(a) / len(a)

# Input parameters
# XXX: command-line options
testUrl = 'http://localhost/PHP/RandomItemWithRecommendations.php'
latencyWindowLength = 10
recommenderValveWindowLength = 10

# Initial values
http = httplib2.Http(timeout = 10)

recommenderValve = 0
try:
	with open('recommenderValve') as f:
		recommenderValve = int(f.read())
except:
	pass

# MAPE-loop
latencies = []
recommenderValves = []
while True: # never ends
	# Monitor
	startTime = time.time()
	try:
		resp, content = http.request(testUrl)
	except socket.timeout as e:
		print("M: timeout after 0.5 seconds")
	endTime = time.time()
	latency = endTime-startTime
	latencies = latencies[:latencyWindowLength-1] + [ latency ]
	print("M: HTTP latency: {0:4d} ms, average over last {1} intervals {2:4d} ms".
		format(int(latency * 1000), len(latencies), int(avg(latencies) * 1000)))

	# Analyze
	if latency > 0.5:
		recommenderValve -= 10
	else:
		recommenderValve += 1

	if recommenderValve > 100:
		recommenderValve = 100
	elif recommenderValve < 0:
		recommenderValve = 0

	# Plan

	# Execute
	recommenderValves = recommenderValves[:recommenderValveWindowLength-1] + [ recommenderValve ]
	print("E: Setting recommender valve to {0}, average in last {1} intervals {2}"
		.format(recommenderValve, len(recommenderValves), avg(recommenderValves)))
	with open('recommenderValve.tmp', 'w') as f:
		print(recommenderValve, file = f)
	os.rename('recommenderValve.tmp', 'recommenderValve')

	if latency < 1:
		sleep(1 - latency)

#!/usr/bin/env python
from __future__ import print_function, division

import httplib2
import time
from time import sleep
import os
import socket

# Input parameters
# XXX: command-line options
testUrl = 'http://localhost/PHP/RandomItemWithRecommendations.php'

# Initial values
http = httplib2.Http(timeout = 10)

recommenderValve = 0
try:
	with open('recommenderValve') as f:
		recommenderValve = float(f.read())
except:
	pass

# MAPE-loop
while True: # never ends
	# Monitor
	startTime = time.time()
	try:
		resp, content = http.request(testUrl)
	except socket.timeout as e:
		print("M: timeout after 0.5 seconds")
	endTime = time.time()
	latency = endTime-startTime
	print("M: HTTP latency: " + str(latency))

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
	print("E: Setting recommender valve to: " + str(recommenderValve))
	with open('recommenderValve.tmp', 'w') as f:
		print(recommenderValve, file = f)
	os.rename('recommenderValve.tmp', 'recommenderValve')

	sleep(1)

"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import flask
from flask import Flask, redirect, url_for, request, render_template
from pymongo import MongoClient
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
import json
import os

import logging
#os.environ['MONGODB_HOSTNAME']
###
# Globals
###
app = flask.Flask(__name__)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetsdb
###
# Pages
###



@app.route("/")
@app.route("/index")
def index():
	app.logger.debug("Main page entry")
	return flask.render_template('calc.html')


@app.errorhandler(404)
def page_not_found(error):
	app.logger.debug("Page not found")
	return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
	"""
	Calculates open/close times from miles, using rules
	described at https://rusa.org/octime_alg.html.
	Expects one URL-encoded argument, the number of miles.
	"""
	app.logger.debug("Got a JSON request")
	km = request.args.get('km', 999, type=float)
	brevetDist = request.args.get('brevetDist', type=float)
	startTime = request.args.get('startTime', type=str)
	startarrow = arrow.get(startTime, "YYYY-MM-DDTHH:mm")

	startarrow = startarrow.shift(hours=8)
	app.logger.debug(f"km={km}")
	app.logger.debug(f"request.args: {request.args}")
	app.logger.debug(f"brevetDist={brevetDist}")


	open_time = acp_times.open_time(km, brevetDist, startarrow)
	close_time = acp_times.close_time(km, brevetDist, startarrow)
	result = {"open": open_time.isoformat().format('YYYY-MM-DDTHH:mm'), "close": close_time.isoformat().format('YYYY-MM-DDTHH:mm')}
	return flask.jsonify(result=result)

@app.route("/_display")
def _display():
	return flask.render_template('display.html', rows=list(db.brevetsdb.find()))

@app.route("/_submit", methods=["POST"])
def _submit():
	success = True
	errorMessage = ""
	data = json.loads(request.form.get('returnData', type=str))
	app.logger.debug(f"entry={data}")
	if(len(data) == 0):
		errorMessage = "Error: there are no table entries in ACP calculator"
		success = False
	else:
		db.brevetsdb.drop()

		for entry in data:
			db.brevetsdb.insert_one(entry)
	

	returnJson = {
	"success": success,
	"errorMessage": errorMessage
	}
	
	return flask.jsonify(returnJson)
		
#############


if __name__ == "__main__":
	print("Opening for global access on port 5000")
	app.run(port=5000, host="0.0.0.0")

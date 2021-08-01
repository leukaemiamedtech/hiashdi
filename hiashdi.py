#!/usr/bin/env python3
""" HIASHDI Historical Data Broker.

The HIASHDI (HIAS Historical Data Interface) is an implementation of a REST
API Server that stores HIAS network historical data and serves it to
authenticated HIAS devices & applications by exposing the data through a
REST API and pushing data through subscriptions.

MIT License

Copyright (c) 2021 Asociación de Investigacion en Inteligencia Artificial
Para la Leucemia Peter Moss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files(the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Contributors:
- Adam Milton-Barker

"""

import json
import psutil
import requests
import os
import signal
import sys
import threading
import urllib

from bson import json_util, ObjectId
from flask import Flask, request, Response
from threading import Thread


from modules.helpers import helpers
from modules.broker import broker
from modules.data import data
from modules.mongodb import mongodb
from modules.mqtt import mqtt


class hiashdi():
	""" HIASHDI Historical Data Broker.

	The HIASHDI Context Broker handles contextual data for all HIAS
	devices/applications and agents. HIASHDI is based on CEF/FIWARE
	NGSI V2 specification.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.helpers = helpers("HIASHDI")
		self.confs = self.helpers.confs
		self.credentials = self.helpers.credentials

		self.component = self.credentials["hiashdi"]["name"]
		self.version = self.credentials["hiashdi"]["version"]

		self.err406 = self.confs["errorMessages"]["406"]

		self.helpers.logger.info(
			self.component + " " + self.version + " initialization complete.")

	def mongoDbConnection(self):
		""" Initiates the mongodb connection class. """

		self.mongodb = mongodb(self.helpers)
		self.mongodb.start()

	def hiashdiConnection(self):
		""" Configures the Context Broker. """

		self.broker = broker(self.helpers, self.mongodb)

	def iotConnection(self):
		""" Initiates the iotJumpWay connection. """

		self.mqtt = mqtt(self.helpers, "HIASHDI", {
			"host": self.credentials["iotJumpWay"]["host"],
			"port": self.credentials["iotJumpWay"]["port"],
			"location": self.credentials["iotJumpWay"]["location"],
			"zone": self.credentials["iotJumpWay"]["zone"],
			"entity": self.credentials["iotJumpWay"]["entity"],
			"name": self.credentials["iotJumpWay"]["name"],
			"un": self.credentials["iotJumpWay"]["un"],
			"up": self.credentials["iotJumpWay"]["up"]
		})
		self.mqtt.configure()
		self.mqtt.start()

	def configureData(self):
		""" Configures the HIASHDI entities. """

		self.data = data(self.helpers, self.mongodb, self.broker)

	def configureTypes(self):
		""" Configures the HIASHDI entity types. """

		self.types = types(self.helpers, self.mongodb, self.broker)

	def configureSubscriptions(self):
		""" Configures the HIASHDI subscriptions. """

		self.subscriptions = subscriptions(self.helpers, self.mongodb, self.broker)

	def getBroker(self):

		return {
			"locations_url": self.confs["endpoints"]["locations_url"],
			"zones_url": self.confs["endpoints"]["zones_url"],
			"data_url": self.confs["endpoints"]["data_url"],
			"life_url": self.confs["endpoints"]["life_url"],
			"sensors_url": self.confs["endpoints"]["sensors_url"],
			"actuators_url": self.confs["endpoints"]["actuators_url"],
			"commands_url": self.confs["endpoints"]["commands_url"],
			"subscriptions_url": self.confs["endpoints"]["subscriptions_url"],
			"CPU": psutil.cpu_percent(),
			"Memory": psutil.virtual_memory()[2],
			"Diskspace": psutil.disk_usage('/').percent,
			"Temperature": psutil.sensors_temperatures()['coretemp'][0].current
		}

	def processHeaders(self, request):
		""" Processes the request headers """

		accepted = self.broker.checkAcceptsType(request.headers)
		content_type = self.broker.checkContentType(request.headers)

		return accepted, content_type

	def checkBody(self, body, text=False):
		""" Checks the request body """

		return self.broker.checkBody(body, text)

	def respond(self, responseCode, response, accepted):
		""" Builds the request response """

		headers = {}
		if "application/json" in accepted:
			response =  Response(response=response, status=responseCode,
					mimetype="application/json")
			headers['Content-Type'] = 'application/json'
		elif "text/plain" in accepted:
			response = self.broker.prepareResponse(response)
			response = Response(response=response, status=responseCode,
					mimetype="text/plain")
			headers['Content-Type'] = 'text/plain; charset=utf-8'
		response.headers = headers
		return response

	def life(self):
		""" Sends vital statistics to HIAS """

		cpu = psutil.cpu_percent()
		mem = psutil.virtual_memory()[2]
		hdd = psutil.disk_usage('/').percent
		tmp = psutil.sensors_temperatures()['coretemp'][0].current
		r = requests.get('http://ipinfo.io/json?token=' +
				self.credentials["iotJumpWay"]["ipinfo"])
		data = r.json()
		location = data["loc"].split(',')

		# Send iotJumpWay notification
		self.mqtt.publish("Life", {
			"CPU": str(cpu),
			"Memory": str(mem),
			"Diskspace": str(hdd),
			"Temperature": str(tmp),
			"Latitude": float(location[0]),
			"Longitude": float(location[1])
		})

		self.helpers.logger.info("HIASHDI life statistics published.")
		threading.Timer(300.0, self.life).start()

	def signal_handler(self, signal, frame):
		self.helpers.logger.info("Disconnecting")
		sys.exit(1)


hiashdi = hiashdi()
app = Flask(hiashdi.component)

@app.route('/', methods=['GET'])
def about():
	""" Responds to GET requests sent to the /v1/ API endpoint. """

	accepted, content_type = hiashdi.processHeaders(request)
	if accepted is False:
		return hiashdi.respond(406, hiashdi.confs["errorMessages"][str(406)], "application/json")
	if content_type is False:
		return hiashdi.respond(415, hiashdi.confs["errorMessages"][str(415)], "application/json")

	return hiashdi.respond(200, json.dumps(json.loads(json_util.dumps(hiashdi.getBroker())), indent=4), accepted)


@app.route('/data', methods=['GET'])
def dataGet():
	""" Responds to GET requests sent to the /v1/data API endpoint. """

	accepted, content_type = hiashdi.processHeaders(request)

	if request.args.get('type') is None:
		return hiashdi.respond(400, hiashdi.helpers.confs["errorMessages"]["400b"], "application/json")
	if accepted is False:
		return hiashdi.respond(406, hiashdi.confs["errorMessages"][str(406)], "application/json")
	if content_type is False:
		return hiashdi.respond(415, hiashdi.confs["errorMessages"][str(415)], "application/json")

	return hiashdi.data.getDatas(request.args, accepted)


@app.route('/data', methods=['POST'])
def dataPost():
	""" Responds to POST requests sent to the /v1/data API endpoint. """

	accepted, content_type = hiashdi.processHeaders(request)

	if request.args.get('type') is None:
		return hiashdi.respond(400, hiashdi.helpers.confs["errorMessages"]["400b"], "application/json")

	query = hiashdi.checkBody(request)
	if query is False:
		return hiashdi.respond(400, hiashdi.helpers.confs["errorMessages"]["400p"], accepted)

	return hiashdi.data.createData(query, request.args.get('type'), accepted)


@app.route('/data/<_id>', methods=['GET'])
def entityGet(_id):
	""" Responds to GET requests sent to the /v1/data/<_id> API endpoint. """

	accepted, content_type = hiashdi.processHeaders(request)

	if request.args.get('type') is None:
		return hiashdi.respond(400, hiashdi.helpers.confs["errorMessages"]["400b"], "application/json")
	if accepted is False:
		return hiashdi.respond(406, hiashdi.confs["errorMessages"][str(406)], "application/json")
	if content_type is False:
		return hiashdi.respond(415, hiashdi.confs["errorMessages"][str(415)], "application/json")

	if request.args.get('attrs') is None:
		attrs = None
	else:
		attrs = request.args.get('attrs')

	return hiashdi.data.getData(request.args.get('type'), _id, attrs, accepted)

def main():
	signal.signal(signal.SIGINT, hiashdi.signal_handler)
	signal.signal(signal.SIGTERM, hiashdi.signal_handler)

	hiashdi.iotConnection()
	hiashdi.mongoDbConnection()
	hiashdi.hiashdiConnection()
	hiashdi.configureData()

	Thread(target=hiashdi.life, args=(), daemon=True).start()

	app.run(host=hiashdi.credentials["server"]["ip"],
			port=hiashdi.credentials["server"]["port"])

if __name__ == "__main__":
	main()

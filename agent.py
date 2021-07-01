#!/usr/bin/env python
""" HIAS iotJumpWay Agent Abstract Class

HIAS IoT Agents process all data coming from entities connected to the HIAS
iotJumpWay brokers.

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

import joblib
import json
import os
import pickle
import psutil
import requests
import signal
import sys
import time
import threading

sys.path.insert(0, os.path.abspath(
	os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime
from datetime import timedelta
from flask import Flask, request, Response
from threading import Thread
from abc import ABC, abstractmethod

from components.agents.AbstractAgent import AbstractAgent


class Agent(AbstractAgent):
	""" Class representing a HIAS iotJumpWay MQTT IoT Agent.

	This object represents a HIAS iotJumpWay IoT Agent. HIAS IoT Agents
	process all data coming from entities connected to the HIAS iotJumpWay
	broker using the MQTT & Websocket machine to machine protocols.
	"""

	def statusCallback(self, topic, payload):
		"""Called in the event of a status payload

		Args:
			topic (str): The topic the payload was sent to.
			payload (:obj:`str`): The payload.
		"""

		status = payload.decode()
		splitTopic = topic.split("/")

		if splitTopic[1] not in self.ignoreTypes:
			entityType = splitTopic[1][:-1]
		else:
			entityType = splitTopic[1]

		self.helpers.logger.info(
			"Received " + entityType  + " Status: " + status)

		attrs = self.getRequiredAttributes(entityType, splitTopic)
		bch = attrs["blockchain"]

		if not self.hiasbch.iotJumpWayAccessCheck(bch):
			return

		entity = attrs["id"]
		location = attrs["location"]
		zone = attrs["zone"] if "zone" in attrs else "NA"

		updateResponse = self.hiascdi.updateEntity(
			entity, entityType, {
				"networkStatus": {"value": status},
				"networkStatus.metadata": {"timestamp": datetime.now().isoformat()},
				"dateModified": {"value": datetime.now().isoformat()}
			})

		if updateResponse:
			_id = self.mongodb.insertData(self.mongodb.mongoConn.Statuses, {
				"Use": entityType,
				"Location": location,
				"Zone": zone,
				"HIASCDI": entity if entityType == "HIASCDI" else "NA",
				"Agent": entity if entityType == "Agent" else "NA",
				"Application": entity if entityType == "Application" else "NA",
				"Device": entity if entityType == "Device" else "NA",
				"Staff": entity if entityType == "Staff" else "NA",
				"Status": status,
				"Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			}, None)

			self.helpers.logger.info(
				entityType + " " + entity + " status update OK")
		else:
			self.helpers.logger.error(
				entityType + " " + entity + " status update KO")

	def lifeCallback(self, topic, payload):
		"""Called in the event of a life payload

		Args:
			topic (str): The topic the payload was sent to.
			payload (:obj:`str`): The payload.
		"""

		data = json.loads(payload.decode("utf-8"))
		splitTopic = topic.split("/")

		if splitTopic[1] not in self.ignoreTypes:
			entityType = splitTopic[1][:-1]
		else:
			entityType = splitTopic[1]

		self.helpers.logger.info(
			"Received " + entityType  + " Life: " + str(data))

		attrs = self.getRequiredAttributes(entityType, splitTopic)
		bch = attrs["blockchain"]

		if not self.hiasbch.iotJumpWayAccessCheck(bch):
			return

		entity = attrs["id"]
		location = attrs["location"]
		zone = attrs["zone"] if "zone" in attrs else "NA"

		updateResponse = self.hiascdi.updateEntity(
			entity, entityType, {
				"networkStatus": {"value": "ONLINE"},
				"networkStatus.metadata": {"timestamp": datetime.now().isoformat()},
				"dateModified": {"value": datetime.now().isoformat()},
				"cpuUsage": {
					"value": float(data["CPU"])
				},
				"memoryUsage": {
					"value": float(data["Memory"])
				},
				"hddUsage": {
					"value": float(data["Diskspace"])
				},
				"temperature": {
					"value": float(data["Temperature"])
				},
				"location": {
					"type": "geo:json",
					"value": {
						"type": "Point",
						"coordinates": [float(data["Latitude"]), float(data["Longitude"])]
					}
				}
			})

		if updateResponse:
			_id = self.mongodb.insertData(self.mongodb.mongoConn.Life, {
				"Use": entityType,
				"Location": location,
				"Zone": zone,
				"HIASCDI": entity if entityType == "HIASCDI" else "NA",
				"Agent": entity if entityType == "Agent" else "NA",
				"Application": entity if entityType == "Application" else "NA",
				"Device": entity if entityType == "Device" else "NA",
				"Staff": entity if entityType == "Staff" else "NA",
				"Data": data,
				"Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			}, None)

			self.helpers.logger.info(
				entityType + " " + entity + " life update OK")
		else:
			self.helpers.logger.error(
				entityType + " " + entity + " life update KO")

	def sensorsCallback(self, topic, payload):
		"""Called in the event of a sensor payload

		Args:
			topic (str): The topic the payload was sent to.
			payload (:obj:`str`): The payload.
		"""

		data = json.loads(payload.decode("utf-8"))
		splitTopic = topic.split("/")

		if splitTopic[1] not in self.ignoreTypes:
			entityType = splitTopic[1][:-1]
		else:
			entityType = splitTopic[1]

		self.helpers.logger.info(
			"Received " + entityType  + " Sensors Data: " + str(data))

		attrs = self.getRequiredAttributes(entityType, splitTopic)
		bch = attrs["blockchain"]

		if not self.hiasbch.iotJumpWayAccessCheck(bch):
			return

		entity = attrs["id"]
		location = attrs["location"]
		zone = attrs["zone"] if "zone" in attrs else "NA"

		sensors = self.hiascdi.getSensors(
			entity, entityType)
		sensorData = sensors["sensors"]


		i = 0
		for sensor in sensorData:
			for prop in sensor["properties"]["value"]:
				if data["Type"].lower() in prop:
					sensorData[i]["properties"]["value"][data["Type"].lower()] = {
						"value": data["Value"],
						"timestamp": datetime.now().isoformat()
					}
			i = i + 1

		updateResponse = self.hiascdi.updateEntity(
			entity, entityType, {
				"networkStatus": {"value": "ONLINE"},
				"networkStatus.metadata": {"timestamp": datetime.now().isoformat()},
				"dateModified": {"value": datetime.now().isoformat()},
				"sensors": sensorData
			})

		if updateResponse:
			_id = self.mongodb.insertData(self.mongodb.mongoConn.Sensors, {
				"Use": entityType,
				"Location": location,
				"Zone": zone,
				"Device": entity if entityType == "Device" else "NA",
				"HIASCDI": entity if entityType == "HIASCDI" else "NA",
				"Agent": entity if entityType == "Agent" else "NA",
				"Application": entity if entityType == "Application" else "NA",
				"Device": entity if entityType == "Device" else "NA",
				"Staff": entity if entityType == "Staff" else "NA",
				"Sensor": data["Sensor"],
				"Type": data["Type"],
				"Value": data["Value"],
				"Message": data["Message"],
				"Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			}, None)

			self.helpers.logger.info(
				entityType + " " + entity + " sensors update OK")
		else:
			self.helpers.logger.error(
				entityType + " " + entity + " sensors update KO")

	def life(self):
		""" Sends entity statistics to HIAS """

		cpu = psutil.cpu_percent()
		mem = psutil.virtual_memory()[2]
		hdd = psutil.disk_usage('/fserver').percent
		tmp = psutil.sensors_temperatures()['coretemp'][0].current
		r = requests.get('http://ipinfo.io/json?token=' +
					self.helpers.credentials["iotJumpWay"]["ipinfo"])
		data = r.json()
		location = data["loc"].split(',')

		self.mqtt.publish("Life", {
			"CPU": float(cpu),
			"Memory": float(mem),
			"Diskspace": float(hdd),
			"Temperature": float(tmp),
			"Latitude": float(location[0]),
			"Longitude": float(location[1])
		})

		self.helpers.logger.info("Agent life statistics published.")
		threading.Timer(300.0, self.life).start()

	def respond(self, responseCode, response):
		""" Returns the request repsonse """

		return Response(response=json.dumps(response, indent=4), status=responseCode,
						mimetype="application/json")

	def signal_handler(self, signal, frame):
		self.helpers.logger.info("Disconnecting")
		self.mqtt.disconnect()
		sys.exit(1)

app = Flask(__name__)
Agent = Agent()

@app.route('/About', methods=['GET'])
def about():
	"""
	Returns Agent details

	Responds to GET requests sent to the North Port About API endpoint.
	"""

	return Agent.respond(200, {
		"Identifier": Agent.credentials["iotJumpWay"]["entity"],
		"Host": Agent.credentials["server"]["ip"],
		"NorthPort": Agent.credentials["server"]["port"],
		"CPU": psutil.cpu_percent(),
		"Memory": psutil.virtual_memory()[2],
		"Diskspace": psutil.disk_usage('/').percent,
		"Temperature": psutil.sensors_temperatures()['coretemp'][0].current
	})

def main():

	signal.signal(signal.SIGINT, Agent.signal_handler)
	signal.signal(signal.SIGTERM, Agent.signal_handler)

	Agent.mongodbConn()
	Agent.hiascdiConn()
	Agent.hiasbchConn()
	Agent.mqttConn({
		"host": Agent.credentials["iotJumpWay"]["host"],
		"port": Agent.credentials["iotJumpWay"]["port"],
		"location": Agent.credentials["iotJumpWay"]["location"],
		"zone": Agent.credentials["iotJumpWay"]["zone"],
		"entity": Agent.credentials["iotJumpWay"]["entity"],
		"name": Agent.credentials["iotJumpWay"]["name"],
		"un": Agent.credentials["iotJumpWay"]["un"],
		"up": Agent.credentials["iotJumpWay"]["up"]
	})

	Thread(target=Agent.life, args=(), daemon=True).start()

	app.run(host=Agent.helpers.credentials["server"]["ip"],
			port=Agent.helpers.credentials["server"]["port"])

if __name__ == "__main__":
	main()

#!/usr/bin/env python
""" HIASCDI Helper Module

This module provides helper functions that allow the HIAS iotAgents
to communicate with the HIASCDI Context Broker.

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
import requests

class hiascdi():
	""" HIAS HIASCDI Helpers

	Helper functions that allow the HIAS iotAgents
	to communicate with the HIASCDI.
	"""

	def __init__(self, helpers, mongodb):
		""" Initializes the class. """

		self.helpers = helpers
		self.program = "HIASCDI Helper Module"

		self.mongodb = mongodb

		self.headers = {
			"accept": self.helpers.confs_core["iotJumpWay"]["hiascdi"]["contentType"],
			"content-type": self.helpers.confs_core["iotJumpWay"]["hiascdi"]["contentType"]
		}

		self.auth = (self.helpers.confs_core["iotJumpWay"]["mqtt"]["agent"]["identifier"],
					self.helpers.confs_core["iotJumpWay"]["mqtt"]["agent"]["auth"])

		self.helpers.logger.info("HIASCDI initialization complete.")

	def getRequiredAttributes(self, entityType, splitTopic):
		""" Gets required attributes. """

		if entityType in ["Robotics","Application","Staff"]:
			entity = splitTopic[2]
			params = "&attrs=id,type,authenticationBlockchainUser.value,networkLocation.value"
		else:
			entity = splitTopic[3]
			params = "&attrs=id,type,authenticationBlockchainUser.value,networkLocation.value,networkZone.value"

		apiUrl = "https://" + self.helpers.confs_core["iotJumpWay"]["host"] + "/" + \
					self.helpers.confs_core["iotJumpWay"]["hiascdi"]["address"] + \
					"/entities/" + entity + "?type=" + entityType + params

		response = requests.get(apiUrl, headers=self.headers, auth=self.auth)

		return json.loads(response.text)

	def updateEntity(self, _id, typer, data):
		""" Updates an entity. """

		apiUrl = "https://" + self.helpers.confs_core["iotJumpWay"]["host"] + "/" + \
			self.helpers.confs_core["iotJumpWay"]["hiascdi"]["address"] + \
			"/entities/" + _id + "/attrs?type=" + typer

		response = requests.post(apiUrl, data=json.dumps(
			data), headers=self.headers, auth=self.auth)
		if response.status_code == 204:
			return True
		else:
			return False

	def getSensors(self, _id, typer):
		""" Gets sensor list. """

		apiUrl = "https://" + self.helpers.confs_core["iotJumpWay"]["host"] + "/" + \
					self.helpers.confs_core["iotJumpWay"]["hiascdi"]["address"] + \
					"/entities/" + _id + "?type=" + typer + "&attrs=sensors"

		response = requests.get(apiUrl, headers=self.headers, auth=self.auth)

		return json.loads(response.text)

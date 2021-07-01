#!/usr/bin/env python
""" HIASBCH Helper Module

This module provides helper functions that allow communication with the
HIASBCH Blockchain.

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

import bcrypt
import json
import sys
import time

from requests.auth import HTTPBasicAuth
from web3 import Web3


class hiasbch():
	""" hiasbch Class

	Handles communication with HIASBCH.
	"""

	def __init__(self, helpers):
		""" Initializes the class. """

		self.helpers = helpers
		self.confs = self.helpers.confs
		self.core_confs = self.helpers.confs_core
		self.credentials = self.helpers.credentials

		self.contractBalance = 5000

		self.helpers.logger.info("HIASBCH Class initialization complete.")

	def start(self):
		""" Connects to HIASBCH. """

		self.w3 = Web3(Web3.HTTPProvider(self.core_confs["hiasbch"]["bchost"], request_kwargs={
						'auth': HTTPBasicAuth(self.core_confs["iotJumpWay"]["mqtt"]["agent"]["identifier"], self.core_confs["iotJumpWay"]["mqtt"]["agent"]["auth"])}))
		self.authContract = self.w3.eth.contract(self.w3.toChecksumAddress(self.core_confs["hiasbch"]["authContract"]),
											abi=json.dumps(self.core_confs["hiasbch"]["authAbi"]))
		self.iotContract = self.w3.eth.contract(self.w3.toChecksumAddress(self.core_confs["hiasbch"]["iotContract"]),
											abi=json.dumps(self.core_confs["hiasbch"]["iotAbi"]))
		self.patientsContract = self.w3.eth.contract(self.w3.toChecksumAddress(self.core_confs["hiasbch"]["patientsContract"]),
											abi=json.dumps(self.core_confs["hiasbch"]["patientsAbi"]))
		self.helpers.logger.info("HIASBCH connections started")

	def iotJumpWayAccessCheck(self, address):
		""" Checks sender is allowed access to the iotJumpWay Smart Contract """

		if not self.iotContract.functions.accessAllowed(self.w3.toChecksumAddress(address)).call({'from': self.w3.toChecksumAddress(self.core_confs["hiasbch"]["iaddress"])}):
			return False
		else:
			return True


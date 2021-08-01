#!/usr/bin/env python
""" HIASHDI Data Module.

This module provides the functionality to create, retrieve
and update HIASHDI data.

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
import jsonpickle
import os
import sys

from bson.objectid import ObjectId
from mgoquery import Parser

class data():
	""" HIASHDI Data Module.

	This module provides the functionality to create, retrieve
	and update HIASHDI data.
	"""

	def __init__(self, helpers, mongodb, broker):
		""" Initializes the class. """

		self.helpers = helpers
		self.program = "HIASHDI Data Module"

		self.mongodb = mongodb
		self.broker = broker

		self.helpers.logger.info(self.program + " initialization complete.")

	def getCollection(self, typeof):

		if typeof == "Location":
			collection = self.mongodb.mongoConn.Locations
		elif typeof == "Zones":
			collection = self.mongodb.mongoConn.Zones
		elif typeof == "Statuses":
			collection = self.mongodb.mongoConn.Statuses
		elif typeof == "Life":
			collection = self.mongodb.mongoConn.Life
		elif typeof == "Sensors":
			collection = self.mongodb.mongoConn.Sensors
		elif typeof == "Actuators":
			collection = self.mongodb.mongoConn.Actuators
		elif typeof == "Commands":
			collection = self.mongodb.mongoConn.Commands
		elif typeof == "Subscriptions":
			collection = self.mongodb.mongoConn.Subscriptions

		return collection

	def getDatas(self, arguments, accepted=[]):
		""" Gets data from MongoDB.

		You can access this endpoint by naviating your browser to https://YourServer/hiascdi/v1/data
		If you are not logged in to the HIAS network you will be shown an authentication pop up
		where you should provide your HIAS network user and password.
		"""

		params = []
		cparams = []
		sort = []
		query = {}
		headers = {}

		collection = self.getCollection(arguments.get('type'))

		count_opt = False
		unique_opt = False

		# Processes the options parameter
		options = arguments.get('options') if arguments.get('options') is not None else None
		if options is not None:
			options = options.split(",")
			for option in options:
				unique_opt = True if option == "unique" else unique_opt
				count_opt = True if option == "count" else count_opt

		# Removes the MongoDB ID
		fields = {}

		if arguments.get('use') is not None:
			# Sets a type query
			eor = []
			types = arguments.get('use').split(",")
			if len(types) == 1:
				query.update({"Use":
					{'$in': [types[0]]}
				})
			else:
				for eid in types:
					eor.append({"Use":
						{'$in': [eid]}
					})
				params.append({"$or": eor})
		elif arguments.get('typePattern') is not None:
			query.update({"Use":
				{'$regex': arguments.get('typePattern')}
			})

		if arguments.get('id') is not None:
			# Sets a id query
			eor = []
			ids = arguments.get('id').split(",")
			if len(ids) == 1:
				print(ids[0])
				query.update({"_id": ObjectId(ids[0])})
			else:
				for eid in ids:
					print(eid)
					eor.append({"_id": ObjectId(eid)})
				params.append({"$or": eor})
		elif arguments.get('idPattern') is not None:
			query.update({"id":
				{'$regex': arguments.get('idPattern')}
			})

		attribs = []
		if arguments.get('attrs') is not None:
			# Sets a attrs query
			attribs = arguments.get('attrs').split(",")
			if '*' in attribs:
				# Removes builtin attributes
				if 'dateCreated' not in attribs:
					fields.update({'dateCreated': False})
				if 'dateModified' not in attribs:
					fields.update({'dateModified': False})
				if 'dateExpired' not in attribs:
					fields.update({'dateExpired': False})
			else:
				for attr in attribs:
					fields.update({attr: True})

		if arguments.get('q') is not None:
			# Sets a q query
			qs = arguments.get('q').split(";")
			for q in qs:
				if "==" in q:
					qp = q.split("==")
					query.update({qp[0]:
						{'$in': [self.broker.cast(qp[1])]}
					})
				elif  ":" in q:
					qp = q.split(":")
					query.update({qp[0]:
						{'$in': [self.broker.cast(qp[1])]}
					})
				elif "!=" in q:
					qp = q.split("!=")
					query.update({qp[0]:
						{'$ne': self.broker.cast(qp[1])}
					})
				elif ">=" in q:
					qp = q.split(">=")
					query.update({qp[0]:
						{'$gte': self.broker.cast(qp[1])}
					})
				elif "<=" in q:
					qp = q.split("<=")
					query.update({qp[0]:
						{'$lte': self.broker.cast(qp[1])}
					})
				elif "<" in q:
					qp = q.split("<")
					query.update({qp[0]:
						{'$lt': self.broker.cast(qp[1])}
					})
				elif ">" in q:
					qp = q.split(">")
					query.update({qp[0]:
						{'$gt': self.broker.cast(qp[1])}
					})

		if len(params):
			query.update({"$and": params})

		# Sets the query ordering
		if arguments.get('orderBy') is not None:
			orders = arguments.get('orderBy').split(",")
			for order in orders:
				if order[0] is "!":
					orderBy = -1
					order = order[1:]
				else:
					orderBy = 1
				sort.append((order, orderBy))

		# Prepares the offset
		if arguments.get('offset') is None:
			offset = False
		else:
			offset = int(arguments.get('offset'))

		# Prepares the query limit
		if arguments.get('limit') is None:
			limit = 0
		else:
			limit = int(arguments.get('limit'))

		if fields == {}:
			fields = None

		try:
			# Creates the full query
			if len(sort) and offset:
				data = collection.find(
					query, fields).skip(offset).sort(sort).limit(limit)
			elif offset:
				data = collection.find(
					query, fields).skip(offset).limit(limit)
			elif len(sort):
				data = collection.find(
					query, fields).sort(sort).limit(limit)
			else:
				data= collection.find(query, fields).limit(limit)

			if count_opt:
				# Sets count header
				headers["Count"] = data.count()

			data = list(data)

			if not len(data):
				self.helpers.logger.info(
					self.program + " 404: " + self.helpers.confs["errorMessages"][str(404)]["Description"])

				return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
									{}, False, accepted)
			else:

				# Converts data to unique values
				if unique_opt:
					newData = []
					for i, entity in enumerate(data):
						dataHolder = []
						for attr in entity:
							if isinstance(entity[attr], str):
								dataHolder.append(entity[attr])
							if isinstance(entity[attr], dict):
								dataHolder.append(entity[attr]["value"])
							if isinstance(entity[attr], list):
								dataHolder.append(entity[attr])
						[newData.append(x) for x in dataHolder if x not in newData]
					data = newData

				self.helpers.logger.info(
					self.program + " 200: " + self.helpers.confs["successMessage"][str(200)]["Description"])

				return self.broker.respond(200, data, headers, False, accepted)
		except Exception as e:
			self.helpers.logger.info(
				self.program + " 404: " + self.helpers.confs["errorMessages"][str(404)]["Description"])
			self.helpers.logger.info(str(e))

			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)

	def getData(self, typeof, _id, attrs, accepted=[]):
		""" Gets a specific HIASHDI data entry. """

		collection = self.getCollection(typeof)

		query = {"_id": ObjectId(_id)}

		# Removes the MongoDB ID
		fields = {}

		clear_builtin = False

		attribs = []
		if attrs is not None:
			# Processes attrs parameter
			attribs = attrs.split(",")
			if '*' in attribs:
				# Removes builtin attributes
				if 'dateCreated' not in attribs:
					fields.update({'dateCreated': False})
				if 'dateModified' not in attribs:
					fields.update({'dateModified': False})
				if 'dateExpired' not in attribs:
					fields.update({'dateExpired': False})
			else:
				clear_builtin = True
				for attr in attribs:
					fields.update({attr: True})
		else:
			fields.update({'dateCreated': False})
			fields.update({'dateModified': False})
			fields.update({'dateExpired': False})

		if fields == {}:
			fields = None

		data = list(collection.find(query, fields))

		if not data:
			self.helpers.logger.info(
				self.program + " 404: " + self.helpers.confs["errorMessages"][str(404)]["Description"])

			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)
		elif len(data) > 1:
			self.helpers.logger.info(
				self.program + " 409: " + self.helpers.confs["errorMessages"][str(409)]["Description"])

			return self.broker.respond(409, self.helpers.confs["errorMessages"][str(409)],
								{}, False, accepted)
		else:
			data = data[0]

			if clear_builtin:
				# Clear builtin data
				if "dateCreated" in data and 'dateCreated' not in attribs:
					del data["dateCreated"]
				if "dateModified" in data and 'dateModified' not in attribs:
					del data["dateModified"]
				if "dateExpired" in data and 'dateExpired' not in attribs:
					del data["dateExpired"]

			self.helpers.logger.info(
				self.program + " 200: " + self.helpers.confs["successMessage"][str(200)]["Description"])

			return self.broker.respond(200, data, {}, False, accepted)

	def createData(self, data, typeof, accepted=[]):
		""" Creates a new HIASHDI data entry."""

		collection = self.getCollection(typeof)

		_id = collection.insert(data)

		if str(_id) is not False:
			return self.broker.respond(201, {}, {"Id": str(_id)}, False, accepted)
		else:
			return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
								{}, False, accepted)

	def updateEntityPost(self, _id, typeof, data, options, accepted=[]):
		""" Updates an HIASHDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Data
					- Entity by ID
						- Update or Append Entity Attributes
		"""

		updated = False
		error = False
		_append = False
		_keyValues = False

		if "id" in data:
			del data['id']

		if "type" in data:
			del data['type']

		if options is not None:
			options = options.split(",")
			for option in options:
				_append = True if option == "append" else _append
				_keyValues = True if option == "keyValues" else _keyValues

		if _append:
			entity = list(collection.find({'id': _id}))
			for update in data:
				if update in entity[0]:
					error = True
				else:
					collection.update_one({"id" : _id},
						{"$set": {update: data[update]}}, upsert=True)
					updated = True
		else:
			for update in data:
				collection.update_one({"id" : _id},
							{"$set": {update: data[update]}}, upsert=True)
				updated = True

		if updated and error is False:
			return self.broker.respond(204, self.helpers.confs["successMessage"][str(204)],
								{}, False, accepted)
		else:
			return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
								{}, False, accepted)

	def updateEntityPatch(self, _id, typeof, data, options, accepted=[]):
		""" Updates an HIASHDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Data
					- Entity by ID
						- Update Existing Entity Attributes
		"""

		updated = False
		error = False

		if "id" in data:
			del data['id']

		if "type" in data:
			del data['type']

		_keyValues = False

		if options is not None:
			options = options.split(",")
			for option in options:
				_keyValues = True if option == "keyValues" else keyValues

		entity = list(collection.find({'id': _id}))
		for update in data:
			if update not in entity[0]:
				error = True
			else:
				collection.update_one({"id" : _id},
					{"$set": {update: data[update]}})
				updated = True

		if updated and error is False:
			return self.broker.respond(204, self.helpers.confs["successMessage"][str(204)],
								{}, False, accepted)
		else:
			return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
								{}, False, accepted)

	def updateEntityPut(self, _id, typeof, data, options, accepted=[]):
		""" Updates an HIASHDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Data
					- Entity by ID
						- Replace all entity attributes
		"""

		if "id" in data:
			del data['id']

		if "type" in data:
			del data['type']

		fields = {
			'_id': False,
			'id': False,
			'type': False,
			'dateCreated': False,
			'dateModified': False,
			'dateExpired': False
		}

		updated = False
		_keyValues = False

		if options is not None:
			options = options.split(",")
			for option in options:
				_keyValues = True if option == "keyValues" else _keyValues

		entity = list(collection.find({"id": _id}, fields))

		for e in entity:
			collection.update({"id": _id}, {'$unset': {e: ""}})

		for update in data:
			collection.update_one({"id" : _id},
				{"$set": {update: data[update]}}, upsert=True)
			updated = True

		if updated:
			return self.broker.respond(204, self.helpers.confs["successMessage"][str(204)],
								{}, False, accepted)
		else:
			return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
								{}, False, accepted)

	def deleteEntity(self, typeof, _id, accepted=[]):
		""" Deletes an HIASHDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Data
					- Entity by ID
						- Remove entity
		"""

		if typeof in self.mongodb.collextions:
			collection = self.mongodb.collextions[typeof]
		else:
			return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
								{}, False, accepted)

		deleted = False
		result = collection.delete_one({"id": _id})

		if result.deleted_count == 1:
			self.helpers.logger.info("Mongo data delete OK")
			return self.broker.respond(204, {}, {}, False, accepted)
		else:
			self.helpers.logger.info("Mongo data delete FAILED")
			return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
								{}, False, accepted)

	def getEntityAttribute(self, typeof, _id, _attr, metadata, is_value=False, accepted=[]):
		""" Gets a specific HIASHDI Entity Attribute.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Attribute
					- Attribute by Entity ID
						- Get Attribute Data
		"""

		query = {'id': _id}

		# Removes the MongoDB ID
		fields = {
			'_id': False
		}

		mattribs = []
		if metadata is not None:
			# Processes metadata parameter
			mattribs = metadata.split(",")
			for attr in mattribs:
				fields.update({_attr + "." + attr: True})

		if typeof is not None:
			query.update({"type": typeof})

		entity = list(collection.find(query, fields))

		if not entity:
			self.helpers.logger.info(self.program + " 404: " + \
							self.helpers.confs["errorMessages"][str(404)]["Description"])
			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)
		elif len(entity) > 1:
			self.helpers.logger.info(self.program + " 409: " + \
							self.helpers.confs["errorMessages"][str(409)]["Description"])
			return self.broker.respond(409, self.helpers.confs["errorMessages"][str(409)],
								{}, False, accepted)
		else:
			data = entity[0]

			if _attr not in data:
				self.helpers.logger.info(self.program + " 400: " + \
									self.helpers.confs["errorMessages"]["400b"]["Description"])
				return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
									{}, False, accepted)

			override = False
			data = data[_attr]
			if is_value:
				if "value" not in data:
					self.helpers.logger.info(self.program + " 400: " + \
						self.helpers.confs["errorMessages"]["400b"]["Description"])
					return self.broker.respond(400, self.helpers.confs["errorMessages"]["400b"],
										{}, False, accepted)

				data = data["value"]
				override = "text/plain"

			self.helpers.logger.info(
				self.program + " 200: " + self.helpers.confs["successMessage"][str(200)]["Description"])

			return self.broker.respond(200, data, None, {}, override, accepted)

	def updateEntityAttrPut(self, _id, _attr, typeof, data, is_value, accepted = None, content_type = None):
		""" Updates an HIASHDI Entity Attribute.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Attribute
					- Attribute by Entity ID
						- Update Attribute Data
		"""

		query = {"id": _id}

		if typeof is not None:
			query.update({"type": typeof})

		entity = list(collection.find(query))

		if not entity:
			self.helpers.logger.info(self.program + " 404: " + \
							self.helpers.confs["errorMessages"][str(404)]["Description"])
			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)
		elif len(entity) > 1:
			self.helpers.logger.info(self.program + " 409: " + \
							self.helpers.confs["errorMessages"][str(409)]["Description"])
			return self.broker.respond(409, self.helpers.confs["errorMessages"][str(409)],
								{}, False, accepted)
		elif _attr not in entity[0]:
			self.helpers.logger.info(self.program + " 404: " + \
				self.helpers.confs["errorMessages"][str(404)]["Description"])
			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)
		else:
			if is_value:
				data = data.decode()
				path = _attr + '.value'
				if content_type == "text/plain":
					if '"' in data:
						data = str(data.replace('"', ""))
					elif data == "true":
						data = True
					elif data == "false":
						data = False
					elif data == "null":
						data = None
					else:
						if "." in data:
							try:
								data = float(data)
							except:
								return self.broker.respond(400,
											self.helpers.confs["errorMessages"]["400p"],
											{}, False, accepted)
						else:
							try:
								data = int(float(data))
							except:
								return self.broker.respond(400,
											self.helpers.confs["errorMessages"]["400p"],
											{}, False, accepted)
			else:
				path = _attr

			collection.update_one({"id": _id},
				{"$set": {path: data}}, upsert=True)
			return self.broker.respond(204, self.helpers.confs["successMessage"][str(204)],
								{}, False, accepted)

	def deleteEntityAttribute(self, _id, _attr, typeof, accepted=[]):
		""" Updates an HIASHDI Entity Attribute.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Attribute
					- Attribute by Entity ID
						- Update Attribute Data
		"""

		query = {"id": _id}

		if typeof is not None:
			query.update({"type": typeof})

		entity = list(collection.find(query))

		if not entity:
			self.helpers.logger.info(self.program + " 404: " +
							self.helpers.confs["errorMessages"][str(404)]["Description"])
			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)
		elif len(entity) > 1:
			self.helpers.logger.info(self.program + " 409: " +
							self.helpers.confs["errorMessages"][str(409)]["Description"])
			return self.broker.respond(409, self.helpers.confs["errorMessages"][str(409)],
								{}, False, accepted)
		elif _attr not in entity[0]:
			self.helpers.logger.info(self.program + " 404: " +
							self.helpers.confs["errorMessages"][str(404)]["Description"])
			return self.broker.respond(404, self.helpers.confs["errorMessages"][str(404)],
								{}, False, accepted)
		else:
			collection.update({"id": _id},
						{'$unset': {_attr: ""}})
			return self.broker.respond(204, self.helpers.confs["successMessage"][str(204)],
								{}, False, accepted)

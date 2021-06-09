from flask import Flask, request, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
import os
from bson.json_util import dumps, loads

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetsdb
	
def convertToCSV(data):
	if len(data) < 1:
		return ""
	returnData = ",".join(list(data[0].keys())) + "\n"

	for entry in data:
		returnData += ",".join(entry.values()) + "\n"
	return returnData


class listAll(Resource):
	def get(self, type="JSON"):
		num = request.args.get('top', default=-1, type=int)
		
		if num == -1:
			data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1,'closeTime':1})
		else:
			data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1,'closeTime':1}).limit(num)

		if type == "csv":
			data = convertToCSV(data)
		else:
			data = loads(dumps(data))
		return data

class listOpenOnly(Resource):
	def get(self, type="JSON"):
		num = request.args.get('top', default=-1, type=int)

		if num == -1:
			data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1})
		else:
			data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1}).limit(num)

		if type == "csv":
			data = convertToCSV(data)
		else:
			data = loads(dumps(data))
		return data

class listCloseOnly(Resource):
	def get(self, type="JSON"):	
		num = request.args.get('top', default=-1, type=int)

		if num == -1:
			data = db.brevetsdb.find({}, {'_id': 0, 'closeTime':1})
		else:
			data = db.brevetsdb.find({}, {'_id': 0, 'closeTime':1}).limit(num)

		if type == "csv":
			data = convertToCSV(data)
		else:
			data = loads(dumps(data))
		return data

# Create routes
# Another way, without decorators
api.add_resource(listAll, '/listAll', '/listAll/', '/listAll/<string:type>')
api.add_resource(listOpenOnly, '/listOpenOnly', '/listOpenOnly/', '/listOpenOnly/<string:type>')
api.add_resource(listCloseOnly,'/listCloseOnly', '/listCloseOnly/', '/listCloseOnly/<string:type>')

# Run the application
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)

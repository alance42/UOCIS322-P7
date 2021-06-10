from flask import Flask, request, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
import os
from bson.json_util import dumps, loads
from passlib.hash import sha256_crypt as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetsdb
passdb = client.passwords

SECRET_KEY = 'test1234@#$'
	
def generate_auth_token(userid, expiration=600):
   s = Serializer(SECRET_KEY, expires_in=expiration)
   return s.dumps({'id': userid})


def verify_auth_token(token):
	s = Serializer(SECRET_KEY)
	try:
		data = s.loads(token)
	except SignatureExpired:
		return False, "Token Signature Expired"
	except BadSignature:
		return False, "Bad Token Signature"
	return True, ""

def convertToCSV(data):
	if db.brevetsdb.count_documents({}) < 1:
		return ""
	returnData = ",".join(list(data[0].keys())) + "\n"

	for entry in data:
		returnData += ",".join(entry.values()) + "\n"
	return returnData


class listAll(Resource):
	def get(self, type="JSON"):
		num = request.args.get('top', default=-1, type=int)
		token = request.args.get('token', type=str)
		check, message = verify_auth_token(token)
		if check:
			if num == -1:
				data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1,'closeTime':1})
			else:
				data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1,'closeTime':1}).limit(num)

			if type == "csv":
				data = convertToCSV(data)
			else:
				data = loads(dumps(data))
			return data
		else:
			return {"message": message}, 401

class listOpenOnly(Resource):
	def get(self, type="JSON"):
		num = request.args.get('top', default=-1, type=int)
		token = request.args.get('token', type=str)
		
		check, message = verify_auth_token(token)
		if check:
			if num == -1:
				data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1})
			else:
				data = db.brevetsdb.find({}, {'_id': 0, 'startTime': 1}).limit(num)

			if type == "csv":
				data = convertToCSV(data)
			else:
				data = loads(dumps(data))
			return data
		else:
			return {"message": message}, 401

class listCloseOnly(Resource):
	def get(self, type="JSON"):	
		num = request.args.get('top', default=-1, type=int)
		token = request.args.get('token', type=str)

		check, message = verify_auth_token(token)
		if check:
			if num == -1:
				data = db.brevetsdb.find({}, {'_id': 0, 'closeTime':1})
			else:
				data = db.brevetsdb.find({}, {'_id': 0, 'closeTime':1}).limit(num)

			if type == "csv":
				data = convertToCSV(data)
			else:
				data = loads(dumps(data))
			return data
		else:
			return {"message": message}, 401


class register(Resource):
	def post(self):
		username = request.args.get('user', type=str)
		password = request.args.get('hashedPass', type=str)
		doubleHash = pwd_context.using(rounds = 12345, salt = "Thisisaverylong").hash(password)

		if passdb.passwords.find_one({"username": username}) == None:
			uniqueID = passdb.passwords.count_documents({})
			passdb.passwords.insert_one({"id": uniqueID, "username": username, "password": doubleHash})
			return {"id": uniqueID, "username": username}, 201

		return {"message": "Username already in use"}, 400

class token(Resource):
	def get(self):
		username = request.args.get('user', type=str)
		checkPass = request.args.get('hashedPass', type=str)
		tokenTime = 30

		if passdb.passwords.find_one({"username": username}) != None:
			user = passdb.passwords.find_one({"username": username})
			if pwd_context.verify(checkPass, user["password"]):
				token = generate_auth_token(user["id"], tokenTime)
				return {"id": user["id"], "token": token.decode('utf-8'), "duration": tokenTime}, 201
		else:
			return  {"message": "Failed to login"}, 401

		

# Create routes
# Another way, without decorators
api.add_resource(listAll, '/listAll', '/listAll/', '/listAll/<string:type>')
api.add_resource(listOpenOnly, '/listOpenOnly', '/listOpenOnly/', '/listOpenOnly/<string:type>')
api.add_resource(listCloseOnly,'/listCloseOnly', '/listCloseOnly/', '/listCloseOnly/<string:type>')
api.add_resource(register,'/register', '/register/')
api.add_resource(token,'/token', '/token/')

# Run the application
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)

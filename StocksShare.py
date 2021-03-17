from flask import Flask, Response, render_template
from flask_restful import Api, Resource, reqparse
from passlib.hash import sha256_crypt
from yahoo_fin import stock_info
import yfinance
import secrets
import sqlite3
import re
import json
import yagmail

ADMIN_EMAIL_ADDRESS = ""
ADMIN_EMAIL_PASSWORD = ""

SQLITE_DATABASE = "database/MyShare.db"

MAX_USER_ID = 1000000000000
MAX_ID = 1000000000000000

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_CONFLICT = 409
HTTP_INTERNAL_SERVER_ERROR = 500

AUTHENTICATION_FAILED = 1000
OWNERSHIP_AUTHENTICATION_FAILED = 1001
TOO_MANY_AUTHENTICATION_ATTEMPTS = 1002

BOUGHT_SOLD_DISCREPANCY = 2000

MISSING_REQUIRED_PARAMS = 10000
MISSING_ID_PARAM = 10001
MISSING_PASSWORD_PARAM = 10002
MISSING_NEW_PASSWORD_PARAM = 10003
MISSING_RESET_CODE_PARAM = 10004
MISSING_USERNAME_PARAM = 10005
MISSING_EMAIL_PARAM = 10006
MISSING_FIRST_NAME_PARAM = 10007
MISSING_LAST_NAME_PARAM = 10008
MISSING_SYMBOL_PARAM = 10009
MISSING_SHARES_PARAM = 10010
MISSING_BUY_PRICE_PARAM = 10011
MISSING_BUY_DATE_PARAM = 10012
MISSING_SELL_PRICE_PARAM = 10013
MISSING_SELL_DATE_PARAM = 10014
MISSING_LOT_ID_PARAM = 10015
MISSING_SELL_LOT_ID_PARAM = 10016

INVALID_PASSWORD_PARAM = 20002
INVALID_NEW_PASSWORD_PARAM = 20003
INVALID_USERNAME_PARAM = 20005
INVALID_EMAIL_PARAM = 20006
INVALID_FIRST_NAME_PARAM = 20007
INVALID_LAST_NAME_PARAM = 20008
INVALID_SYMBOL_PARAM = 20009
INVALID_SHARES_PARAM = 20010
INVALID_BUY_PRICE_PARAM = 20011
INVALID_BUY_DATE_PARAM = 20012
INVALID_SELL_PRICE_PARAM = 20013
INVALID_SELL_DATE_PARAM = 20014

USERNAME_ALREADY_TAKEN = 30005
EMAIL_ALREADY_TAKEN = 30006

app = Flask(__name__)
StocksShare = Api(app)


# email must be in valid format (xxx@xxx.xxx) and can't be longer than 100 characters
emailRegex = '^(?=.{1,100}$)[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
def checkEmailFormat(email):
    return re.search(emailRegex, email)

# username can only contain letters, numbers, periods and underscores and must be 6-25 characters long
usernameRegex = '^(?=.{6,25}$)[a-zA-Z0-9._]+$'
def checkUsernameFormat(username):
    return re.search(usernameRegex, username)

# password must be between 8 and 50 characters
def checkPasswordFormat(password):
	return len(password) >= 8 and len(password) <= 50

# name can't be longer than 25 characters and can only contain letters, periods, and spaces
nameRegex = '^(?=.{1,25}$)[a-zA-Z.( )]+$'
def checkNameFormat(name):
    return re.search(nameRegex, name)

# must be a positive integer or a positive float with exactly one or two digits after the decimal
dollarRegex = '^\d+\.\d\d$|^\d+\.\d$|^\d+$'
def checkDollarFormat(dollar):
    return re.search(dollarRegex, dollar)

# must be a valid date in the format YYYY-MM-DD
dateRegex = '^\d\d\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])$'
def checkDateFormat(date):
    return re.search(dateRegex, date)

# must be a positive integer
intRegex = '^\d+$'
def checkIntFormat(integer):
    return re.search(intRegex, integer)

# must be 1 to 5 letters
symbolRegex = '^(?=.{1,5}$)[a-zA-Z]+$'
def checkSymbolFormat(symbol):
    return re.search(symbolRegex, symbol)

def executeDatabaseQuery(query):
	connection = sqlite3.connect(SQLITE_DATABASE)
	cursor = connection.cursor()
	results = cursor.execute(query).fetchall()
	connection.commit()
	connection.close()
	return results

def executeDatabaseUpdate(statement):
	connection = sqlite3.connect(SQLITE_DATABASE)
	cursor = connection.cursor()
	cursor.execute("PRAGMA foreign_keys = ON;")
	cursor.execute(statement)
	connection.commit()
	connection.close()
	return cursor

def usernameAvailable(username):
	if not checkUsernameFormat(username):
		return False
	query = "SELECT COUNT(*) FROM Users WHERE Username = '{}';".format(username)
	result = executeDatabaseQuery(query)
	return result[0][0] == 0

def userOwnsUsername(id, username):
	query = "SELECT COUNT(*) FROM Users WHERE ID = {} AND Username = '{}';".format(id, username);
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def emailAvailable(email):
	if not checkEmailFormat(email):
		return False
	query = "SELECT COUNT(*) FROM Users WHERE Email = '{}';".format(email)
	result = executeDatabaseQuery(query)
	return result[0][0] == 0

def userOwnsEmail(id, email):
	query = "SELECT COUNT(*) FROM Users WHERE ID = {} AND Email = '{}';".format(id, email);
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def matchIdAndPassword(id, password):
	if not checkIntFormat(id):
		return False
	query = "SELECT Password FROM Users WHERE ID = '{}';".format(id)
	result = executeDatabaseQuery(query)
	if result == []:
		return False
	return sha256_crypt.verify(password, result[0][0])

def symbolHeldByUser(symbol, userId):
	if not symbolExists(symbol):
		return False
	query = "SELECT COUNT(*) FROM Holdings WHERE User = {} AND Symbol = '{}' AND SellLotID IS NULL;".format(userId, symbol)
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def lotOwnedByUser(lotId, userId):
	if not checkIntFormat(lotId) or not checkIntFormat(userId):
		return False
	query = "SELECT COUNT(*) FROM Holdings WHERE LotID = {} AND User = {};".format(lotId, userId)
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def lotHeldByUser(lotId, userId):
	if not checkIntFormat(lotId) or not checkIntFormat(userId):
		return False
	query = "SELECT COUNT(*) FROM Holdings WHERE LotID = {} AND User = {} AND SellLotID IS NULL;".format(lotId, userId)
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def lotSoldByUser(sellLotId, userId):
	if not checkIntFormat(sellLotId) or not checkIntFormat(userId):
		return False
	query = "SELECT COUNT(*) FROM Holdings WHERE SellLotID = {} AND User = {};".format(sellLotId, userId)
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def shareHeldByUser(shareId, userId):
	if not checkIntFormat(shareId) or not checkIntFormat(userId):
		return False
	query = "SELECT COUNT(*) FROM Holdings WHERE ShareId = {} AND User = {} AND SellLotID IS NULL;".format(shareId, userId)
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def shareSoldByUser(shareId, userId):
	if not checkIntFormat(shareId) or not checkIntFormat(userId):
		return False
	query = "SELECT COUNT(*) FROM Holdings WHERE ShareID = {} AND User = {} AND SellLotID IS NOT NULL;".format(shareId, userId)
	result = executeDatabaseQuery(query)
	return result[0][0] != 0

def symbolExists(symbol):
	if not checkSymbolFormat(symbol):
		return False
	try:
		price = stock_info.get_live_price(symbol)
		info = yfinance.Ticker(symbol)
		info.info.update({ "currentPrice" : price })
	except:
		return False
	return True

def createUserId():
	while True:
		id = secrets.randbelow(MAX_USER_ID)
		query = "SELECT COUNT(*) FROM Users WHERE ID = {};".format(id)
		result = executeDatabaseQuery(query)
		if result[0][0] == 0:
			return id

def createShareId():
	while True:
		id = secrets.randbelow(MAX_ID)
		query = "SELECT COUNT(*) FROM Holdings WHERE ID = {};".format(id)
		result = executeDatabaseQuery(query)
		if result[0][0] == 0:
			return id

def createShareIds(numberOfShares):
	shareIds = []
	for i in range(numberOfShares):
		ShareIdUnique = False
		while not ShareIdUnique:
			shareId = secrets.randbelow(MAX_ID)
			query = "SELECT COUNT(*) FROM Holdings WHERE ShareID = {};".format(shareId)
			result = executeDatabaseQuery(query)
			if result[0][0] == 0 and shareId not in shareIds:
				shareIds.append(shareId)
				ShareIdUnique = True
	return shareIds

def createLotId():
	while True:
		id = secrets.randbelow(MAX_ID)
		query = "SELECT COUNT(*) FROM Holdings WHERE LotID = {};".format(id)
		result = executeDatabaseQuery(query)
		if result[0][0] == 0:
			return id

def createSellLotId():
	while True:
		id = secrets.randbelow(MAX_ID)
		query = "SELECT COUNT(*) FROM Holdings WHERE SellLotID = {};".format(id)
		result = executeDatabaseQuery(query)
		if result[0][0] == 0:
			return id

def createPasswordResetEmail(firstName, username, resetCode):
	return """
			<!DOCTYPE html>
			<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
			<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Poppins">
			<body style="background-color:#191919;font-size:16px;font-family:'Poppins', 'Helvetica Neue', sans-serif;">
				<div style="background-color:#464646;background:linear-gradient(0deg, #232323 0%, #5A5A5A 100%);Margin:0px auto;max-width:600px;">
					<div style="color:#24A292;font-size:25px;width:40%;margin-left:30%;">
						<a href="http://localhost:1817/myshare/home" style="text-decoration:none;">
							<div style="width:100%;background-color: #353535;background: linear-gradient(0deg, #1D1D1D 0%, #353535 100%);color:#24A292;font-size:25px;text-align:center;padding-top:10px;padding-bottom:10px;border:2px solid #24A292;border-radius:10px;cursor:pointer;">MyShare</div>
						</a>
					</div>
					<div style="width:90%;margin-left:5%;border-bottom:2px solid #24A292;">
						<div style="color:#C4C4C4;width:90%;margin-left:5%;margin-bottom:15px;font-size:18px;font-weight:bolder;">Hi {},</div>
						<div style="color:#FFFDFD;width:90%;margin-left:5%;">You have requested to reset your MyShare password. If this was not you, please ignore this email.</div>
					</div>
					<div style="width:90%;margin-left:5%;border-bottom:2px solid #24A292;">
						<div style="color:#FFFDFD;width:90%;margin-left:5%;margin-bottom:5px;">Here is the information you will need to reset your password:</div>
						<div style="color:#C4C4C4;width:90%;margin-left:5%;">Username: <span style="color:#FFFDFD;font-weight:bolder;">{}</span><br><span>Password Reset Code: </span><span style="font-weight:bolder;color:#FF3200">{}</span></div>
					</div>
					<div style="width:36%;margin-left:32%;">
						<a href="http://localhost:1817/myshare/recover-password" style="text-decoration:none;">
							<div style="width:100%;margin-bottom:10px;padding-top:10px;padding-bottom:10px;background-color:#24A292;background:linear-gradient(90deg, #24A292 0%, #247da2 100%);color:#FFFDFD;border-radius:45px;text-align:center;cursor:pointer;">Reset Password</div>
						</a>
					</div>
				</div>
			</body>
			</html>
			""".format(firstName, username, resetCode)


class Info(Resource):

	# get general information of a symbol including current price, previous close, name, business summary, etc.
	#
	# param : "symbol" the symbol whose info will be returned (required)
	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("symbol")
		params = parser.parse_args()

		if params["symbol"] is None:
			return Response(json.dumps({ "error" : MISSING_SYMBOL_PARAM, "message" : "'symbol' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		try:
			price = round(stock_info.get_live_price(params["symbol"]), 2)
			info = yfinance.Ticker(params["symbol"])
			info.info.update({ "currentPrice" : price })
			return Response(json.dumps(info.info), status=HTTP_OK, mimetype="application/json")
		except:
			return Response(json.dumps({ "error" : INVALID_SYMBOL_PARAM, "message" : "Invalid symbol" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

class ID(Resource):

	# get a user's id
	#
	# param : "username" the user's username (required)
	# param : "password" the user's password (required)
	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("username")
		parser.add_argument("password")
		params = parser.parse_args()

		if params["username"] is None:
			return Response(json.dumps({ "error" : MISSING_USERNAME_PARAM, "message" : "'username' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["password"] is None:
			return Response(json.dumps({ "error" : MISSING_PASSWORD_PARAM, "message" : "'password' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkUsernameFormat(params["username"]) or not checkPasswordFormat(params["password"]):
			return Response(json.dumps({ "id" : None }), status=HTTP_OK, mimetype="application/json")

		query = "SELECT Password, ID FROM Users WHERE Username = '{}';".format(params["username"])
		result = executeDatabaseQuery(query)
		if result == []:
			return Response(json.dumps({ "id" : None }), status=HTTP_OK, mimetype="application/json")

		if sha256_crypt.verify(params["password"], result[0][0]):
			return Response(json.dumps({ "id" : result[0][1] }), status=HTTP_OK, mimetype="application/json")

		return Response(json.dumps({ "id" : None }), status=HTTP_OK, mimetype="application/json")


class User(Resource):

	# get a user's username, email, first name, and last name
	#
	# param : "id" the user's id (required)
	# param : "password" the user's password (required)
	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("id")
		parser.add_argument("password")
		params = parser.parse_args()

		if params["id"] is None:
			return Response(json.dumps({ "error" : MISSING_ID_PARAM, "message" : "'id' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["password"] is None:
			return Response(json.dumps({ "error" : MISSING_PASSWORD_PARAM, "message" : "'password' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkIntFormat(params["id"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")
		if not checkPasswordFormat(params["password"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		query = "SELECT Password, Username, Email, FirstName, LastName FROM Users WHERE ID = {};".format(params["id"])
		result = executeDatabaseQuery(query)
		if result == []:
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if sha256_crypt.verify(params["password"], result[0][0]):
			return Response(json.dumps({ "username" : result[0][1], "email" : result[0][2], "firstName" : result[0][3], "lastName" : result[0][4] }), status=HTTP_OK, mimetype="application/json")

		return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")


	# register a user
	#
	# param : "username" the user's username (required)
	# param : "password" the user's password (required)
	# param : "email" the user's email (required)
	# param : "firstName" the user's first name (required)
	# param : "lastName" the user's last name (required)
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("username")
		parser.add_argument("password")
		parser.add_argument("email")
		parser.add_argument("firstName")
		parser.add_argument("lastName")
		params = parser.parse_args()

		if params["username"] is None:
			return Response(json.dumps({ "error" : MISSING_USERNAME_PARAM, "message" : "'username' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["password"] is None:
			return Response(json.dumps({ "error" : MISSING_PASSWORD_PARAM, "message" : "'password' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["email"] is None:
			return Response(json.dumps({ "error" : MISSING_EMAIL_PARAM, "message" : "'email' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["firstName"] is None:
			return Response(json.dumps({ "error" : MISSING_FIRST_NAME_PARAM, "message" : "'firstName' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["lastName"] is None:
			return Response(json.dumps({ "error" : MISSING_LAST_NAME_PARAM, "message" : "'lastName' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkUsernameFormat(params["username"]):
			return Response(json.dumps({ "error" : INVALID_USERNAME_PARAM, "message" : "Invalid username" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkPasswordFormat(params["password"]):
			return Response(json.dumps({ "error" : INVALID_PASSWORD_PARAM, "message" : "Invalid Password" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkEmailFormat(params["email"]):
			return Response(json.dumps({ "error" : INVALID_EMAIL_PARAM, "message" : "Invalid email" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkNameFormat(params["firstName"]):
			return Response(json.dumps({ "error" : INVALID_FIRST_NAME_PARAM, "message" : "Invalid first name" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkNameFormat(params["lastName"]):
			return Response(json.dumps({ "error" : INVALID_LAST_NAME_PARAM, "message" : "Invalid last name" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not usernameAvailable(params["username"]):
			return Response(json.dumps({ "error" : USERNAME_ALREADY_TAKEN, "message" : "Username is already taken" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if not emailAvailable(params["email"]):
			return Response(json.dumps({ "error" : EMAIL_ALREADY_TAKEN, "message" : "Email is already taken" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		id = createUserId()
		password = sha256_crypt.encrypt(params["password"])
		statement = "INSERT OR IGNORE INTO Users (ID, Username, Password, Email, FirstName, LastName) VALUES ({}, '{}', '{}', '{}', '{}', '{}');".format(id, params["username"], password, params["email"], params["firstName"], params["lastName"])
		update = executeDatabaseUpdate(statement)
		if update.rowcount == 0:
			return Response(json.dumps({ "message" : "Internal Server Error" }), status=HTTP_INTERNAL_SERVER_ERROR, mimetype="application/json")
		return Response(json.dumps({ "id" : id }), status=HTTP_OK, mimetype="application/json")


	# edit a user's information
	#
	# param : "id" the user's id (required)
	# param : "password" the user's password (required)
	# param : "username" the user's new username (*)
	# param : "newPassword" the user's new password (*)
	# param : "email" the user's new email (*)
	# param : "firstName" the user's new first name (*)
	# param : "lastName" the user's new last name (*)
	#
	# (*) at least one of these parameters is required
	def patch(self):
		parser = reqparse.RequestParser()
		parser.add_argument("id")
		parser.add_argument("password")
		parser.add_argument("username")
		parser.add_argument("newPassword")
		parser.add_argument("email")
		parser.add_argument("firstName")
		parser.add_argument("lastName")
		params = parser.parse_args()

		if params["id"] is None:
			return Response(json.dumps({ "error" : MISSING_ID_PARAM, "message" : "'id' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["password"] is None:
			return Response(json.dumps({ "error" : MISSING_PASSWORD_PARAM, "message" : "'password' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkIntFormat(params["id"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if not checkPasswordFormat(params["password"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if not matchIdAndPassword(params["id"], params["password"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		updates = ""

		if params["username"] is not None:
			if not checkUsernameFormat(params["username"]):
				return Response(json.dumps({ "error" : INVALID_USERNAME_PARAM, "message" : "Invalid username" }), status=HTTP_BAD_REQUEST, mimetype="application/json")
			updates += ", Username = '{}'".format(params["username"])

		if params["email"] is not None:
			if not checkEmailFormat(params["email"]):
				return Response(json.dumps({ "error" : INVALID_EMAIL_PARAM, "message" : "Invalid email" }), status=HTTP_BAD_REQUEST, mimetype="application/json")
			updates += ", Email = '{}'".format(params["email"])

		if params["newPassword"] is not None:
			if not checkPasswordFormat(params["newPassword"]):
				return Response(json.dumps({ "error" : INVALID_NEW_PASSWORD_PARAM, "message" : "Invalid new password" }), status=HTTP_BAD_REQUEST, mimetype="application/json")
			updates += ", Password = '{}'".format(sha256_crypt.encrypt(params["newPassword"]))

		if params["firstName"] is not None:
			if not checkNameFormat(params["firstName"]):
				return Response(json.dumps({ "error" : INVALID_FIRST_NAME_PARAM, "message" : "Invalid first name" }), status=HTTP_BAD_REQUEST, mimetype="application/json")
			updates += ", FirstName = '{}'".format(params["firstName"])

		if params["lastName"] is not None:
			if not checkNameFormat(params["lastName"]):
				return Response(json.dumps({ "error" : INVALID_LAST_NAME_PARAM, "message" : "Invalid last name" }), status=HTTP_BAD_REQUEST, mimetype="application/json")
			updates += ", LastName = '{}'".format(params["lastName"])

		if params["username"] is not None:
			if not usernameAvailable(params["username"]) and not userOwnsUsername(params["id"], params["username"]):
				return Response(json.dumps({ "error" : USERNAME_ALREADY_TAKEN, "message" : "Username is already taken" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if params["email"] is not None:
			if not emailAvailable(params["email"]) and not userOwnsEmail(params["id"], params["email"]):
				return Response(json.dumps({ "error" : EMAIL_ALREADY_TAKEN, "message" : "Email is already taken" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if len(updates) == 0:
			return Response(json.dumps({ "error" : MISSING_REQUIRED_PARAMS, "message" : "'username' and/or 'newPassword' and/or 'email' and/or 'firstName' and/or 'lastName' parameter(s) required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		statement = "UPDATE Users SET {} WHERE ID = {};".format(updates[2:], params["id"])
		update = executeDatabaseUpdate(statement)
		if update.rowcount == 0:
			return Response(json.dumps({ "message" : "Internal Server Error" }), status=HTTP_INTERNAL_SERVER_ERROR, mimetype="application/json")

		query = "SELECT Username, Email, FirstName, LastName FROM Users WHERE ID = {};".format(params["id"])
		result = executeDatabaseQuery(query)

		if result == []:
			return Response(json.dumps({ "message" : "Internal Server Error" }), status=HTTP_INTERNAL_SERVER_ERROR, mimetype="application/json")

		return Response(json.dumps({ "username" : result[0][0], "email" : result[0][1], "firstName" : result[0][2], "lastName" : result[0][3] }), status=HTTP_OK, mimetype="application/json")


	# remove a user and all of their data
	#
	# param : "id" the user's id (required)
	# param : "password" the user's password (required)
	def delete(self):
		parser = reqparse.RequestParser()
		parser.add_argument("id")
		parser.add_argument("password")
		params = parser.parse_args()

		if params["id"] is None:
			return Response(json.dumps({ "error" : MISSING_ID_PARAM, "message" : "'id' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if params["password"] is None:
			return Response(json.dumps({ "error" : MISSING_PASSWORD_PARAM, "message" : "'password' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		if not checkIntFormat(params["id"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if not checkPasswordFormat(params["password"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		if not matchIdAndPassword(params["id"], params["password"]):
			return Response(json.dumps({ "error" : AUTHENTICATION_FAILED, "message" : "Id and password do not match" }), status=HTTP_FORBIDDEN, mimetype="application/json")

		statement = "DELETE FROM Users WHERE ID = {};".format(params["id"])
		delete = executeDatabaseUpdate(statement)
		if delete.rowcount == 0:
			return Response(json.dumps({ "message" : "Internal Server Error" }), status=HTTP_INTERNAL_SERVER_ERROR, mimetype="application/json")

		return Response(json.dumps({ "id" : params["id"] }), status=HTTP_OK, mimetype="application/json")


class SymbolPage(Resource):
	def get(self):
		return Response(render_template("symbol.html"), status=HTTP_OK, mimetype="text/html")

class HomePage(Resource):
	def get(self):
		return Response(render_template("home.html"), status=HTTP_OK, mimetype="text/html")

class LoginPage(Resource):
	def get(self):
		return Response(render_template("login.html"), status=HTTP_OK, mimetype="text/html")

class RegisterPage(Resource):
	def get(self):
		return Response(render_template("register.html"), status=HTTP_OK, mimetype="text/html")

class RecoverPasswordPage(Resource):
	def get(self):
		return Response(render_template("recover-password.html"), status=HTTP_OK, mimetype="text/html")

class ResetPasswordPage(Resource):
	def get(self):
		return Response(render_template("reset-password.html"), status=HTTP_OK, mimetype="text/html")

class AccountSettingsPage(Resource):
	def get(self):
		return Response(render_template("account-settings.html"), status=HTTP_OK, mimetype="text/html")

class ChangePasswordPage(Resource):
	def get(self):
		return Response(render_template("change-password.html"), status=HTTP_OK, mimetype="text/html")

class DeleteAccountPage(Resource):
	def get(self):
		return Response(render_template("delete-account.html"), status=HTTP_OK, mimetype="text/html")



StocksShare.add_resource(Info,"/StocksShare/info")
StocksShare.add_resource(User,"/StocksShare/user")
StocksShare.add_resource(ID,"/StocksShare/user/id")
StocksShare.add_resource(HomePage, "/StocksShare/home")
StocksShare.add_resource(SymbolPage, "/StocksShare/symbol")
StocksShare.add_resource(LoginPage, "/StocksShare/login")
StocksShare.add_resource(RegisterPage, "/StocksShare/register")
StocksShare.add_resource(RecoverPasswordPage, "/StocksShare/recover-password")
StocksShare.add_resource(ResetPasswordPage, "/StocksShare/reset-password")
StocksShare.add_resource(AccountSettingsPage, "/StocksShare/account-settings")
StocksShare.add_resource(ChangePasswordPage, "/StocksShare/change-password")
StocksShare.add_resource(DeleteAccountPage, "/StocksShare/delete-account")

if __name__ == '__main__':
	app.run(port=5000)

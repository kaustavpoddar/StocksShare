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


class Price(Resource):

	# get current price a symbol
	#
	# param : "symbol" the symbol whose price will be returned (required)
	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("symbol")
		params = parser.parse_args()

		if params["symbol"] is None:
			return Response(json.dumps({ "error" : MISSING_SYMBOL_PARAM, "message" : "'symbol' parameter required" }), status=HTTP_BAD_REQUEST, mimetype="application/json")

		try:
			return Response(json.dumps({ "price" : round(stock_info.get_live_price(params["symbol"]), 2) }), status=HTTP_OK, mimetype="application/json")
		except:
			return Response(json.dumps({ "error" : INVALID_SYMBOL_PARAM, "message" : "Invalid symbol" }), status=HTTP_BAD_REQUEST, mimetype="application/json")


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

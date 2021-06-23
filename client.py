# port number 5016
# run this on cs2s! Not on your computer you numpty.
from flask import Flask,jsonify,request,Response, render_template, flash, redirect, make_response, url_for, session
from flaskext.mysql import MySQL
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os
import json
restServer = Flask(__name__)
mysql = MySQL()
UPLOAD_FOLDER = '/home/samuel.hobman/htdocs/advancedWebDev/static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # We're not getting text files downloaded. Or javascript files.
restServer.config['MYSQL_DATABASE_USER'] = 'samuel.hobman'
restServer.config['MYSQL_DATABASE_PASSWORD'] = 'xm8s4XAGwtXru2Dy' # Really, this should be an environemnt variable.
restServer.config['MYSQL_DATABASE_DB'] = 'samuelhobman_restServer'
restServer.config['MYSQL_DATABASE_HOST'] = 'ysjcs.net'
restServer.config['MYSQL_DATABASE_PORT'] = 3306
restServer.config['MYSQL_DATABASE_CHARSET'] = 'utf8'
restServer.config['SECRET_KEY'] = 'debugPass' # required for forms. Should be an environment variable.
restServer.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Directs images to the static folder, which is useful for template rendering.
mysql.init_app(restServer)
conn = mysql.connect()
cursor = conn.cursor()
class UploadForm(FlaskForm):
	snakeType = StringField('SnakeType', validators=[DataRequired()])
	snakeName = StringField('Snake Name', validators=[DataRequired()])
	snakeDescription = StringField('Snake Description', validators=[DataRequired()])
	snakeImage = FileField('Snake Image', validators=[FileRequired(),FileAllowed(['jpg', 'png'], 'Images only!')]) # last argument is a failure warning.
	submit = SubmitField("Submit Here")
class LoginForm(FlaskForm):
	userName = StringField('Username', validators=[DataRequired()])
	passWord = PasswordField('Password', validators=[DataRequired()])
	submitt = SubmitField('Sign In')
class DeleteForm(FlaskForm):
	reptileID = IntegerField("Repitle ID", validators=[DataRequired()])
	submit = SubmitField("Delete reptile")
class ViewForm(FlaskForm):
	reptileName = StringField("Reptile Name", validators=[DataRequired()])
	submit = SubmitField("Search for reptile.")
class UpdateForm(FlaskForm):
	reptileID = IntegerField("Repitle ID", validators=[DataRequired()])
	snakeType = StringField('SnakeType', validators=[DataRequired()])
	snakeName = StringField('Snake Name', validators=[DataRequired()])
	snakeDescription = StringField('Snake Description', validators=[DataRequired()])
	submit = SubmitField("Update the reptile. Make sure you have the right ID, please.")
@restServer.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	return response
@restServer.route("/")
def home():
	if session.get("username") == 'admin':
		flash("You are currently logged in as the admin.") #
	return render_template('home.html')
@restServer.route("/dbsend", methods=['GET', 'POST']) # because of forms, we need to have both permissions.
def sendData():
	if session.get("username") == 'admin': #primitive security measures.
		form = UploadForm()
		if form.validate_on_submit(): # this is only accessed if the page sends a valid wtform.
			type = form.snakeType.data # grab values from the website.
			name = form.snakeName.data # worth noting that this will never be empty.
			description = form.snakeDescription.data
			snakePhoto = form.snakeImage.data
			filename = secure_filename(snakePhoto.filename)
			snakePhoto.save(os.path.join(restServer.config['UPLOAD_FOLDER'], filename))
			insert_stmt = (
		 	"INSERT INTO reptileData (reptileType, reptileName, reptileDescription, pathToImage) "
	     	"VALUES (%s, %s, %s, %s)" # This actually prepares the SQL statement. Even something as bizarre as "); wouldn't work.
	   		)
	   		data = (type, name, description, filename)
	   		cursor.execute(insert_stmt, data)
	   		conn.commit()
			flash("Form created successfully!") # Flash gives feedback on the next viewed page with flash messages enabled. Useful.
			return redirect('/') # Redirect them home.
		return render_template('sendData.html', form=form) # form=form is weird, but works. Effectively shows
	else:
		flash("You're not logged in. Please log in before attempting this again.")
		return redirect('/login')
	#return jsonify(data)
@restServer.route("/dbdelete", methods=['GET', 'POST'])
def deleteData():
	if session.get("username") == 'admin':
		form = DeleteForm()
		if form.validate_on_submit():
			reptileID = form.reptileID.data
			delete_stmt = (
			"DELETE FROM reptileData WHERE reptileID = %s "
			)
			cursor.execute(delete_stmt, reptileID)
			conn.commit()
			if cursor.rowcount != 0:
				flash("Row deleted successfully.")
				return redirect('/')
			else:
				flash("Something went wrong.")
				return redirect('/')
		return render_template('deleteData.html', form=form)
	else:
		return redirect('/login')
@restServer.route("/dbget", methods=['GET', 'POST'])
def getData():
	form = ViewForm() # given the safety, it should be fine letting use use SQL. They also don't need to be admin.
	if form.validate_on_submit():
		resultList = []
		search_stmt =  (
		"SELECT * FROM reptileData WHERE reptileName = %s "
		)
		data = form.reptileName.data
		cursor.execute(search_stmt, data)
		result = cursor.fetchall()
		if cursor.rowcount <= 0:
			flash("No reptiles with that ID were found!")
		for k in result:
			riderslist = {'reptileID' : k[0], 'reptileType' : k[1], 'reptileName' : k[2], 'reptileDescription' : k[3], 'pathToImage' : k[4] }  # This is easier to use when passed to the template.
			resultList.append(riderslist)
			resultList = json.dumps(resultList)
			return render_template('results.html', data = resultList, form = form)
	return render_template('results.html', form=form)
@restServer.route("/dbUpdate", methods=['GET', 'POST'])
def updateData():
	if session.get("username") == 'admin': # This is extremely primitive. However, for the first model it works.
		form = UpdateForm()
		if form.validate_on_submit():
			reptileID = form.reptileID.data
			reptileType = form.snakeType.data
			reptileName = form.snakeName.data
			reptileDescription = form.snakeDescription.data
				# I assume the path doesn't change. Otherwise, deleting the reptile and restarting would be preferable.
			update_stmt = (
			"UPDATE reptileData SET reptileType = %s, reptileName = %s, reptileDescription = %s WHERE reptileID = %s"
			)
			data = (reptileType, reptileName, reptileDescription, reptileID)
			cursor.execute(update_stmt, data)
			conn.commit()
			flash("Updated succesfully.")
			return redirect("/")
		return render_template('updateData.html', form=form)
	else:
		return redirect('/login')
@restServer.route("/login", methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		userName = form.userName.data
		passWord = form.passWord.data
		if userName == 'Admin' and passWord == 'Debug': # this should be replaced with OAuth. We don't have access to it.
			session['username'] = 'admin' # This disappears on client reopening!
			flash("Welcome back, admin.")
		else:
			flash("That isn't the right login or password. Try again?")
		return redirect("/")
	return render_template('login.html', form=form)
if __name__ == '__main__':
        print("== Running in debug mode ==")
        restServer.run(host='ysjcs.net', port=5016, debug=True)

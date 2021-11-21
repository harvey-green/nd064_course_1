import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# global variable used to count the number of open db connections
ccount = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global ccount
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    ccount = ccount + 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global ccount
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    ccount = ccount - 1
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    global ccount
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    ccount = ccount - 1
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    
    app.logger.info('Article "' + post['title'] + '" retrieved!')
    
    if post is None:
      return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global ccount
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            ccount = ccount - 1

            return redirect(url_for('index'))

    return render_template('create.html')
    
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    #app.logger.info('Status request successfull')
    return response

@app.route('/metrics')
def metrics():
    global ccount
    connection = get_db_connection()
    postCountQuery = connection.execute("select count(*) from posts")
    postCountData = postCountQuery.fetchone()
    postCount = postCountData[0]
    connection.close()
    ccount = ccount - 1
    
    response = app.response_class(
            response=json.dumps({"db_connection_count":ccount,"post_count":postCount}),
            status=200,
            mimetype='application/json'
    )

    #app.logger.info('Metrics request successfull')
    return response
    

# start the application on port 3111
if __name__ == "__main__":
    
    ## log to both stdout and stderr
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',datefmt='%d/%m/%Y, %H:%M:%S')
    stdErrHandler = logging.StreamHandler(sys.stderr)
    app.logger.addHandler(stdErrHandler)
    
    app.run(host='0.0.0.0', port='3111')

import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    try:
        connection = sqlite3.connect('database.db')
        connection.row_factory = sqlite3.Row
        app.config['DB_CONN_COUNTER'] = app.config['DB_CONN_COUNTER'] + 1
    except:
        connection = None
        app.logger.error('Error opening database connection!')
        
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    if connection is None:
        post = None
    else:
        post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
        connection.close()
        
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# flash config variable used to count the number of db connections
app.config['DB_CONN_COUNTER'] = 0

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
        
    if post is None:
        app.logger.error('Post with id %d not found, returning 404!', post_id)
        return render_template('404.html'), 404
    else:
        app.logger.info('Article "%s" retrieved!', post['title'])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('"About Us" page retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
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
            app.logger.info('New article "%s" created!', title)

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
    connection = get_db_connection()
    if connection is None:
        postCount = 0
    else:
        postCountQuery = connection.execute("select count(*) from posts")
        postCountData = postCountQuery.fetchone()
        postCount = postCountData[0]
        connection.close()
        
    response = app.response_class(
            response=json.dumps({"db_connection_count":app.config['DB_CONN_COUNTER'],"post_count":postCount}),
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

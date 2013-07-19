#!flask/bin/python
from flask import Flask, render_template, session, redirect, url_for, escape, request
app = Flask(__name__)

import redis
import settings

settings.r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
from models import User,Post,Timeline

reserved_usernames = 'follow mentions home signup login logout post'

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

def authenticate(handler):
	def _check_auth(*args, **kwargs):
		if not session.new:
			user = User.find_by_id(session['id'])
			if user:
				return handler(user, *args, **kwargs)
		return redirect(url_for('login'))
	return _check_auth


def logged_in_user():
	if not session.new:
		return User.find_by_id(session['id'])
	return None


def user_is_logged():
	if logged_in_user():
		return True
	return False

@app.route('/')
def index():
	if user_is_logged():
		return redirect(url_for('home'))
	return render_template('home_not_logged.html', header='home', logged=False)


@app.route('/home')
@authenticate
def home(user):
	counts = user.followees_count, user.followers_count, user.tweet_count
	if len(user.posts()) > 0:
		last_tweet = user.posts()[0]
	else:
		last_tweet = None
	return render_template('timeline.html', header='page', timeline=user.timeline(), page='timeline.html', username=user.username, counts=counts, last_tweet=last_tweet, logged=True)


@app.route('/mentions')
@authenticate
def mentions(user):
	counts = user.followees_count, user.followers_count, user.tweet_count
	return render_template('mentions.html', header='page', mentions=user.mentions(), page='mentions.html', username=user.username, counts=counts, posts=user.posts()[:1],logged=True)


@app.route('/:name')
def user_page(name):
	is_following, is_logged = False, user_is_logged()
	user = User.find_by_username(name)
	if user:
		counts = user.followees_count, user.followers_count, user.tweet_count
		logged_user = logged_in_user()
		himself = logged_user.username == name
		if logged_user:
			is_following = logged_user.following(user)

		return render_template('user.html', header='page', posts=user.posts(), counts=counts, page='user.html', username=user.username, logged=is_logged, is_following=is_following, himself=himself)

	else:
		abort(404)


@app.route('/:name/statuses/:id')
def status(name, id):
	post = Post.find_by_id(id)
	if post:
		if post.user.username == name:
			return render_template('single.html', header='page', username=post.user.username, tweet=post, page='single.html', logged=user_is_logged())

	abort(404)


@app.route('/post', methods=['POST'])
@authenticate
def post(user):
	content = request.form['content']
	Post.create(user, content)
	return redirect(url_for('home'))


@app.route('/follow/:name', methods=['POST'])
@authenticate
def post(user, name):
	user_to_follow = User.find_by_username(name)
	if(user_to_follow):
		user.follow(user_to_follow)
	return redirect(url_for('%s' % name))


@app.route('/unfollow/:name', methods=['POST'])
@authenticate
def post(user, name):
	user_to_unfollow = User.find_by_username(name)
	if user_to_unfollow:
		user.stop_following(user_to_follow)
	return redirect(url_for('%s' % name))


@app.route('/signup')
@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
                if 'name' in request.form and 'password' in request.form:
                        name = request.form['name']
                        password = request.form['password']

                        user = User.find_by_username(name)
                        if user and user.password == settings.SALT + password:
                                session['id'] = user.id
                                return redirect(url_for('home'))

                return render_template('login.html', header='page', page='login.html', error_login=True, error_signup=False, logged=False)
	else:
		if user_is_logged():
			return redirect(url_for('home'))
		return render_template('login.html', header='page', page='login.html', error_login=False, error_signup=False, logged=False)




@app.route('/logout')
def logout():
	session.pop('id', None)
	return redirect('/')


@app.route('/signup', methods=['POST'])
def sign_up():
	if 'name' in request.form and 'password' in request.form:
		name = request.form['name']
		if name not in reserved_usernames.split():
			password = request.form['password']
			user = User.create(name, password)
			if user:
				session['id'] = user.id
				return redirect(url_for('home'))
			return render_template('login.html', header='page', page='login.html', error_login=False, error_signup=True, logged=False)


@app.route('/static/:filename')
def static_file(filename):
	app.send_static_file(filename)
	# return redirect(url_for('static', filename=filename)


if __name__ == '__main__':
	app.run(debug=True)

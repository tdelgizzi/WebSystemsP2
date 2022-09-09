"""
Insta485 user page view.

URLs include:
/u/<user_url_slug>/
"""
import flask
from flask import request
import insta485


@insta485.app.route('/u/<user_url_slug>/')
def show_user(user_url_slug):
    """Display /u/<user_url_slug>/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    connection = insta485.model.get_db()
    # if user is not in db, abort(404)
    username = user_url_slug
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM users "
        "WHERE username = ?", (username,)
    )
    if not cur.fetchall()[0]['COUNT(*)']:
        flask.abort(404)
    logname = flask.session['user']
    # Connect to database
    cur = connection.execute(
        "SELECT fullname "
        "FROM users "
        "WHERE username = ?", (username,)
    )
    fullname = cur.fetchall()[0]['fullname']
    # check if user follows this account
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username1 = ? AND username2 = ?", (logname, username)
    )
    logname_follows_username = cur.fetchall()[0]['COUNT(*)']
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username2 = ?", (username,)
    )
    followers = cur.fetchall()[0]['COUNT(*)']
    # Get number of followers
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username2 = ?", (username,)
    )
    followers = cur.fetchall()[0]['COUNT(*)']
    # Get number of following
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username1 = ?", (username,)
    )
    following = cur.fetchall()[0]['COUNT(*)']
    # Get posts data
    cur = connection.execute(
        "SELECT postid, filename as img_url "
        "FROM posts "
        "WHERE owner = ?", (username,)
    )
    posts = cur.fetchall()
    # Calculate Number of Posts from Post data
    total_posts = len(posts)
    # Add database info to context
    ctxt = {"username": username,
            "logname_follows_username": logname_follows_username,
            "fullname": fullname,
            "logname": logname,
            "followers": followers,
            "following": following,
            "posts": posts,
            "total_posts": total_posts}
    return flask.render_template("user.html", **ctxt)


def logname_follows(username, follows):
    """Return 1 if username is followed in follows dict, 0 o.w."""
    for follow in follows:
        if follow['username'] == username:
            return 1
    return 0


@insta485.app.route('/u/<user_url_slug>/following/')
def show_following(user_url_slug):
    """Display /<user_url_slug>/following/ route."""
    # Connect to database
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    connection = insta485.model.get_db()
    # if user is not in db, abort(404)
    username = user_url_slug
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM users "
        "WHERE username = ?", (username,)
    )
    if not cur.fetchall()[0]['COUNT(*)']:
        flask.abort(404)
    logname = flask.session['user']
    # Get list of following, with username and pictures
    cur = connection.execute(
            "SELECT username, filename as user_img_url FROM following "
            "JOIN users "
            "ON following.username2 = users.username "
            "WHERE following.username1 = ? ", (username,)
        )
    users = cur.fetchall()
    # get list of users logname follows
    cur = connection.execute(
            "SELECT DISTINCT username2 as username FROM following "
            "WHERE username1 = ? ", (logname,)
        )
    follows = cur.fetchall()
    # check if logname follows all users
    for user in users:
        log_follows = logname_follows(user['username'], follows)
        user['logname_follows_username'] = log_follows
    # Add database info to context
    context = {"following": users, "logname": logname, "username": username}
    return flask.render_template("following.html", **context)


@insta485.app.route('/u/<user_url_slug>/followers/')
def show_followers(user_url_slug):
    """Display /<user_url_slug>/followers/ route."""
    # Connect to database
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    connection = insta485.model.get_db()
    # if user is not in db, abort(404)
    username = user_url_slug
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM users "
        "WHERE username = ?", (username,)
    )
    if not cur.fetchall()[0]['COUNT(*)']:
        flask.abort(404)
    logname = flask.session['user']
    # Get list of followers, with username and pictures
    cur = connection.execute(
            "SELECT username, filename as user_img_url FROM following "
            "JOIN users "
            "ON following.username1 = users.username "
            "WHERE following.username2 = ? ", (username,)
        )
    users = cur.fetchall()
    # get list of users logname follows
    cur = connection.execute(
            "SELECT DISTINCT username2 as username FROM following "
            "WHERE username1 = ? ", (logname,)
        )
    follows = cur.fetchall()
    # check if logname follows all users
    for user in users:
        log_follows = logname_follows(user['username'], follows)
        user['logname_follows_username'] = log_follows
    # Add database info to context
    context = {"followers": users, "logname": logname, "username": username}
    return flask.render_template("followers.html", **context)


@insta485.app.route('/following/', methods=['POST'])
def post_following():
    """Fulfill post request with /following/ extennsion."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    url = request.args.get('target')
    if not url:
        url = flask.url_for('show_index')
    logname = flask.session['user']
    connection = insta485.model.get_db()
    operation = request.form.get("operation")
    username = request.form.get("username")
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username1 = ? AND username2 = ?", (logname, username)
    )
    already_follows = cur.fetchall()[0]['COUNT(*)']
    if operation == "follow":
        # ensure they do not follow this user
        if already_follows:
            flask.abort(409)
        # add follow
        cur = connection.execute(
            "INSERT INTO following(username1, username2) "
            "VALUES(?, ?)", (logname, username)
        )
    elif operation == "unfollow":
        # ensure they follow this user
        if not already_follows:
            flask.abort(409)
        # remove follow
        cur = connection.execute(
            "DELETE FROM following "
            "WHERE username1 = ? AND username2 = ?", (logname, username)
        )
    return flask.redirect(url)

"""
Insta485 user page view.

URLs include:
TODO
"""
import pathlib
import uuid
import hashlib
import os
from flask import request
import flask
import insta485


def get_user_password(username):
    """Retrieve username's password from db."""
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT password FROM users "
        "WHERE username = ? ", (username,)
    )
    query = cur.fetchall()
    if not query:
        flask.abort(403)
    return query[0]['password']


def delete_file(old_file):
    """Delete file from upload folder."""
    # make sure user is logged in
    if "user" not in flask.session:
        flask.abort(403)
    os.remove(os.path.join(insta485.app.config['UPLOAD_FOLDER'], old_file))


def compute_encrypted_password(password, salt=uuid.uuid4().hex):
    """Compute a string literal's encryped password."""
    # compute login password value
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


@insta485.app.route('/accounts/login/')
def show_login():
    """Display /accounts/login/ route."""
    # If logged-in, redirect to /
    if "user" in flask.session:
        return flask.redirect(flask.url_for("show_index"))
    return flask.render_template("login.html")


@insta485.app.route('/accounts/create/')
def show_create():
    """Display /accounts/create/ route."""
    # If logged-in, redirect to /accounts/edit
    if "user" in flask.session:
        return flask.redirect(flask.url_for("show_edit"))
    return flask.render_template("create.html")


@insta485.app.route('/accounts/logout/', methods=['POST'])
def show_logout():
    """Display /accounts/logout/ route."""
    # remove session
    flask.session.pop('user', None)
    # redirect
    return flask.redirect(flask.url_for("show_login"))


@insta485.app.route('/accounts/password/')
def show_password():
    """Display /accounts/passowrd/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    context = {'logname': flask.session['user']}
    return flask.render_template("password.html", **context)


@insta485.app.route('/accounts/delete/')
def show_delete():
    """Display /accounts/delete/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    context = {'logname': flask.session['user']}
    return flask.render_template("delete.html", **context)


@insta485.app.route('/accounts/edit/')
def show_edit():
    """Display /accounts/edit/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    username = flask.session['user']
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT username, email, fullname, filename FROM users "
        "WHERE username = ? ", (username,)
    )
    query_result = cur.fetchall()[0]
    email = query_result['email']
    fullname = query_result['fullname']
    image = query_result['filename']
    ctxt = {'logname': username, 'email': email,
            'fullname': fullname, 'user_image': image}
    return flask.render_template("edit.html", **ctxt)


def login_user(username, password):
    """Login user, add session cookie."""
    # compute password, compare it to database value for username
    # read in password from db
    db_password = get_user_password(username)
    # extract the salt
    salt = db_password.split('$')[1]
    password_db_string = compute_encrypted_password(password, salt)
    if password_db_string != db_password:
        flask.abort(403)
    # if successful, start session
    # create session for this user
    flask.session["user"] = username


def create_user(fullname, username, email, password, uuid_basename):
    """Create user."""
    if not fullname or not username or not email or not password:
        flask.abort(400)
    # check that username isn't already used
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT COUNT(*) FROM users "
        "WHERE username = ?", (username,)
    )
    if cur.fetchall()[0]['COUNT(*)'] != 0:
        flask.abort(409)
    password_db_string = compute_encrypted_password(password)
    # add to db
    # Query database
    cur = connection.execute(
        "INSERT INTO users(username, fullname, email, filename, password) "
        "VALUES (?, ?, ?, ?, ?) ",
        (username, fullname, email, uuid_basename, password_db_string)
    )
    # create session for this user
    flask.session["user"] = username


def delete_user(username):
    """Delete user from server."""
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT filename FROM users "
        "WHERE username = ? ", (username,)
    )
    icon = cur.fetchall()[0]['filename']
    # delete icon
    delete_file(icon)
    # get list of post filenames
    cur = connection.execute(
        "SELECT filename FROM posts "
        "WHERE owner = ? ", (username,)
    )
    posts = cur.fetchall()
    for photo in posts:
        delete_file(photo['filename'])
    # delete from table
    cur = connection.execute(
        "DELETE FROM users "
        "WHERE username = ?", (username,)
    )
    flask.session.pop('user', None)


def edit_account(username, fullname, email):
    """Edit user account information."""
    if not fullname or not email:
        flask.abort(400)
    fileobj = flask.request.files["file"]
    connection = insta485.model.get_db()
    if fileobj:
        # get name of old file
        cur = connection.execute(
            "SELECT filename FROM users "
            "WHERE username = ? ", (username,)
        )
        old_file = cur.fetchall()[0]['filename']
        # delete old picture from filesystem
        delete_file(old_file)
        filename = fileobj.filename
        uuid_basename = "{stem}{suffix}".format(
            stem=uuid.uuid4().hex,
            suffix=pathlib.Path(filename).suffix
        )
        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)
        # update table
        connection.execute(
            "UPDATE users "
            "SET filename = ? "
            "WHERE username = ? ", (uuid_basename, username)
        )
    # edit rest
    connection.execute(
        "UPDATE users "
        "SET fullname = ? , email = ? "
        "WHERE username = ? ", (fullname, email, username)
    )


def update_password(username, password, new_password1, new_password2):
    """Update user password."""
    if not password or not new_password1 or not new_password2:
        flask.abort(400)
    db_password = get_user_password(username)
    salt = db_password.split('$')[1]
    password_db_string = compute_encrypted_password(password, salt)
    # authenticate password:
    if password_db_string != db_password:
        flask.abort(403)
    if new_password1 != new_password2:
        flask.abort(401)
    # calculate new password, update value
    updated_password = compute_encrypted_password(new_password1)
    connection = insta485.model.get_db()
    connection.execute(
        "UPDATE users "
        "SET password = ? "
        "WHERE username = ? ", (updated_password, username)
    )


@insta485.app.route('/accounts/', methods=["POST"])
def show_accounts():
    """Display /accounts/ route."""
    url = request.args.get('target')
    operation = request.form.get("operation")
    if not url:
        url = flask.url_for('show_index')
    if operation == "create":
        # Unpack flask object
        fileobj = flask.request.files["file"]
        if not fileobj:
            flask.abort(400)
        filename = fileobj.filename
        uuid_basename = "{stem}{suffix}".format(
            stem=uuid.uuid4().hex,
            suffix=pathlib.Path(filename).suffix
        )
        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)
        fullname = request.form.get("fullname")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        create_user(fullname, username, email, password, uuid_basename)
        # send them to index
    elif operation == "login":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flask.abort(400)
        login_user(username, password)
    elif operation == "delete":
        # delete all user photos, including icon
        if "user" not in flask.session:
            flask.abort(403)
        username = flask.session['user']
        delete_user(username)
    elif operation == "edit_account":
        if "user" not in flask.session:
            flask.abort(403)
        username = flask.session['user']
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        edit_account(username, fullname, email)
    elif operation == "update_password":
        if "user" not in flask.session:
            flask.abort(403)
        # take in post data
        username = flask.session['user']
        password = request.form.get("password")
        new_password1 = request.form.get("new_password1")
        new_password2 = request.form.get("new_password2")
        update_password(username, password, new_password1, new_password2)
    return flask.redirect(url)

"""
Insta485 user page view.

URLs include:
/u/<user_url_slug>/
"""
import pathlib
import uuid
import flask
import arrow
from flask import request
import insta485
from insta485.views.accounts import delete_file


@insta485.app.route('/p/<postid_url_slug>/')
def show_post(postid_url_slug):
    """Display /p/<postid_url_slug>/ route."""
    # Connect to database
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    logname = flask.session['user']
    connection = insta485.model.get_db()
    postid = postid_url_slug
    # Query database
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE postid = ?", (postid,)
    )
    post_info = cur.fetchall()
    if not post_info:
        flask.abort(404)
    post_info = post_info[0]
    owner = post_info['owner']
    # Get owner image url
    cur = connection.execute(
        "SELECT filename "
        "FROM users "
        "WHERE username = ?", (owner,)
    )
    owner_img_url = cur.fetchall()[0]['filename']
    timestamp = arrow.get(post_info['created']).humanize()
    # Comments
    cur = connection.execute(
        "SELECT owner, text, commentid "
        "FROM comments where postid == ? "
        " order by commentid asc", (postid,)
    )  # query to obtain comments
    comments = cur.fetchall()
    cur = connection.execute(
        "SELECT owner "
        "FROM likes where postid = ?", (postid,)
    )  # query to obtain number of likes
    query = cur.fetchall()
    # likes = query['owner']
    likes = len(query)
    user_like = 0
    for like in query:
        if like['owner'] == logname:
            user_like = 1

    # Add database info to context
    ctxt = {"owner": post_info['owner'],
            "owner_img_url": owner_img_url,
            "postid": postid,
            "logname": logname,
            "img_url": post_info['filename'],
            "timestamp": timestamp,
            "user_like": user_like,
            "likes": likes,
            "comments": comments}
    return flask.render_template("post.html", **ctxt)


@insta485.app.route('/posts/', methods=['POST'])
def show_posts():
    """Post /posts/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    logname = flask.session['user']
    url = request.args.get('target')
    if not url:
        url = flask.url_for('show_user', user_url_slug=logname)
    operation = request.form.get("operation")
    connection = insta485.model.get_db()

    if operation == "create":
        # if the user tries to create a post with an empty
        # file, then abort(400)
        fileobj = flask.request.files["file"]
        if not fileobj:
            flask.abort(400)
        # save image file to disk and redirect to url
        file = fileobj.filename
        uuid_basename = "{stem}{suffix}".format(
            stem=uuid.uuid4().hex,
            suffix=pathlib.Path(file).suffix
        )
        # Save to disk
        pth = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(pth)
        cur = connection.execute(
            "INSERT INTO posts(filename, owner) "
            "VALUES (?, ?) ", (uuid_basename, logname)
        )
    elif operation == "delete":
        # check to ensure user owns post
        postid = request.form.get("postid")
        cur = connection.execute(
            "SELECT owner, filename "
            "FROM posts "
            "WHERE postid = ?", (postid,)
        )
        query = cur.fetchall()[0]
        if query['owner'] != logname:
            flask.abort(403)
        # delete the image file for postid from the filesystem
        old_file = query['filename']
        delete_file(old_file)
        # delete everything related to post (comments, likes, post row)
        cur = connection.execute(
            "DELETE FROM comments "
            "WHERE postid = ?", (postid,)
        )  # deleting post comments
        cur = connection.execute(
            "DELETE FROM likes "
            "WHERE postid = ?", (postid,)
        )  # deleting likes from post
        cur = connection.execute(
            "DELETE FROM posts "
            "WHERE postid = ?", (postid,)
        )  # deleting post from post table

    # Redirect to URL
    return flask.redirect(url)

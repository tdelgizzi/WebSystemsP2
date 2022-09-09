"""
Insta485 user page view.

URLs include:
/comments/
"""
from flask import request
import flask
import insta485


@insta485.app.route('/comments/', methods=['POST'])
def show_comments():
    """Display /comments/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    user = flask.session['user']
    url = request.args.get('target')
    if not url:
        url = flask.url_for('show_index')
    operation = request.form.get("operation")
    postid = request.form.get("postid")
    connection = insta485.model.get_db()
    # check operation and perform necessary commands
    if operation == "create":
        # run query to add comment to db
        text = request.form.get("text")
        if not text:
            flask.abort(400)
        cur = connection.execute(
            "INSERT INTO comments(owner, postid, text) "
            "VALUES (?, ?, ?) ", (user, postid, text)
        )
    elif operation == "delete":
        # check owner of commend, confirm it is the user
        commentid = request.form.get("commentid")
        cur = connection.execute(
            "SELECT owner "
            "FROM comments "
            "where commentid = ?", (commentid,)
        )
        if cur.fetchall()[0]['owner'] != user:
            flask.abort(403)
        # run query to delete comment from db
        cur = connection.execute(
            "DELETE FROM comments WHERE "
            " commentid = ?", (commentid,)
        )
    return flask.redirect(url)

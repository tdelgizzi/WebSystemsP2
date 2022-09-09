"""
Insta485 user likes view.

URLs include:
/likes/
"""
import flask
from flask import request
import insta485


@insta485.app.route('/likes/', methods=["POST"])
def show_likes():
    """Display /likes/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    owner = flask.session['user']
    link = request.args.get('target')
    if not link:
        link = flask.url_for('show_index')
    operation = request.form.get("operation")
    postid = request.form.get("postid")
    cxn = insta485.model.get_db()
    if operation == "like":
        # make sure they haven't liked the post flask.abort(409)
        # Query database
        cur = cxn.execute(
            "SELECT COUNT(*) "
            "FROM likes "
            "WHERE postid = ? AND owner = ?", (postid, owner)
        )
        if cur.fetchall()[0]['COUNT(*)']:
            flask.abort(409)
        # create a like for postid
        cur = cxn.execute(
            "INSERT INTO likes(owner, postid) "
            "VALUES (?, ?) ", (owner, postid)
        )
    elif operation == "unlike":
        # make sure they've already liked flask.abort(409)
        # Query database
        cur = cxn.execute(
            "SELECT COUNT(*) "
            "FROM likes "
            "WHERE postid = ? AND owner = ?", (postid, owner)
        )
        if cur.fetchall()[0]['COUNT(*)'] == 0:
            flask.abort(409)
        # delete a like for postid
        cur = cxn.execute(
            "DELETE FROM likes "
            "WHERE owner = ? AND postid = ?", (owner, postid)
        )
    return flask.redirect(link)

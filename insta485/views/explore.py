"""
Insta485 user page view.

URLs include:
/u/<user_url_slug>/
"""
import flask
import insta485


@insta485.app.route('/explore/')
def show_explore():
    """Display /explore/ route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    username = flask.session['user']
    connection = insta485.model.get_db()
    # Query database
    cur = connection.execute(
        "SELECT a.username, u2.filename as user_img_url "
        "FROM (SELECT DISTINCT username "
        "FROM users "
        "WHERE username <> ? "
        "EXCEPT "
        "SELECT DISTINCT username2 as username "
        "FROM users u2 "
        "JOIN following "
        "ON u2.username = following.username1 "
        "WHERE u2.username = ?) a "
        "JOIN users u2 "
        "ON a.username = u2.username ", (username, username)
    )
    users = cur.fetchall()
    # Add database info to context
    context = {"logname": username, "not_following": users}
    return flask.render_template("explore.html", **context)

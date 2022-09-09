"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import arrow
import insta485


@insta485.app.route('/')
def show_index():
    """Display / route."""
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    logname = flask.session["user"]
    # Connect to database
    connection = insta485.model.get_db()
    # Query database
    cur = connection.execute(
        "SELECT a.postid, a.filename, a.owner, "
        "a.created, u.filename as owner_pic "
        "FROM (SELECT DISTINCT postid, filename, owner, created "
        "FROM (SELECT username2 "
        "FROM following "
        "WHERE username1 = ?) "
        "JOIN posts "
        "ON owner = username2 or owner = ?"
        "ORDER BY postid DESC) a "
        "INNER JOIN users u "
        "ON u.username = a.owner", (logname, logname)
    )
    post_query = cur.fetchall()
    pts = []
    for post in post_query:
        postid = post['postid']
        owner = post['owner']
        timestamp = arrow.get(post['created']).humanize()
        cur = connection.execute(
            "SELECT owner "
            "FROM likes where postid == ?", (postid,)
        )  # query to obtain number of likes
        que = cur.fetchall()
        # likes = query['owner']
        likes = len(que)
        user_like = 0
        for like in que:
            if like['owner'] == logname:
                user_like = 1
        cur = connection.execute(
            "SELECT owner, text "
            "FROM comments where postid == ? "
            " order by commentid asc", (postid,)
        )  # query to obtain comments
        comments = cur.fetchall()
        pts.append({"postid": postid, "owner": owner,
                    "owner_img_url": post['owner_pic'],
                    "img_url": post['filename'],
                    "timestamp": timestamp, "likes": likes,
                    "comments": comments, "user_like": user_like})
    # Add database info to context
    ctxt = {"logname": logname,
            "posts": pts}
    return flask.render_template("index.html", **ctxt)

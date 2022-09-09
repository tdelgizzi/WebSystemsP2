"""
Insta485 user page view.

URLs include:
/uploads/<filename>/
"""
import flask
import insta485


@insta485.app.route('/uploads/<filename>')
def show_uploads(filename):
    """Display /uploads/<filename> route."""
    if "user" not in flask.session:
        flask.abort(403)
    up_file = flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"],
                                        filename=filename)
    if not up_file:
        flask.abort(404)
    return up_file

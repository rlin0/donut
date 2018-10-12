import flask
import json
import os
from werkzeug import secure_filename
from donut.modules.uploads import blueprint, helpers
from donut.resources import Permissions
from donut.auth_utils import check_permission


@blueprint.route('/lib/<path:url>')
def display(url):
    '''
    Displays the webpages that have been created by users.
    '''
    page = helpers.read_page(url.replace(' ', '_'))
    return flask.render_template(
        'page.html',
        page=page,
        title=url.replace('_', ' '),
        permission=check_permission(Permissions.ADMIN))


@blueprint.route('/_send_page', methods=['GET'])
def get_page():
    '''
    Sends the page to frontend.
    '''
    url = flask.request.args.get('url')
    page = helpers.read_page(url.replace(' ', '_'))
    return flask.jsonify(result=page)


@blueprint.route('/uploads')
def uploads():
    '''
    Serves the webpage that allows a user to upload a file.
    '''
    if check_permission(Permissions.ADMIN) and 'username' in flask.session:
        return flask.render_template('uploads.html')
    else:
        flask.abort(403)


@blueprint.route('/_upload_file', methods=['POST'])
def upload_file():
    '''
    Handles the uploading of the file
    '''
    if 'file' not in flask.request.files:
        return flask.abort(500)
    file = flask.request.files['file']
    filename = secure_filename(file.filename)
    uploads = os.path.join(flask.current_app.root_path,
                           flask.current_app.config['UPLOAD_FOLDER'])
    file.save(os.path.join(uploads, filename))
    if 'username' in flask.session and check_permission(Permissions.ADMIN):
        return flask.jsonify({
            'url':
            flask.url_for('uploads.uploaded_file', filename=filename)
        })
    else:
        return flask.abort(403)


@blueprint.route('/_check_valid_file', methods=['POST'])
def check_file():
    '''
    Checks if the file: exists, has a valid extension, and
    smaller than 10 mb
    '''
    if 'file' not in flask.request.files:
        return flask.jsonify({'error': 'No file selected'})
    if 'username' in flask.session and check_permission(Permissions.ADMIN):
        return flask.jsonify({'error': helpers.check_valid_file(file)})
    else:
        return flask.abort(403)


@blueprint.route('/uploaded_file/<filename>', methods=['GET'])
def uploaded_file(filename):
    '''
    Serves the actual uploaded file.
    '''
    uploads = os.path.join(flask.current_app.root_path,
                           flask.current_app.config['UPLOAD_FOLDER'])
    return flask.send_from_directory(uploads, filename, as_attachment=False)


@blueprint.route('/uploaded_list')
def uploaded_list():
    '''
    Shows the list of uploaded files
    '''

    filename = flask.request.args.get('filename')
    if filename != None:
        helpers.remove_link(filename)

    links = helpers.get_links()
    return flask.render_template('uploaded_list.html', links=links)

import flask
from donut.modules.arcfeedback import blueprint
from donut.modules.arcfeedback import helpers


@blueprint.route('/arcfeedback')
def arcfeedback():
    return flask.render_template('arcfeedback.html')


@blueprint.route('/arcfeedback/submit', methods=['POST'])
def arcfeedback_submit():
    fields = ['name', 'email', 'course', 'msg']
    required = ['course', 'msg']
    data = {}
    for field in fields:
        data[field] = flask.request.form.get(field)
    for field in required:
        if (data[field] == ""):
            flask.flash('Please fill in all required fields (marked with *)', 'error')
            return flask.redirect(flask.url_for('arcfeedback.arcfeedback'))
    complaint_id = helpers.register_complaint(data)
    if data['email'] != "":
        helpers.send_confirmation_email(data['email'], complaint_id)
    flask.flash('Success')
    return flask.redirect(flask.url_for('arcfeedback.arcfeedback'))


@blueprint.route('/arcfeedback/view/<uuid:id>')
def arcfeedback_view_complaint(id):
    if not (helpers.get_id(id)):
        return flask.render_template("404.html")
    return flask.render_template('complaint.html', uuid=id)

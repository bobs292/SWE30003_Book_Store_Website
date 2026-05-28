from flask import Blueprint, render_template

catalogue = Blueprint('catalogue', __name__)

@catalogue.route('/catalogue')
def catalogue():
    return render_template('catalogue.html')

from flask_login.utils import login_required
from app.main import bp
from flask import render_template
from app.models import Admin
from flask_login import current_user
from app.decorators import login_required


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@bp.route('/admin', methods=['GET', 'POST'])
@bp.route('/admin/index', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_home():
    return render_template('admin_home.html', title='Home')


@bp.route('/home', methods=['GET', 'POST'])
@login_required(role='customer')
def customer_home():
    return render_template('customer_home.html', title='Home')

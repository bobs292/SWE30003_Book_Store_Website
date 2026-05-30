from flask import Blueprint, render_template, session, redirect, url_for, request, flash

def create_auth_routes(auth_service):
    auth = Blueprint('auth', __name__)

    @auth.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            try:
                auth_service.register(
                    first_name=request.form.get('first_name'),
                    last_name=request.form.get('last_name'),
                    email=request.form.get('email'),
                    password=request.form.get('password'),
                    phone_number=request.form.get('phone_number') or None
                )
                flash('Registration successful. Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except ValueError as e:
                flash(str(e), 'error')
        return render_template('register.html')

    @auth.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            try:
                user = auth_service.login(
                    email=request.form.get('email'),
                    password=request.form.get('password')
                )
                session['customer_id'] = user['customer_id']
                flash('Login successful.', 'success')
                return redirect(url_for('homepage'))
            except ValueError as e:
                flash(str(e), 'error')
        return render_template('login.html')

    @auth.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('homepage'))

    return auth

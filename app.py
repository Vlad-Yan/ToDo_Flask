from flask import Flask, render_template, url_for, flash, request, redirect
from flask_login.utils import logout_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, login_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'fdgdfgdfggf786hfg6hfg6h7f'
db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    
    def __repr__(self):
        return '<Task %r' % self.id


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    psw = db.Column(db.String(500), nullable=False)

    
    def __repr__(self):
        return '<Users %r' % self.id


#db.create_all()


@app.route('/task')
@login_required
def index():
    user_id = current_user.id
    task = Task.query.filter_by(user_id=user_id).all()
    #task = Task.query.order_by(Task.done).all()
    return render_template("index.html", task=task)


@app.route('/create_task', methods=['POST', 'GET'])
@login_required
def create_task():
    if request.method == "POST":
        title = request.form['title']
        text = request.form['text']
        user_id = current_user.id
        task = Task(title=title, text=text, user_id=user_id)
        try:
            if len(title) > 0 and len(text) > 0:
                db.session.add(task)
                db.session.commit()
                return redirect('/task')
            else:
                flash('Заполните все поля!')
                return redirect('/create_task')
        except:
            return "При добавлении статьи произошла ошибка"
    else:
        return render_template("create_task.html")


@app.route('/change_task/<int:id>', methods=['POST', 'GET'])
@login_required
def change_task(id):
    user_id = current_user.id
    task = Task.query.get(id)
    if task.user_id == user_id:
        if request.method == "POST":
            task.title = request.form['title']
            task.text = request.form['text']
            try:
                if len(task.title) > 0 and len(task.text) > 0:
                    db.session.commit()
                return redirect('/task')
            except:
                return "При редактировании статьи произошла ошибка"
        else:
            return render_template("change_task.html", task=task)
    else:
        return render_template("page404.html")


@app.route('/task/<int:id>/done')
@login_required
def done_task(id):
    task = Task.query.get(id)
    user_id = current_user.id
    if task.user_id == user_id:
        task.done = True
        db.session.commit()
        return redirect('/task')
    else:
        return render_template("page404.html")


@app.route('/task/<int:id>/no_done')
@login_required
def no_done_task(id):
    task = Task.query.get(id)
    user_id = current_user.id
    if task.user_id == user_id:
        task.done = False
        db.session.commit()
        return redirect('/task')
    else:
        return render_template("page404.html")


@app.route('/task/<int:id>/delete')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    # get_or_404 - если запись не найдена, то будет ошибка 404
    user_id = current_user.id
    if task.user_id == user_id:
        try:
            db.session.delete(task)
            db.session.commit()
            return redirect('/task')
        except:
            return "При удалении статьи произошла ошибка"
    else:
        return render_template("page404.html")


# Ошибка 404 - несуществующий адрес страницы
@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html'), 404

# Если пользователь хочет попасть на чужую страницу
@app.errorhandler(401)
def userNotLogin(error):
    return render_template('page401.html'), 401


@app.route("/login", methods=["POST", "GET"])
@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        name = request.form['name']
        psw = request.form['psw']
        if name and psw:
            user = Users.query.filter_by(name=name).first()
            if user:
                if check_password_hash(user.psw, psw):
                    login_user(user)
                    return redirect('/task')
                    # return render_template("/task")
                else:
                    flash("Неверный пароль", "error")
            else:
                flash("Такого пользователя не существует", "error")
        else:
            flash("Пожалуйста введите все данные", "error")

        return render_template("login.html")
    else:
        return render_template("login.html")


@app.route('/logout', methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        try:
            if len(request.form['name']) > 2 and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
                hash = generate_password_hash(request.form['psw'])
                name = request.form['name']
                user = Users(name=name, psw=hash)
                db.session.add(user)
                db.session.commit()
                if db.session:
                    flash("Вы успешно зарегистрированы", "success")
                    return redirect(url_for('login'))
                else:
                    flash("Ошибка при добавлении в БД", "error")
            else:
                flash("Неверно заполнены поля", "error")
        except:
            flash("Пользователь уже существует", "error")
            return render_template("register.html")
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for,abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, logout_user, login_user, login_required
import uuid 
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import or_

login_manager = LoginManager()
# create the extension
db = SQLAlchemy()
# create tusershe app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_astropoint.db"
app.secret_key = 'dsgrytkddvcwykjhwwefdifu'
# initialize the app with the extension
db.init_app(app)
login_manager.init_app(app)

UPLOAD_FOLDER = './static/assets/articles/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg',  'JPG'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Article(db.Model):
    __tablename__ = 'article'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    writter_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.String)
    image = db.Column(db.String)

class Comment(db.Model):
     __tablename__ = 'comment'

     id = db.Column(db.String, primary_key=True)
     article_id = db.Column(db.String, db.ForeignKey("article.id"), nullable=False)
     commenter_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
     date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
     message = db.Column(db.String)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_writter =  db.Column(db.Boolean, default=False)
    articles = db.relationship("Article", backref="user", lazy=True)
    comments = db.relationship("Comment", backref="user", lazy=True)
    authenticated = db.Column(db.Boolean, default=False)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

with app.app_context():
    db.create_all()

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(password=password, email=email).first()
        if user:
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user=user, remember=True)

            return redirect(url_for('home'))
        else:
            return render_template("auth/login.html", error_message='Erro no login! tente de novo por favor ')
    
    return render_template("auth/login.html", error_message='')

@app.route("/logout")
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))


@app.route('/', methods=['GET'])
def home():
    user = None

    if current_user.is_authenticated:
        user = current_user

    articles = Article.query.order_by(Article.publish_date.desc()).all()

    return render_template("index.html",user=user, articles=articles)

@app.route('/pesquisar', methods=['GET'])
def pesquisar():
    user = None

    if current_user.is_authenticated:
        user = current_user

    args = request.args

    results = Article.query.filter(or_(Article.title.contains(args["s"]),Article.content.contains(args["s"]))).all()

    return render_template("search.html", user=user, results=results)

@app.route('/perfil/<id>', methods=['GET'])
@login_required
def perfil(id):
    user = current_user

    articles = Article.query.filter_by(writter_id=user.id).all()

    return render_template("perfil.html", user=user, articles=articles)

@app.route('/article/<id>', methods=['GET', 'POST'])
def article(id):
    user = None

    if current_user.is_authenticated:
        user = current_user

    if request.method == 'POST':
        comment = Comment(
            id = str(uuid.uuid1()),
            article_id= id,
            commenter_id = user.id,
            message = request.form['message']
        )
        db.session.add(comment)
        db.session.commit()


    article = Article.query.filter_by(id=id).first()
    results = User.query.filter_by().all()
    
    return render_template("article.html", user=user, article=article, results=results, aritcle_id=id)


@app.route('/new_article', methods=['GET', 'POST'])
@login_required
def new_article():
    user = current_user

    message = ""
    filename = None

    if request.method == 'POST':
        # check if the post request has the file part
        
        if 'file' not in request.files:
            message = 'No file part'
            #return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            message = 'No selected file'
            #return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = app.config['UPLOAD_FOLDER'] +'/'+ filename
            file.save(file_path)
            message = "Artigo salvo"

            article = Article(
                id = str(uuid.uuid1()),
                title= request.form['title'],
                writter_id = user.id,
                content = request.form['content'],
                image = file_path     
            )
            db.session.add(article)
            db.session.commit()
        else:
            message = "Ficheiro nao permitido"
            
    return render_template("new_article.html", user=user, message=message)

@app.route('/360', methods=['GET'])
def page_360():
    user = None

    if current_user.is_authenticated:
        user = current_user

    return render_template("solar_system.html",user=user)

@app.route('/estatistica', methods=['GET'])
def estatistica():
    user = None

    if current_user.is_authenticated:
        user = current_user

    df = pd.read_csv("data/final_data.csv", delimiter=",")

    df['Distance'] = df['Distance'].str.replace(',','')
    #df['Mass'] = df['Mass'].str.replace(',','')
    df['Radius'] = df['Radius'].str.replace(',','')

    df['Mass'] = df['Mass'].astype(float)
    df['Radius'] = df['Radius'].astype(float)
    df['Distance'] = df['Distance'].astype(float)
    
    
    data = df.to_dict("records")

    df = df[df.Star_name!="Sun"]

    planetas_mais_distantes = df.sort_values(by=["Distance"], ascending=True).head(5)
    planetas_mais_distantes = planetas_mais_distantes.to_dict("records")

    planetas_mais_pesados = df.sort_values(by=["Mass"], ascending=False).head(5)
    planetas_mais_pesados = planetas_mais_pesados.to_dict("records")


    return render_template("estatistica.html", user=user, dados_da_tabela=data, planetas_mais_distantes=planetas_mais_distantes, planetas_mais_pesados=planetas_mais_pesados)


@app.route('/registar', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        writter = False

        if 'is_writter' in request.form:
            if request.form['is_writter']=="on":
                writter=True

        user = User(
            id = str(uuid.uuid1()),
            email= request.form['email'],
            name = request.form['name'],
            password = request.form['password'],
            is_writter = writter     
        )
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template("auth/register.html")


@app.errorhandler(404) 
def not_found(e): 
    user = None

    if current_user.is_authenticated:
        user = current_user

    return render_template("404.html", user=user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
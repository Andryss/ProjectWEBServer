import sqlite3
from flask import Flask, redirect, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField, TextAreaField
from wtforms.validators import DataRequired
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
 
class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn
 
    def get_connection(self):
        return self.conn
 
    def __del__(self):
        self.conn.close()
        
db = DB()

class UsersModel:
    def __init__(self, connection):
        self.connection = connection
        
    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128)
                             )''')
        cursor.close()
        self.connection.commit()
        
    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, password_hash) 
                          VALUES (?,?)''', (user_name, password_hash))
        cursor.close()
        self.connection.commit()    
        
    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?", (user_name, password_hash))
        row = cursor.fetchone()
        cursor.close()
        return (True, row[0]) if row else (False,)
    
    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        cursor.close()
        return row
    
    def get_name(self, name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ?", (str(name),))
        row = cursor.fetchone()
        cursor.close()
        return row
     
    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    def delete(self, name):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM users WHERE user_name = ?''', (str(name),))
        cursor.close()
        self.connection.commit()
    
session = {}
main_user = UsersModel(db.get_connection())
main_user.init_table()
    
class NewsModel:
    def __init__(self, connection):
        self.connection = connection
        
    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             stroka VARCHAR(50),
                             date VARCHAR(20),
                             user_id INTEGER,
                             content VARCHAR(1000000)
                             )''')
        cursor.close()
        self.connection.commit()
        
    def insert(self, title, stroka, data, user_id, content):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                          (title, stroka, date, user_id, content) 
                          VALUES (?,?,?,?,?)''', (title, str(stroka), data, str(user_id), str("\n".join(content)),))
        cursor.close()
        self.connection.commit()
        
    def exists(self, title):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE title = ?", (str(title),))
        row = cursor.fetchone()
        cursor.close()
        return (True, row[0]) if row else (False,)
        
    def get(self,news_id ):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id),))
        row = cursor.fetchone()
        cursor.close()
        return row
    
    def get_str(self, title):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE title = ?", (str(title),))
        row = cursor.fetchone()[5]
        return row       
     
    def get_all(self, user_id = None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ?",
                           (str(user_id)))
        else:
            cursor.execute("SELECT * FROM news")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    def get_all_delete(self, user_id):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ?", (str(user_id)))
            rows = cursor.fetchall()
            cursor.execute('''DELETE FROM news WHERE user_id = ?''', (str(user_id)))
        else:
            cursor.execute("SELECT * FROM news")
            rows = cursor.fetchall()
            cursor.execute('''DELETE FROM news''')         
        cursor.close()
        return rows
    
    def delete(self, title):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE title = ?''', (str(title),))
        cursor.close()
        self.connection.commit()
        
main_news = NewsModel(db.get_connection())
main_news.init_table()

if not main_user.exists("Andryss", "admin")[0]:
    main_user.insert("Andryss", "admin")
        
class AddNewsForm(FlaskForm):
    title = StringField('Заголовок книги', validators=[DataRequired()])
    file = FileField('Файл с текстом книги', validators=[DataRequired()])
    submit = SubmitField('Добавить')
    
class AddNewsTextForm(FlaskForm):
    title = StringField('Заголовок книги', validators=[DataRequired()])
    content = TextAreaField('Текст книги', validators=[DataRequired()])
    submit = SubmitField('Добавить')
    
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
    
class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегестрироваться')
    
@app.route('/sorting_data')
def sorting_data():
    news = NewsModel(db.get_connection()).get_all_delete(session['user_id'])
    news.sort(key = lambda x: (x[5], x[1], x[2], x[0], x[3], x[4]))
    news_table = NewsModel(db.get_connection())
    for new in news:
        news_table.insert(new[1], new[2], new[3], new[4], new[5])
    return redirect('/index')

@app.route('/logout')
def logout():
    session.pop('username',0)
    session.pop('user_id',0)
    return redirect('/login')

@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect('/login')
    if session['username'] == 'Читатель':
        return redirect('/index_user')
    if session['username'] == 'Andryss':
        return redirect('/index_admin')
    n = NewsModel(db.get_connection()).get_all(session['user_id'])
    return render_template('index.html', username=session['username'], news=n)
    
@app.route('/index_user')
def index_user():
    session['username'] = 'Читатель'
    session['user_id'] = None
    news_main = NewsModel(db.get_connection()).get_all()
    users_main = UsersModel(db.get_connection()).get_all()
    n = []
    for news in news_main:
        for users in users_main:
            if users[0] == news[4]:
                name = users[1]
        new = (news[0], news[1], news[2], news[3], name)
        n.append(new)
    return render_template('index_user.html', username=session['username'], news=n)

@app.route('/index_admin')
def index_admin():
    if 'username' not in session:
        return redirect('/login')
    n = NewsModel(db.get_connection()).get_all()
    u = UsersModel(db.get_connection()).get_all()
    n1 = []
    for new in n:
        for user in u:
            if user[0] == new[4]:
                name = user[1]
        news = (new[0], new[1], new[2], new[3], name, new[5])
        n1.append(news)
    return render_template('index_admin.html', username=session['username'], news=n1)

@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        nm = NewsModel(db.get_connection())
        if not nm.exists(title)[0]:
            ########
            with open(form.file.data, 'r') as file:
                content = file.read()
                list_con = content.split('\n')
                if len(list_con[0]) > 77:
                    stroka = list_con[0][:77] + '...'
                else:
                    stroka = list_con[0]
            ########
            data = str(datetime.now()).split()[0]
            nm.insert(title, stroka, data, session['user_id'], list_con)
            return redirect("/index")
    return render_template('add_news.html', title='Добавление книги',
                           form=form, username=session['username'])

@app.route('/add_news/text', methods=['GET', 'POST'])
def add_news_text():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsTextForm()
    if form.validate_on_submit():
        title = form.title.data
        nm = NewsModel(db.get_connection())
        if not nm.exists(title)[0]:
            ########
            content = form.content.data
            if len(content) > 77:
                stroka = content[:77] + '...'
            else:
                stroka = content
            ########
            data = str(datetime.now()).split()[0]
            nm.insert(title, stroka, data, session['user_id'], content.split('\n'))
            return redirect("/index")
    return render_template('add_news_text.html', title='Добавление книги',
                           form=form, username=session['username'])
 
@app.route('/delete_news/<title>', methods=['GET'])
def delete_news(title):
    if 'username' not in session:
        return redirect('/login')
    title = str(title)
    nm = NewsModel(db.get_connection())
    nm.delete(title)
    return redirect("/index")

@app.route('/delete_user/<username>', methods=['GET'])
def delete_user(username):
    if 'username' not in session:
        return redirect('/login')
    u = UsersModel(db.get_connection())
    user = u.get_name(username)
    n = NewsModel(db.get_connection())
    news = NewsModel(db.get_connection()).get_all(user[0])
    for new in news:
        n.delete(new[1])
    u.delete(user[1])
    return redirect('/index_admin')
    
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    user_name = form.username.data
    password = form.password.data
    user_model = UsersModel(db.get_connection())
    exists = user_model.exists(user_name, password)
    if form.validate_on_submit():
        if not exists[0]:
            user_model.insert(user_name, password)
            return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user_name = form.username.data
    password = form.password.data
    user_model = UsersModel(db.get_connection())
    exists = user_model.exists(user_name, password)  
    if form.validate_on_submit():
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
            return redirect('/index')
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/open_book_user/<title>', methods=['GET'])
def book_user(title):
    if 'username' not in session:
        return redirect('/login')
    book = NewsModel(db.get_connection()).get_str(str(title))
    book = [title, book.split('\n')]
    return render_template('book_user.html', title='НАЖМИ НА МЕНЯ!!!', book=book)

@app.route('/open_book/<title>', methods=['GET'])
def book(title):
    if 'username' not in session:
        return redirect('/login')
    book = NewsModel(db.get_connection()).get_str(str(title))
    book = [title, book.split('\n')]
    return render_template('book.html', title='НАЖМИ НА МЕНЯ!!!', book=book)

@app.route('/open_book_admin/<title>', methods=['GET'])
def book_admin(title):
    if 'username' not in session:
        return redirect('/login')
    book = NewsModel(db.get_connection()).get_str(str(title))
    book = [title, book.split('\n')]
    return render_template('book.html', title='НАЖМИ НА МЕНЯ!!!', book=book)

@app.route('/download_book/<title>')
def download(title):
    if 'username' not in session:
        return redirect('/login')
    news = NewsModel(db.get_connection())
    content = news.get_str(title)
    name = str(title) + '.txt'
    file = open(name, 'w')
    file.write(content)
    file.close()
    return redirect('/index_user')
    

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
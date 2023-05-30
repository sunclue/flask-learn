from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
import os
import click
from flask import request,url_for,redirect,flash
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required,logout_user
from flask_login import current_user

app=Flask(__name__)

#设置数据库连接地址
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(app.root_path,'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'

db=SQLAlchemy(app)      # 初始化扩展，导入程序实例
login_manager=LoginManager(app)

login_manager.login_view='login'

class User(db.Model,UserMixin):   #表名将为user，自动小写
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20))
    username=db.Column(db.String(20))
    password_hash=db.Column(db.String(128))
    
    def set_password(self,password):
        self.password_hash=generate_password_hash(password)

    def validate_password(self,password):
        return check_password_hash(self.password_hash,password)

class Movie(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(60))
    year=db.Column(db.String(4))

@login_manager.user_loader
def user_loader(user_id):   #创建用户加载回调函数，接受用户ID作为参数
    user=User.query.get(int(user_id))
    return user

@app.cli.command()
@click.option('--drop',is_flag=True,help='Create after Drop')
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database')

@app.cli.command()
def forge():
    db.create_all()
    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    u=User(name=name)
    db.session.add(u)
    for m in movies:
        movie=Movie(title=m['title'],year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done')

@app.cli.command()
@click.option('--username',prompt=True,help='The username used to login')
@click.option('--password',prompt=True,hide_input=True,confirmation_prompt=True,help='The password used to login')
def admin(username,password):
    db.create_all()

    user=User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.name=username
        user.password=password
    else:
        click.echo('Creating user...')
        user=User(username=username,name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')

@app.context_processor
def inject_user():
    user=User.query.first()
    return dict(user=user)

@app.route('/home')
def hello():
    return 'Welcome to My Watchlist'

@app.route('/',methods=['GET','POST'])
def index():
    if request.method=='POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        title=request.form.get('title') #获取form标签的name值
        year=request.form.get('year')
        if not title or not year or len(year)>4 or len(title)>60:
            flash('Invalid input.')
            return redirect(url_for('index'))
        movie=Movie(title=title,year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    movies=Movie.query.all()
    return render_template('index.html',movies=movies)

@app.route('/movie/edit/<int:movie_id>',methods=['GET','POST'])
@login_required
def edit(movie_id):
    movie=Movie.query.get_or_404(movie_id)
    if request.method=='POST':
        title=request.form['title']
        year=request.form['year']

        if not title or not year or len(year)>4 or len(title)>60:
            flash('Invalid input')
            return redirect(url_for('edit',movie_id=movie_id))
        
        movie.title=title
        movie.year=year
        db.session.commit()
        flash('Item updated')
        return redirect(url_for('index'))
    return render_template('edit.html',movie=movie)

@app.route('/movie/delete/<int:movie_id>',methods=['POST'])
@login_required
def delete(movie_id):
    movie=Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted')
    return render_template('index')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']

        if not username or not password:
            flash('Invalid input')
            return redirect(url_for('login'))
        
        user=User.query.first()
        if username==user.username and user.validate_password(password):
            login_user(user)
            flash('Login success')
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required #用于视图保护
def logout():
    logout_user()
    flash('Goodbye')
    return redirect(url_for('index'))

@app.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    if request.method=='POST':
        name=request.form['name']

        if not name or len(name)>20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        
        current_user.name=name  # current_user会返回当前登录用户的数据库记录对象
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    
    return render_template('settings.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404
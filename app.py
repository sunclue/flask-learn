from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
import os
import click

app=Flask(__name__)

#设置数据库连接地址
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(app.root_path,'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False  # 关闭对模型修改的监控

db=SQLAlchemy(app)      # 初始化扩展，导入程序实例

@app.cli.command()
@click.option('--drop',is_flag=True,help='Create after Drop')
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database')

class User(db.Model):   #表名将为user，自动小写
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20))

class Movie(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(60))
    year=db.Column(db.String(4))

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

@app.route('/home')
def hello():
    return 'Welcome to My Watchlist'

@app.route('/')
def index():
    user=User.query.first()
    movies=Movie.query.all()
    return render_template('index.html',user=user,movies=movies)


import os
from makeitminev2_5.make import Make


class FKMake(Make):
  """ Recipies for a Makefile supporting a Flask project.
  """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.fksrc = os.path.join("src",self.name(),"flaskapp")
    self.fkdb = os.path.join("test", "flask.sqlite")
    if not os.path.exists("test"):
      os.mkdir("test")
    if not os.path.exists(self.fksrc):
      os.mkdir(self.fksrc)

  def create_files(self):
    super().create_files()
    for fn in ["routes.py","models.py"]:
      p = os.path.join(self.fksrc,fn)
      if os.path.exists(p): continue
      print(f"INFO creating {p}")
      with open(p,"w") as f:
        f.write("")
    p = os.path.join(self.fksrc,"__init__.py")
    if not os.path.exists(p):
      print(f"INFO creating {p}")
      contents = f"""
import os
from flask import Flask
from . import db

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev',DATABASE='{self.fkdb}')
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    db.init_app(app)
    return app
"""
      with open(p,"w") as f: f.write(contents)
      self.pyinstall(package="flask")
    p = os.path.join(self.fksrc,"db.py")
    if not os.path.exists(p):
      print(f"INFO creating {p}")
      contents="""
import sqlite3
from datetime import datetime
import click
from flask import current_app, g
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
          current_app.config['DATABASE'],
          detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

"""
      with open(p,"w") as f: f.write(contents)
    p = os.path.join(self.fksrc,"schema.sql")
    if not os.path.exists(p):
      print(f"INFO creating {p}")
      contents="""
DROP TABLE IF EXISTS test;
DROP TABLE IF EXISTS test2;

CREATE TABLE test (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  field1 TEXT UNIQUE NOT NULL,
  field2 TEXT NOT NULL
);

CREATE TABLE test2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  field2 TEXT NOT NULL,
  field3 TEXT NOT NULL,
  FOREIGN KEY (test_id) REFERENCES test (id)
);
"""
      with open(p,"w") as f: f.write(contents)

  def flask(self):
    """ Run the flask server """
    self.pysync()
    self._cmdInteractive([self.poetry_p,"run","flask","--app",f"{self.name()}.flaskapp","init-db"],_show=True)
    print("connect to http://127.0.0.1:5000/<endpoint>")
    self._cmdInteractive([self.poetry_p,"run","flask","--app",f"{self.name()}.flaskapp","run","--debug"],_show=True)

if __name__ == "__main__":
  FKMake.main()

import os
from flask import Flask, session, render_template, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import numpy as np
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
#from datatime import datatime, date

load_dotenv()

app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
insp = reflection.Inspector.from_engine(engine)
print(insp.get_table_names())


@app.route("/", methods=["GET", "POST"])
def index():

    return render_template('index.html')

@app.route("/insert/<value>", methods=["GET", "POST"])
def insert(value):
    
    query = f"INSERT INTO sensorinputs (deviceid, sensorid, created, value, measuretype) VALUES (1, 1, now(), {value}, 'temp');"
    insert = db.execute(query)
    db.commit()

    return "Successfully inserted: "+query

@app.route("/results", methods=["GET", "POST"])
def results():

    data = db.execute("SELECT * FROM sensorinputs WHERE created > current_timestamp - (60 * interval '1 minute') LIMIT 50").fetchmany(50)

    return render_template('results.html', data = data)

@app.route("/raw", methods=["GET", "POST"])
def raw():

    data = db.execute("SELECT * FROM sensorinputs LIMIT 2").fetchall()

    return str(data)

@app.route("/charttest", methods=["GET", "POST"])
def charttest():

    data = db.execute("SELECT id, value, created FROM sensorinputs WHERE created > current_timestamp - (60 * interval '1 minute') ORDER BY created ASC").fetchall()

    values = []
    id = []
    labels = []

    for i in data:
        id.append(int(i[0]))
        values.append(float(i[1]))
        labels.append(i[2].strftime("%c"))

    print(type(id), type(values), type(labels))
    print(id[2])
    print(values[2])
    print(labels[2])
    

    return render_template('charttest.html', data = data, id=id, labels=labels, values=values)
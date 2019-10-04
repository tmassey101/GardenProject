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

    data = db.execute("SELECT * FROM sensorinputs WHERE created >= NOW() - INTERVAL '60 minutes' ORDER BY created ASC LIMIT 50 ;").fetchmany(50)

    return render_template('results.html', data = data)

@app.route("/raw", methods=["GET", "POST"])
def raw():

    data = db.execute("SELECT * FROM sensorinputs LIMIT 2").fetchall()

    return str(data)

@app.route("/charttest/", methods=["GET", "POST"])
def hourlyChart():

    title = "Hourly Chart"
    chartType = "'line'"
    data = db.execute("SELECT id, value, created FROM sensorinputs WHERE created >= NOW() - INTERVAL '60 minutes' ORDER BY created ASC;").fetchall()

    
    values = []
    id = []
    labels = []

    for i in data:
        id.append(int(i[0]))
        values.append(float(i[1]))
        labels.append(i[2].strftime("%c"))

    print(type(id), type(values), type(labels))
    

    return render_template('charttest.html', labels=labels, values=values, title=title, chartType=chartType)

@app.route("/charttest/daily", methods=["GET", "POST"])
def dailyChart():

    title = "Daily Chart"
    chartType = "'line'"
    data = db.execute("SELECT id, value, created FROM sensorinputs WHERE created >= NOW() - INTERVAL '24 hours' ORDER BY created ASC;").fetchall()

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
    

    return render_template('charttest.html', labels=labels, values=values, chartType=chartType)

@app.route("/charttest/dailyByHr", methods=["GET", "POST"])
def dailyChartByHr():

    title = "By Hour Chart"
    chartType = "'line'"
    data = db.execute("select date_trunc('hour', created - interval '1 minutes') as interv_start, date_trunc('hour', created - interval '1 minutes')  + interval '1 hours' as interv_end, avg(value) from sensorinputs where created >= NOW() - INTERVAL '24 hours' group by date_trunc('hour', created - interval '1 minutes') order by interv_start;").fetchall()

    values = []
    id = []
    labels = []

    for i in data:

        values.append(float(i[2]))
        labels.append(i[1].strftime("%c"))

    print(type(id), type(values), type(labels))
   
    print(values[2])
    print(labels[2])
    

    return render_template('charttest.html', labels=labels, values=values, chartType=chartType)

@app.route("/insertall/<deviceid>/<sensorid>/<measuretype>/<value>", methods=["GET", "POST"])
def insertall(deviceid, sensorid, measuretype, value):

    query = f"INSERT INTO sensorinputs (deviceid, sensorid, created, value, measuretype) VALUES ({deviceid}, {sensorid}, now(), {value}, '{measuretype}');"
    insert = db.execute(query)
    db.commit()

    return "Successfully inserted: "+query
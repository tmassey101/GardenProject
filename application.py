import os
from flask import Flask, session, render_template, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import numpy as np
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression

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
    title = "Home"
    chartType = "'line'"

    #SQL Queries
    data = db.execute("select date_trunc('hour', created - interval '1 minutes') as interv_start, date_trunc('hour', created - interval '1 minutes')  + interval '1 hours' as interv_end, avg(value) as avgvalue, measuretype from sensorinputs where created >= NOW() - INTERVAL '120 hours' group by measuretype, date_trunc('hour', created - interval '1 minutes') order by interv_start").fetchall()
    data2 = db.execute("select avg(value) as avgvalue, measuretype from sensorinputs WHERE created >= NOW() - INTERVAL '60 minutes' GROUP BY measuretype ORDER BY measuretype;").fetchall()
    moisturetrend = db.execute("select date_trunc('hour', created - interval '1 minutes') as interv_start, avg(value) as avgvalue, measuretype from sensorinputs where created >= NOW() - INTERVAL '3 days' AND measuretype = 'moisture' group by measuretype, date_trunc('hour', created - interval '1 minutes') order by interv_start;").fetchall()

    values = []
    id = []
    labels = []
    measuretype = []  
    moistureY = []
    tempY = []
    datetimeX = []

    for i in data:

        values.append(float(i[2]))
        labels.append(i[1].strftime("%c"))
        measuretype.append(str(i[3]))

        if ('temp' in str(i[3])):
            tempY.append(float(i[2]))

        elif ('moisture' in str(i[3])):
            moistureY.append(float(i[2]))

        else: 
            return ("Error : unknown measure")

    metrics = []
    key = []
    
    for i in data2:
        metrics.append(float(i[0]))
        key.append(str(i[1]))

    #set desired average moisture level to re-water
    watering_point = 500
    
    y = np.asarray(moistureY)
    x = np.asarray(labels).reshape((-1,1))
    x2 = np.arange(len(moistureY)).reshape((-1,1))

    print(y.shape, x.shape, x2.shape)

    model = LinearRegression().fit(x2, y)
    moistureCoef = float(model.coef_)
    moistureIntercept = model.intercept_

    if (model.coef_ < 0):
    
        hr_pred = (watering_point - model.intercept_) / model.coef_
        print(hr_pred)
        
        day_pred = hr_pred / 24
        print(day_pred)

    else:
        print("Plant getting wetter?")

    moistureTrend = []

    for i in np.arange(0,len(labels)):
        moistureTrend.append( (i * moistureCoef) + moistureIntercept)
        
    

    return render_template('index.html', labels=labels, values=values, chartType=chartType, measuretype=measuretype, title=title, metrics=metrics, day_pred=day_pred, moistureTrend=moistureTrend)


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
    data = db.execute("SELECT id, value, created, measuretype FROM sensorinputs WHERE created >= NOW() - INTERVAL '60 minutes' ORDER BY created ASC;").fetchall()

    
    values = []
    id = []
    labels = []
    measuretype = []

    for i in data:
        id.append(int(i[0]))
        values.append(float(i[1]))
        labels.append(i[2].strftime("%c"))
        measuretype.append(str(i[3]))

    print(type(id), type(values), type(labels), type(measuretype))
    print(id[2])
    print(values[2])
    print(labels[2])
    print(measuretype[2])
    

    return render_template('charttest.html', labels=labels, values=values, measuretype=measuretype, chartType=chartType, title=title)

@app.route("/charttest/daily", methods=["GET", "POST"])
def dailyChart():

    title = "Daily Chart"
    chartType = "'line'"
    data = db.execute("SELECT id, value, created, measuretype FROM sensorinputs WHERE created >= NOW() - INTERVAL '24 hours' ORDER BY created ASC;").fetchall()

    values = []
    id = []
    labels = []
    measuretype = []

    for i in data:
        id.append(int(i[0]))
        values.append(float(i[1]))
        labels.append(i[2].strftime("%c"))
        measuretype.append(str(i[3]))

    print(type(id), type(values), type(labels), type(measuretype))
    print(id[2])
    print(values[2])
    print(labels[2])
    print(measuretype[2])
    

    return render_template('charttest.html', labels=labels, values=values, measuretype=measuretype, chartType=chartType, title=title)

@app.route("/charttest/dailyByHr", methods=["GET", "POST"])
def dailyChartByHr():

    title = "Hourly Average Chart"
    chartType = "'line'"
    data = db.execute("select date_trunc('hour', created - interval '1 minutes') as interv_start, date_trunc('hour', created - interval '1 minutes')  + interval '1 hours' as interv_end, avg(value) as avgvalue, measuretype from sensorinputs where created >= NOW() - INTERVAL '24 hours' group by measuretype, date_trunc('hour', created - interval '1 minutes') order by interv_start").fetchall()

    values = []
    id = []
    labels = []
    measuretype = []

    for i in data:

        values.append(float(i[2]))
        labels.append(i[1].strftime("%c"))
        measuretype.append(str(i[3]))

    print(type(id), type(values), type(labels))
   
    print(values[2])
    print(labels[2])
    print(measuretype[2])
    

    return render_template('charttest.html', labels=labels, values=values, chartType=chartType, measuretype=measuretype, title=title)

@app.route("/charttest/dailyBy5d", methods=["GET", "POST"])
def dailyChartBy5d():

    title = "Hourly Average Chart"
    chartType = "'line'"
    data = db.execute("select date_trunc('hour', created - interval '1 minutes') as interv_start, date_trunc('hour', created - interval '1 minutes')  + interval '1 hours' as interv_end, avg(value) as avgvalue, measuretype from sensorinputs where created >= NOW() - INTERVAL '120 hours' group by measuretype, date_trunc('hour', created - interval '1 minutes') order by interv_start").fetchall()

    values = []
    id = []
    labels = []
    measuretype = []

    for i in data:

        values.append(float(i[2]))
        labels.append(i[1].strftime("%c"))
        measuretype.append(str(i[3]))

    print(type(id), type(values), type(labels))
   
    print(values[2])
    print(labels[2])
    print(measuretype[2])
    

    return render_template('charttest.html', labels=labels, values=values, chartType=chartType, measuretype=measuretype, title=title)

@app.route("/insertall/<deviceid>/<sensorid>/<measuretype>/<value>", methods=["GET", "POST"])
def insertall(deviceid, sensorid, measuretype, value):

    query = f"INSERT INTO sensorinputs (deviceid, sensorid, created, value, measuretype) VALUES ({deviceid}, {sensorid}, now(), {value}, '{measuretype}');"
    insert = db.execute(query)
    db.commit()

    return "Successfully inserted: "+query
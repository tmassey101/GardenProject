import os
from flask import Flask, session, render_template, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import numpy as np
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
import datetime
import pandas as pd

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


def floatList(pdList):
    
    floatsOut = pdList.to_list()
    floatsOut = [float(i) for i in floatsOut]
    return floatsOut


@app.route("/", methods=["GET", "POST"])
def index():
    title = "Home"
    chartType = "'line'"

    #SQL Query
    mlQuery = db.execute("select date_trunc('hour', created - interval '1 minutes') as CreatedHour, avg(value) as Value, TRIM(measuretype) as Type from sensorinputs group by MeasureType, CreatedHour order by CreatedHour").fetchall()

    # Create pivoted dataframe for each variable
    df = pd.DataFrame(mlQuery, columns=['CreatedHr', 'AvgValue', 'Type'])
    mldf = df.pivot(index='CreatedHr', columns='Type', values='AvgValue')
    mldf['CreatedHr'] = mldf.index
    mldf['watering'] = mldf['watering'].fillna(0)

    # Categorical True/False column for watering
    wateredTimes = mldf.loc[mldf['watering'] == 1]
    wateredTimes = wateredTimes.index

    mldf['mostRecentWater'] = wateredTimes.searchsorted(value = mldf.index) - 1
    mldf[mldf['mostRecentWater']< 0 ] = 0
    mldf['mostRecentWater'] = wateredTimes.values[mldf['mostRecentWater']]
    mldf['wateringElapsed']= (mldf.index - mldf['mostRecentWater']).astype('timedelta64[h]')

    # Calculate rolling average moisture level
    periods = 4
    mldf['Prev4Hrs'] =  mldf['moisture'].rolling(min_periods=1, window=periods).mean()

    mldf = mldf.dropna()

    # Compute Correlation for Moisture Level

    x_train = mldf['moisture']
    y_train = mldf[['temp','watering','wateringElapsed','Prev4Hrs']]

    model = LinearRegression().fit(y_train,x_train)
    print("Model Coefs = ", model.coef_)
    print("Model Interc = ", model.intercept_)

    y_pred = model.predict(y_train)
    mldf['moisturePred'] = y_pred

    # Remove first line (zeros due to historical calc)
    mldf = mldf.iloc[1:]

    ### Create Historical Variables for Plotting
    print(mldf.columns)
    plotTemp = floatList(mldf['temp'])
    plotMoisture = floatList(mldf['moisture']) 
    plotWatering = floatList(mldf['watering'])
    plotMoisturePred = floatList(mldf['moisturePred'])
    
    labels = mldf['CreatedHr'].to_list()
    labels = [str(i) for i in labels]

    # Latest Metrics for dashboard
    lastTemp = plotTemp[-1]
    lastMoist = plotMoisture[-1]
    waterings = mldf.index[mldf['watering'] == 1]
    latestWater = waterings.to_list()[-1]
    

    ### Set desired average moisture level to re-water
    watering_point = 500

    ### Calculate linear moisture trend and rewater point
    TrendDays = 3
    Moisture3d = plotMoisture

    y = np.asarray(Moisture3d)
    x = np.arange(len(Moisture3d)).reshape((-1,1))

    linearModel = LinearRegression().fit(x, y)
    linMoistureCoef = float(linearModel.coef_)
    linMoistureIntercept = linearModel.intercept_
   
    hr_pred = (watering_point - linMoistureIntercept) / linMoistureIntercept
    day_pred = hr_pred / 24
    
    moistureTrend = []
    for i in np.arange(0,len(Moisture3d)):
        moistureTrend.append( (i * linMoistureCoef) + linMoistureIntercept)

    return render_template('test.html', latestWater=latestWater, lastTemp=lastTemp, lastMoist=lastMoist, plotTemp=plotTemp, plotMoisture=plotMoisture, plotWatering=plotWatering, plotMoisturePred=plotMoisturePred, labels=labels, chartType=chartType, title=title, day_pred=day_pred, moistureTrend=moistureTrend)


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

@app.route("/test", methods=["GET", "POST"])
def test():
    title = "Home"
    chartType = "'line'"

    #SQL Query
    mlQuery = db.execute("select date_trunc('hour', created - interval '1 minutes') as CreatedHour, avg(value) as Value, TRIM(measuretype) as Type from sensorinputs group by MeasureType, CreatedHour order by CreatedHour").fetchall()

    # Create pivoted dataframe for each variable
    df = pd.DataFrame(mlQuery, columns=['CreatedHr', 'AvgValue', 'Type'])
    mldf = df.pivot(index='CreatedHr', columns='Type', values='AvgValue')
    mldf['CreatedHr'] = mldf.index
    mldf['watering'] = mldf['watering'].fillna(0)

    # Categorical True/False column for watering
    wateredTimes = mldf.loc[mldf['watering'] == 1]
    wateredTimes = wateredTimes.index

    mldf['mostRecentWater'] = wateredTimes.searchsorted(value = mldf.index) - 1
    mldf[mldf['mostRecentWater']< 0 ] = 0
    mldf['mostRecentWater'] = wateredTimes.values[mldf['mostRecentWater']]
    mldf['wateringElapsed']= (mldf.index - mldf['mostRecentWater']).astype('timedelta64[h]')

    # Calculate rolling average moisture level
    periods = 4
    mldf['Prev4Hrs'] =  mldf['moisture'].rolling(min_periods=1, window=periods).mean()

    mldf = mldf.dropna()

    # Compute Correlation for Moisture Level

    x_train = mldf['moisture']
    y_train = mldf[['temp','watering','wateringElapsed','Prev4Hrs']]

    model = LinearRegression().fit(y_train,x_train)
    print("Model Coefs = ", model.coef_)
    print("Model Interc = ", model.intercept_)

    y_pred = model.predict(y_train)
    mldf['moisturePred'] = y_pred

    # Remove first line (zeros due to historical calc)
    mldf = mldf.iloc[1:]

    ### Create Historical Variables for Plotting
    print(mldf.columns)
    plotTemp = floatList(mldf['temp'])
    plotMoisture = floatList(mldf['moisture']) 
    plotWatering = floatList(mldf['watering'])
    plotMoisturePred = floatList(mldf['moisturePred'])
    
    labels = mldf['CreatedHr'].to_list()
    labels = [str(i) for i in labels]

    # Latest Metrics for dashboard
    lastTemp = plotTemp[-1]
    lastMoist = plotMoisture[-1]
    waterings = mldf.index[mldf['watering'] == 1]
    latestWater = waterings.to_list()[-1]
    

    ### Set desired average moisture level to re-water
    watering_point = 500

    ### Calculate linear moisture trend and rewater point
    TrendDays = 3
    Moisture3d = plotMoisture

    y = np.asarray(Moisture3d)
    x = np.arange(len(Moisture3d)).reshape((-1,1))

    linearModel = LinearRegression().fit(x, y)
    linMoistureCoef = float(linearModel.coef_)
    linMoistureIntercept = linearModel.intercept_
   
    hr_pred = (watering_point - linMoistureIntercept) / linMoistureIntercept
    day_pred = hr_pred / 24
    
    moistureTrend = []
    for i in np.arange(0,len(Moisture3d)):
        moistureTrend.append( (i * linMoistureCoef) + linMoistureIntercept)

    
    ####### NEW PREDICTION SECTION #############
    rollingPeriods = -4
    lastElapsed = floatList(mldf['wateringElapsed'])

    histMoisture = np.mean(plotMoisture[rollingPeriods:]) #base historical moisture on last x periods
    futTemp = plotTemp[-24:] #base historical temps on last 24 hours
    

    hours = 72 #enter days of history as future temps
    for i in range(hours-24): #append multple days as set
        futTemp.append(futTemp)

    histWater = lastElapsed[-1]
    futElapsed = [histWater]

    i = 1
    while i < 72:
        futElapsed.append(futElapsed[0]+i)
        i+=1

    print(len(futTemp))
    print(len(futElapsed))
    
    
    futureDF = pd.DataFrame()
    futureDF['futTemp'] = futTemp
    futureDF['futElapsed'] = futElapsed                
    

    print(futureDF.columns)
    print(futureDF.head(5))
    

    return render_template('test.html', latestWater=latestWater, lastTemp=lastTemp, lastMoist=lastMoist, plotTemp=plotTemp, plotMoisture=plotMoisture, plotWatering=plotWatering, plotMoisturePred=plotMoisturePred, labels=labels, chartType=chartType, title=title, day_pred=day_pred, moistureTrend=moistureTrend)

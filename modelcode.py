import os
from flask import Flask, session, render_template, jsonify
#from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
import numpy as np
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
import datetime
import pandas as pd


load_dotenv()

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))

db = scoped_session(sessionmaker(bind=engine))
insp = reflection.Inspector.from_engine(engine)


# New ML Model

#SQL Queries
mlQuery = db.execute("select date_trunc('hour', created - interval '1 minutes') as CreatedHour, avg(value) as Value, TRIM(measuretype) as Type from sensorinputs group by MeasureType, CreatedHour order by CreatedHour").fetchall()

df = pd.DataFrame(mlQuery, columns=['CreatedHr', 'AvgValue', 'Type'])

mldf = df.pivot(index='CreatedHr', columns='Type', values='AvgValue')
mldf['CreatedHr'] = mldf.index
mldf['watering'] = mldf['watering'].fillna(0)

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


x_train = mldf['moisture']
y_train = mldf[['temp','watering','wateringElapsed','Prev4Hrs']]

model = LinearRegression()
model.fit(y_train,x_train) 
print(model.coef_)
print(model.intercept_)

y_pred = model.predict(y_train)
mldf['moisturePred'] = y_pred

###


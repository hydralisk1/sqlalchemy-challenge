# import dependencies
from flask import Flask, jsonify, redirect
import numpy as np
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import datetime, timedelta
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect = True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

session = Session(engine)

# Store latest date and date of last year
latest_date = datetime.strptime(session.query(func.max(Measurement.date)).first()[0], "%Y-%m-%d")
last_year_date = latest_date - timedelta(days = 365)
session.close()

app = Flask(__name__)
# Prevent jsonify from sorting data 
app.config["JSON_SORT_KEYS"] = False

@app.route("/")
def home():
    return (
        "API Routes<br/>"
        "<hr/>"
        "<table style='border-style: none;'>"
        "<tr><td>/api/v1.0/precipitation</td><td>Precipitation data for a year</td></tr>"
        "<tr><td>/api/v1.0/stations</td><td>Station data</td></tr>"
        "<tr><td>/api/v1.0/tobs</td><td>Temperature observation data for the most active station</td></tr>"
        "<tr><td>/api/v1.0/&lt;start_date&gt;</td><td>Minimum, maximum and average temperature from start_date to the latest date on the data</td></tr>"
        "<tr><td>/api/v1.0/&lt;statrt_date&gt;/&lt;end_date&gt;</td><td>Minimum, maximum and average temperature from start_date to end_date</td></tr></table>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date > last_year_date).all()
    session.close()

    dict_list = []

    for row in results:
        dict = {}
        dict[row[0]] = row[1]
        dict_list.append(dict)

    return jsonify(dict_list)

@app.route("/api/v1.0/stations")
def stations():
    results = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()
    session.close()

    station_list = []

    for row in results:
        dict = {}
        dict["id"] = row[0]
        dict["station"] = row[1]
        dict["name"] = row[2]
        dict["latitude"] = row[3]
        dict["longitude"] = row[4]
        dict["elevation"] = row[5]
        station_list.append(dict)
    
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
                          group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    
    results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).\
                            filter(Measurement.date > last_year_date).all()
    session.close()

    most_list = [{"Station":most_active_station}]

    for row in results:
        dict = {}
        dict[row[0]] = row[1]
        most_list.append(dict)

    return jsonify(most_list)


@app.route("/api/v1.0/<start>/")
def temp_st(start):
    end = latest_date.strftime("%Y-%m-%d")
    # Redirect with end date
    return redirect(f"/api/v1.0/{start}/{end}")

@app.route("/api/v1.0/<start>/<end>")
def temp(start, end):
    tmin, tavg, tmax = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                       filter(Measurement.date >= start).filter(Measurement.date <= end).first()
    session.close()

    return (
        f"From {start} to {end}<br/>"
        f"=======================<br/>"
        f"Min. Temperature: {tmin}<br/>"
        f"Max. Temperature: {tmax}<br/>"
        f"Avg. Temperature: {round(tavg, 2)}<br/>"
    )


if __name__ == "__main__":
    app.run(debug=True)
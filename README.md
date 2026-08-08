# 🌫️ Kathmandu Valley AQI Prediction System

> **Real-time Air Quality Monitoring, Next-Day Forecasting & Model Comparison**

An end-to-end AQI prediction and monitoring system for the **Kathmandu Valley**.  
The system collects current environmental data, stores historical observations, engineers time-series features, generates next-day forecasts using **XGBoost**, and continuously updates an **online-learning River model** as new observations become available.

---

## 📌 Project Overview

Air quality changes continuously with pollution levels, weather conditions, seasonality, and recent historical trends. This project combines:

- 🌐 Current environmental data collection
- 🗄️ PostgreSQL-based historical storage
- 🧮 Time-series feature engineering
- 🤖 **XGBoost** batch-learning forecasting
- 🔄 **River** online-learning forecasting
- 📊 Actual-vs-predicted visualization
- 📅 Historical forecast lookup
- ⚖️ Model comparison: **XGBoost vs River vs Actual**
- 📰 AQI/news information on the dashboard

The goal is not only to produce an AQI forecast, but to provide a complete pipeline from **data acquisition → processing → prediction → storage → visualization → continuous model updating**.

---

## ✨ Main Features

| Feature | Description |
|---|---|
| 📡 Real-time Monitoring | Displays the latest observed AQI and environmental parameters |
| 🔮 Next-Day Forecast | Generates forecasts for AQI, PM2.5, PM10 and temperature |
| 🤖 XGBoost | Main batch-learning multi-output forecasting model |
| 🔄 River | Online-learning model that can update when new actual observations arrive |
| 📊 Forecast Review | Compares previous predictions with the actual observation |
| 📈 AQI Trends | Visualizes actual and predicted AQI over time |
| 🌡️ Weather Forecasting | Compares predicted and observed temperature |
| 🫁 Particulate Matter | Tracks PM2.5 and PM10 predictions versus observations |
| 📅 Historical Calendar | Select a date and inspect stored observations and forecasts |
| ⚖️ Model Comparison | Compares XGBoost, River and actual values for the same target date |

---

## 🖥️ Dashboard

### Overview & AQI Trends

The dashboard provides a high-level view of the current AQI, next-day forecast, model performance information, forecast review, AQI trends, particulate matter and temperature.

![Dashboard Overview](https://github.com/PiyushPandey369/Project-I/blob/main/Project_I/dashboard-overview.png)

### Historical Forecast Lookup

The calendar interface allows a user to select a historical date and compare the observed sensor values against the saved forecast for that date.

![Historical Forecast Lookup](https://github.com/PiyushPandey369/Project-I/blob/main/Project_I/historical-forecast.png)

---

## 🧠 Machine Learning Approach

### 1. XGBoost — Batch Learning

XGBoost is the primary forecasting model in the existing system.

The model is trained using historical AQI and environmental data and is saved as a serialized model:

```text
model/
└── multioutput_xgboost_aqi_forecaster.pkl
```

The model produces multiple outputs:

```text
PM2.5
PM10
AQI
Temperature
```

The production pipeline loads the saved model and uses the latest historical data plus engineered features to generate the next-day forecast.

---

### 2. River — Online Learning

River is used as the online-learning component.

Unlike the traditional batch-learning workflow, the River model can learn incrementally as new observations arrive.

Conceptually:

```text
Historical / warm-up data
        ↓
Initialize River model
        ↓
Generate prediction
        ↓
Wait for actual observation
        ↓
Compare prediction with actual
        ↓
learn_one()
        ↓
Updated model
        ↓
Next prediction
        ↓
Repeat
```

The River model uses the same general feature representation required by the production forecasting pipeline, including lag, rolling, calendar, cyclic, trend and seasonal information.

---

## 🔄 Production Pipeline

When the **Sync Data Pipeline** button is pressed, the system follows the production workflow:

```text
External Data Sources
        │
        ▼
Current Data Collector
        │
        ▼
Daily Data / PostgreSQL
        │
        ▼
History Retrieval
        │
        ▼
Feature Engineering
        │
        ▼
72 Feature Representation
        │
        ├───────────────────┐
        ▼                   ▼
     XGBoost              River
        │                   │
        ▼                   ▼
   Forecast Output     Forecast Output
        │                   │
        └─────────┬─────────┘
                  ▼
           Store Predictions
                  │
                  ▼
             Web Dashboard
```

For River, the learning cycle additionally uses the newly observed actual data:

```text
New Actual Observation
          ↓
     River Update
          ↓
       learn_one()
          ↓
  Updated Model State
```

---

## 🧮 Feature Engineering

The forecasting pipeline generates a **72-feature representation**.

The feature groups include:

### Environmental Features

```text
PM2.5
PM10
TSP
Temperature
Humidity
Wind Speed
Wind Direction
Sea Level Pressure
Visibility
Precipitation
Solar Radiation
AQI
```

### Lag Features

Recent historical values are included to capture temporal dependencies:

```text
lag1
lag3
lag7
lag14
```

for relevant variables such as:

```text
PM2.5
PM10
AQI
Temperature
```

### Rolling Features

Rolling statistics capture recent behavior:

```text
rolling mean
rolling standard deviation
```

over multiple windows.

### Difference / Trend Features

Difference features help represent whether pollution is increasing or decreasing relative to previous observations.

### Calendar Features

```text
Year
Month
Day
Day of Week
Day of Year
Weekend indicator
```

### Cyclic Features

Cyclic encoding represents periodic behavior such as:

```text
Month
Day of Week
Day of Year
```

using sine/cosine transformations.

### Seasonal Encoding

The system includes:

```text
Autumn
Monsoon
Spring
Winter
```

---

## 🗄️ Data Storage

The system uses multiple storage mechanisms for different purposes.

### PostgreSQL

The database stores the main daily observations and XGBoost prediction records.

Conceptually:

```text
aqi_daily
├── datetime
├── pm25
├── pm10
├── tsp
├── temp
├── humidity
├── windspeed
├── winddir
├── sealevelpressure
├── visibility
├── precipitation
├── solarradiation
└── aqi
```

The prediction table stores the XGBoost forecast:

```text
predicted_values
├── prediction_date
├── predicted_pm25
├── predicted_pm10
├── predicted_aqi
└── predicted_temperature
```

### River Prediction CSV

River predictions are separately recorded so that they can be compared later with XGBoost and actual observations:

```text
data/
└── river_predicted_values.csv
```

This allows the dashboard to build a comparison such as:

| Parameter | XGBoost | River | Actual |
|---|---:|---:|---:|
| AQI | Forecast | Forecast | Observed |
| PM2.5 | Forecast | Forecast | Observed |
| PM10 | Forecast | Forecast | Observed |
| Temperature | Forecast | Forecast | Observed |

---

## 📊 Correct Model Comparison Logic

The comparison is **date-aligned**.

For example:

```text
August 7
   │
   ├── XGBoost predicts August 8
   └── River predicts August 8

August 8
   │
   └── Actual August 8 observation becomes available

Comparison:
August 8 XGBoost prediction
        vs
August 8 River prediction
        vs
August 8 Actual
```

This prevents a future observation from being incorrectly compared with a forecast.

---

## 📈 Forecast Evaluation

The system can evaluate forecasts using common regression metrics such as:

- **MAE** — Mean Absolute Error
- **RMSE** — Root Mean Squared Error
- **R²** — Coefficient of Determination

For a prediction `ŷ` and actual value `y`:

```text
MAE  → average absolute prediction error

RMSE → penalizes larger errors more strongly

R²   → measures how much variation is explained by the model
```

For online learning, evaluation should also be performed chronologically because new observations arrive over time.

---

## 🏗️ Project Structure

```text
Project_I/
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
│
├── fetch_data.py
├── ingest.py
├── predict.py
└── run_pipeline.py
│
├── api/
│   ├── main.py
│   ├── route.py
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── current.css
│   │   │   ├── prediction.css
│   │   │   └── style.css
│   │   │
│   │   └── js/
│   │       ├── current.js
│   │       ├── dashboard.js
│   │       └── prediction.js
│   │
│   └── templates/
│       ├── current_data.html
│       ├── index.html
│       └── prediction.html
│
├── data/
│   ├── daily_data.csv
│   ├── river_predicted_values.csv
│   │
│   ├── raw/
│   ├── processed/
│   └── features/
│
├── data_fetching_and_db/
│   ├── config/
│   │   └── config_.py
│   │
│   └── services/
│       ├── csv_services.py
│       ├── db_service.py
│       ├── news_service.py
│       ├── prediction_service.py
│       ├── river_update_service.py
│       └── river_prediction_csv_service.py
│
├── model/
│   ├── model_services.py
│   ├── multioutput_xgboost_aqi_forecaster.pkl
│   ├── river_model_service.py
│   └── river_aqi_forecaster.pkl
│
├── notebooks/
│   └── Data Analysis/
│       ├── 01_Data_Cleaning_Pollution.ipynb
│       ├── 02_Data_Handling.ipynb
│       ├── 03_Temp_Data_Managing.ipynb
│       ├── 04_Merging_Dataset.ipynb
│       ├── 05_EDA.ipynb
│       └── Model_Evaluation/
│           ├── Random_Forest.ipynb
│           └── XGBoost.ipynb
│
└── src/
    └── features/
        ├── feature_calendar.py
        ├── feature_cyclic.py
        ├── feature_date_pipeline.py
        ├── feature_lag.py
        ├── feature_master_pipeline.py
        ├── feature_rolling.py
        ├── feature_season_encoding.py
        ├── feature_trend.py
        └── feature_ts_pipeline.py
```

---

## 🛠️ Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn
- PostgreSQL

### Machine Learning

- XGBoost
- River
- scikit-learn
- Pandas
- NumPy

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2 templates

### Data

- Historical AQI/environmental datasets
- Current weather and environmental API data
- PostgreSQL
- CSV-based River prediction history

---

## ⚙️ Installation

### 1. Clone the project

```bash
git clone <YOUR_REPOSITORY_URL>
cd Project_I
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file containing the required database and API configuration.

Example structure:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password

OPENWEATHER_API_KEY=your_api_key
```

Do **not** commit `.env` or API keys to Git.

---

## ▶️ Running the Application

Start the FastAPI server:

```bash
uvicorn api.main:app --reload
```

Then open the local dashboard in your browser.

To execute the complete synchronization pipeline:

```bash
python run_pipeline.py
```

The pipeline performs the current-data collection, database ingestion, River update, and next-day prediction workflow.

---

## 🔁 Daily Learning Concept

The system is designed around a chronological forecasting loop:

```text
Day t
 │
 ├── Collect actual environmental data
 │
 ├── Store observation
 │
 ├── Update River model with actual observation
 │
 ├── Generate Day t+1 forecast
 │
 └── Save predictions
          │
          ▼
       Day t+1
          │
          ├── New actual observation
          │
          ├── Evaluate previous forecast
          │
          └── Update River model
```

This makes the River component different from the fixed XGBoost model: the River model is designed to **adapt incrementally as new observations arrive**.

---

## 🎯 Project Objectives

1. Collect and integrate AQI and meteorological data.
2. Clean and preprocess historical environmental data.
3. Engineer meaningful time-series and seasonal features.
4. Develop a multi-output XGBoost forecasting model.
5. Integrate an online-learning River model.
6. Generate next-day AQI and environmental forecasts.
7. Store predictions and actual observations for later evaluation.
8. Compare model predictions against actual observations.
9. Provide an interactive dashboard for monitoring and historical analysis.

---

## 🔬 Model Comparison

The project provides two complementary learning approaches:

| Aspect | XGBoost | River |
|---|---|---|
| Learning style | Batch learning | Online learning |
| Training pattern | Trained using historical dataset | Updated incrementally |
| New observation | Requires retraining to incorporate it | Can learn from it incrementally |
| Best suited for | Strong offline forecasting | Continuously changing data streams |
| Prediction | Next-day forecast | Next-day forecast |
| Model update | Periodic retraining | `learn_one()` update |
| Project role | Main established forecasting model | Adaptive forecasting model |

The dashboard allows their outputs to be compared against the actual observation once that observation becomes available.

---

## 📜 License

This project is intended for academic/project development purposes. Add your preferred license information here.

---

## 👨‍💻 Project

**Kathmandu Valley AQI Prediction System**

An end-to-end environmental intelligence system combining historical analysis, real-time data collection, machine learning forecasting, online learning and interactive visualization.

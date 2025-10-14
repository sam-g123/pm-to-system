import numpy as np
from sklearn.linear_model import LinearRegression  # For weighted model

def calculate_score(focus_time, completion_rate, time_efficiency):
    # TODO: Train regression model; mock for now
    X = np.array([[focus_time], [completion_rate], [time_efficiency]])
    model = LinearRegression().fit(X, [80])  # Placeholder
    score = model.predict(X)[0]
    return min(max(score, 0), 100)
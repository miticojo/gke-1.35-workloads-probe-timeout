
from flask import Flask, Response
import time
import random

app = Flask(__name__)

@app.route('/healthy')
def healthy():
    return "OK"

@app.route('/slow')
def slow():
    time.sleep(5)
    return "OK"

@app.route('/flaky')
def flaky():
    if random.random() < 0.5:
        time.sleep(5)
        return "OK"
    else:
        return "OK"

@app.route('/timeout')
def timeout():
    time.sleep(10)
    return "OK"

@app.route('/startup')
def startup():
    # Simulate a slow startup
    time.sleep(10)
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

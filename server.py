from flask import Flask, request, jsonify, render_template
import pymongo
from datetime import datetime
import threading
from flask_caching import Cache
# import chors
from flask_cors import CORS


app = Flask(__name__)

# Enable CORS
CORS(app)

global_data = {}
mongodb_url = "mongodb://localhost:27017/"
database_name = "smart_chair"
collection_name = "sensor_data"

# Define a lock to protect the global_data dictionary when accessed by multiple threads
data_lock = threading.Lock()


def store_to_db(data):
    try:
        client = pymongo.MongoClient(mongodb_url)
        db = client[database_name]
        collection = db[collection_name]
        collection.insert_one(data)
        client.close()
    except Exception as e:
        print(e)


@app.route('/iot', methods=['POST'])
def store_data():
    try:
        # Extract form data
        a1 = request.form.get('a1')
        a2 = request.form.get('a2')
        a3 = request.form.get('a3')
        a4 = request.form.get('a4')
        a5 = request.form.get('a5')
        a6 = request.form.get('a6')
        a7 = request.form.get('a7')
        a8 = request.form.get('a8')
        chair_id = request.form.get('chair_id')
        timestamp = datetime.now()
        type_of_device=request.form.get('type_of_device')
        # Store data in MongoDB
        data = {
            "a1": a1,
            "a2": a2,
            "a3": a3,
            "a4": a4,
            "a5": a5,
            "a6": a6,
            "a7": a7,
            "a8": a8,
            "chair_id": chair_id,
            "timestamp": timestamp,
            "type_of_device":type_of_device
        }

        with data_lock:
            global_data[chair_id] = data

        # using multi thread deamon store data to db
        # thread = threading.Thread(target=store_to_db, args=(data,))
        # thread.daemon = True
        # thread.start()

        return jsonify({"message": "Data stored successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/data/<chair_id>', methods=['GET'])
def get_data(chair_id):
    try:
        client = pymongo.MongoClient(mongodb_url)
        db = client[database_name]
        collection = db[collection_name]

        # Query the collection based on chair_id
        cursor = collection.find({"chair_id": chair_id})

        # Convert ObjectId to string for each document
        data = []
        for document in cursor:
            document['_id'] = str(document['_id'])
            data.append(document)

        client.close()

        if not data:
            return jsonify({"message": "No data found for chair_id: " + chair_id})

        return render_template('data.html', chair_id=chair_id, data=data)
    except Exception as e:
        return jsonify({"error": str(e)})




@app.route('/count', methods=['GET'])
def get_chair_id_count():
    try:
        # Retrieve the list of chair_id values from the global data dictionary
        with data_lock:
            chair_ids = list(global_data.keys())
        # get count of chair_id
        chair_id_count = len(chair_ids)
        # todo:: return type, active / inactive status
        active_list = []
        inactive_list = []
        # check the time stamp of the data
        for chair_id in chair_ids:
            data = global_data[chair_id]
            timestamp = data['timestamp']
            current_time = datetime.now()
            type_of_device = data['type_of_device']
            # if the difference between the current time and the timestamp is less than 10 seconds, the chair is active
            if (current_time - timestamp).seconds < 10:
                # append to active list and tyoe of device
                active_list.append({'chair_id': chair_id, 'type_of_device': type_of_device})

            else:
                inactive_list.append({'chair_id': chair_id, 'type_of_device': type_of_device})
        return jsonify({"number": chair_id_count, "chair_ids": chair_ids, "active_list": active_list, "inactive_list": inactive_list})
    except Exception as e:
        return jsonify({"error": str(e)})




@app.route('/app/<chair_id>', methods=['GET'])
def get_latest_data(chair_id):
    try:
        # Retrieve data from the global dictionary based on chair_id
        with data_lock:
            latest_data = global_data.get(chair_id)

        if latest_data is None:
            return jsonify({"message": f"No data found for chair_id: {chair_id}"})
        else:
            # Convert ObjectId to string if it exists in the data
            if '_id' in latest_data:
                latest_data['_id'] = str(latest_data['_id'])
            return jsonify(latest_data)
    except Exception as e:
        return jsonify({"error": str(e)})


def run_flask_app():
    # app.run("host":"0.0.0.0")
    # run server in port 0.0.0.0
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

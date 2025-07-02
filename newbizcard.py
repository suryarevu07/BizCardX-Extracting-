from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import numpy as np
import pandas as pd
import easyocr
from PIL import Image
import re
import mysql.connector
from io import BytesIO
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Database connection
class BusinessCardManager:
    def __init__(self):
        self.mydb = None
        self.mycursor = None
        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",  # Update to your MySQL password
                database='business_card'
            )
            self.mycursor = self.mydb.cursor(buffered=True)
        except mysql.connector.Error as e:
            print(f"Database connection failed: {e}")
            raise

    def create_table(self):
        if self.mycursor and self.mydb:
            query = """
            CREATE TABLE IF NOT EXISTS Cards (
                Company_name VARCHAR(50),
                Card_holder VARCHAR(50),
                Designation VARCHAR(50),
                Mobile_number VARCHAR(50),  -- Increased from 15 to 50
                Email VARCHAR(50),
                Website VARCHAR(50),
                Area VARCHAR(50),
                City VARCHAR(50),
                State VARCHAR(50),
                Pin_code VARCHAR(10)
            )
            """
            self.mycursor.execute(query)
            self.mydb.commit()
            print('Table created successfully')

    def insert_data(self, df):
        if self.mycursor and self.mydb:
            query = """
            INSERT INTO Cards (Company_name, Card_holder, Designation, Mobile_number, Email, Website, Area, City, State, Pin_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for _, row in df.iterrows():
                values = tuple(row.values)
                self.mycursor.execute(query, values)
            self.mydb.commit()
            print('Data inserted successfully')

    def retrieve_data(self, card_holder):
        if self.mycursor and self.mydb:
            query = "SELECT * FROM Cards WHERE Card_holder = %s"
            self.mycursor.execute(query, (card_holder,))
            return self.mycursor.fetchall()
        return []

    def modify_data(self, card_holder, field_to_update, new_value):
        if self.mycursor and self.mydb:
            query = f"UPDATE Cards SET {field_to_update} = %s WHERE Card_holder = %s"
            self.mycursor.execute(query, (new_value, card_holder))
            self.mydb.commit()

    def delete_data(self, card_holder):
        if self.mycursor and self.mydb:
            query = "DELETE FROM Cards WHERE Card_holder = %s"
            self.mycursor.execute(query, (card_holder,))
            self.mydb.commit()

    def get_all_records(self):
        if self.mycursor and self.mydb:
            query = "SELECT * FROM Cards"
            self.mycursor.execute(query)
            return self.mycursor.fetchall()
        return []

    def __del__(self):
        if self.mycursor:
            self.mycursor.close()
        if self.mydb:
            self.mydb.close()

# Initialize manager
try:
    manager = BusinessCardManager()
    manager.create_table()
except Exception as e:
    print(f"Failed to initialize BusinessCardManager: {e}")

# OCR and data extraction
def extract_business_card(image_data):
    input_image = Image.open(BytesIO(image_data))
    image_np = np.array(input_image)
    reader = easyocr.Reader(['en'])
    extract_data = reader.readtext(image_np, detail=0)

    structured_data = {
        "Company_name": [], "Card_holder": [], "Designation": [],
        "Mobile_number": [], "Email": [], "Website": [],
        "Area": [], "City": [], "State": [], "Pin_code": []
    }
    city = ""

    for jo, i in enumerate(extract_data):
        if "www " in i.lower() or "www." in i.lower():
            structured_data["Website"].append(i)
        elif "WWW" in i:
            structured_data["Website"].append(extract_data[jo-1] + "." + extract_data[jo])
        
        elif "@" in i:
            structured_data["Email"].append(i)
        
        elif "-" in i:
            structured_data["Mobile_number"].append(i)
            if len(structured_data["Mobile_number"]) == 2:
                structured_data["Mobile_number"] = [" & ".join(structured_data["Mobile_number"])]

        elif jo == len(extract_data) - 1:
            structured_data["Company_name"].append(i)

        elif jo == 0:
            structured_data["Card_holder"].append(i)

        elif jo == 1:
            structured_data["Designation"].append(i)

        if re.findall("^[0-9].+, [a-zA-Z]+", i):
            structured_data["Area"].append(i.split(",")[0])
        elif re.findall("[0-9] [a-zA-Z]+", i):
            structured_data["Area"].append(i)

        match1 = re.findall(".*St , ([a-zA-Z]+).*", i)
        match2 = re.findall(".*St,, ([a-zA-Z]+).*", i)
        match3 = re.findall("^[E].*", i)
        if match1:
            city = match1[0]
        elif match2:
            city = match2[0]
        elif match3:
            city = match3[0]

        state_match = re.findall("[a-zA-Z]{9} +[0-9]", i)
        if state_match:
            structured_data["State"].append(i[:9])
        elif re.findall("^[0-9].+, ([a-zA-Z]+);", i):
            structured_data["State"].append(i.split()[-1])
        if len(structured_data["State"]) == 2:
            structured_data["State"].pop(0)

        if len(i) >= 6 and i.isdigit():
            structured_data["Pin_code"].append(i)
        elif re.findall("[a-zA-Z]{9} +[0-9]", i):
            structured_data["Pin_code"].append(i[10:])

    structured_data["City"].append(city)
    return pd.DataFrame(structured_data)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    image = request.files['image']
    socketio.emit('loading', {'status': 'start'})
    try:
        df = extract_business_card(image.read())
        socketio.emit('update', {'message': 'Data extracted successfully', 'data': df.to_dict(orient="records"), 'action': 'extract'})
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"message": "Data extracted", "data": df.to_dict(orient="records")})
    except Exception as e:
        print(f"Extraction error: {e}")
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"error": f"Error processing image: {e}"}), 500

@app.route('/insert', methods=['POST'])
def insert_data():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400
    socketio.emit('loading', {'status': 'start'})
    try:
        df = pd.DataFrame(data['data'])
        manager.insert_data(df)
        socketio.emit('update', {'message': 'Data inserted successfully'})
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"message": "Data inserted successfully"})
    except Exception as e:
        print(f"Insertion error: {e}")
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"error": f"Error inserting data: {e}"}), 500

@app.route('/retrieve', methods=['GET'])
def retrieve_data():
    card_holder = request.args.get('card_holder')
    if not card_holder:
        return jsonify({"error": "Card holder name required"}), 400
    socketio.emit('loading', {'status': 'start'})
    try:
        data = manager.retrieve_data(card_holder)
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"data": data})
    except Exception as e:
        print(f"Retrieval error: {e}")
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"error": f"Error retrieving data: {e}"}), 500

@app.route('/modify', methods=['POST'])
def modify_data():
    card_holder = request.form.get('card_holder')
    field_to_update = request.form.get('field_to_update')
    new_value = request.form.get('new_value')
    if not all([card_holder, field_to_update, new_value]):
        return jsonify({"error": "All fields required"}), 400
    socketio.emit('loading', {'status': 'start'})
    try:
        manager.modify_data(card_holder, field_to_update, new_value)
        socketio.emit('update', {'message': 'Data modified successfully'})
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"message": "Data modified successfully"})
    except Exception as e:
        print(f"Modification error: {e}")
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"error": f"Error modifying data: {e}"}), 500

@app.route('/delete', methods=['POST'])
def delete_data():
    card_holder = request.form.get('card_holder')
    if not card_holder:
        return jsonify({"error": "Card holder name required"}), 400
    socketio.emit('loading', {'status': 'start'})
    try:
        manager.delete_data(card_holder)
        socketio.emit('update', {'message': 'Data deleted successfully'})
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"message": "Data deleted successfully"})
    except Exception as e:
        print(f"Deletion error: {e}")
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"error": f"Error deleting data: {e}"}), 500

@app.route('/all_records', methods=['GET'])
def get_all_records():
    socketio.emit('loading', {'status': 'start'})
    try:
        data = manager.get_all_records()
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"data": data})
    except Exception as e:
        print(f"Records fetch error: {e}")
        socketio.emit('loading', {'status': 'stop'})
        return jsonify({"error": f"Error fetching records: {e}"}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

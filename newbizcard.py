
import numpy as np
import streamlit as st
import pandas as pd
import easyocr
from PIL import Image
import re
import mysql.connector


st.title("Business Card Extracting")

# Sidebar for image upload
with st.sidebar:
    st.header("Business Card")
    image_file = st.file_uploader("Upload your business card image", type=["jpg", "png", "jpeg"])

# If an image is uploaded
if image_file:
    input_image = Image.open(image_file)
    
    image_np = np.array(input_image)
    
    # Display the uploaded business card image
    st.image(input_image, caption='Uploaded Business Card', width=400) 

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])
    
    # Extract text from the image
    extract_data = reader.readtext(image_np, detail=0)

    structed_data={
        "Company_name": [],
        "Card_holder": [],
        "Designation": [],
        "Mobile_number": [],
        "Email": [],
        "Website": [],
        "Area": [],
        "City": [],
        "State": [],
        "Pin_code": [],
        
    }

    city = ""           # Initialize the city variable
    for jo,i in enumerate(extract_data):
    
        if "www " in i.lower() or "www." in i.lower():    # To get WEBSITE_URL
            structed_data["Website"].append(i)
        elif "WWW" in i:
            structed_data["Website"].append(extract_data[jo-1] + "." + extract_data[jo])
        
        elif "@" in i:           # To get EMAIL ID
            structed_data["Email"].append(i)
        
        elif "-" in i:                  # To get MOBILE NUMBER
            structed_data["Mobile_number"].append(i)
            if len(structed_data["Mobile_number"]) == 2:
                structed_data["Mobile_number"] = " & ".join(structed_data["Mobile_number"])
        
        elif jo == len(extract_data) - 1 :
            structed_data["Company_name"] .append(i) 

    
        elif jo == 0:             # To get CARD HOLDER NAME
            structed_data["Card_holder"].append(i)

        
        elif jo == 1:            # To get DESIGNATION
            structed_data["Designation"].append(i)
    
        if re.findall("^[0-9].+, [a-zA-Z]+", i):       # To get AREA
            structed_data["Area"].append(i.split(",")[0])
        elif re.findall("[0-9] [a-zA-Z]+", i):
            structed_data["Area"].append(i)
        
        match1 = re.findall(".+St , ([a-zA-Z]+).+", i)     # To get CITY NAME
        match2 = re.findall(".+St,, ([a-zA-Z]+).+", i)
        match3 = re.findall("^[E].*", i)
        if match1:
            city = match1[0]  # Assign the matched city value
        elif match2:
            city = match2[0]  # Assign the matched city value
        elif match3:
            city = match3[0]  # Assign the matched city value

            
        state_match = re.findall("[a-zA-Z]{9} +[0-9]", i)         # To get STATE
        if state_match: 
            structed_data["State"].append(i[:9])
        elif re.findall("^[0-9].+, ([a-zA-Z]+);", i):
            structed_data["State"].append(i.split()[-1])
        if len(structed_data["State"]) == 2:
            structed_data["State"].pop(0)

    
        if len(i) >= 6 and i.isdigit():         # To get PINCODE
            structed_data["Pin_code"].append(i)
        elif re.findall("[a-zA-Z]{9} +[0-9]", i):
            structed_data["Pin_code"].append(i[10:])

    structed_data["City"].append(city)  # Append the city value to the 'city' array
    df=pd.DataFrame(structed_data)

    # Display the structured data
    st.write(df)



    class businesscard:
        def __init__(self):
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database='businesscard'
            )
            self.mycursor = self.mydb.cursor(buffered=True)

        def create_table(self):
            query = """
            CREATE TABLE IF NOT EXISTS Cards (
                Company_name VARCHAR(50),
                Card_holder VARCHAR(50),
                Designation VARCHAR(50),
                Mobile_number VARCHAR(15),
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
            query = """
            INSERT INTO Cards (Company_name, Card_holder, Designation, Mobile_number, Email, Website, Area, City, State, Pin_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for _, row in df.iterrows():
                values = tuple(row.values)
                self.mycursor.execute(query, values)
            self.mydb.commit()
            print('Data inserted successfully')

        def retrive_data(self,card_holder):
            query = "SELECT * FROM Cards where card_holder = %s"
            self.mycursor.execute(query,(card_holder,))
            return self.mycursor.fetchall()

        def modify_data(self, card_holder, field_to_update, new_value):
            query = f"UPDATE Cards SET {field_to_update} = %s WHERE Card_holder = %s"
            self.mycursor.execute(query, (new_value, card_holder))
            self.mydb.commit()


        def delete_data(self, card_holder):
            
            query = "DELETE FROM Cards WHERE Card_holder = %s"
            self.mycursor.execute(query, (card_holder,))
            self.mydb.commit()
        def all_recoreds(self):
            query = "SELECT * FROM Cards"
            self.mycursor.execute(query)
            return self.mycursor.fetchall()
    
    manager=businesscard()
        

    with st.sidebar:
        st.header("Navigation")
        option = st.selectbox("Choose an option", ["Insert Data", "Retrieve Data", "Modify Data", "Delete Data",'show all recordes'])
        
    
        
        
   # Automatically show all records after insertion
    if option=='show all recordes':
        st.header("All Records")
        if st.button("Show All Records"):
            records = manager.all_recoreds()
            try:# Fetch all records
                if records:
                    st.write(pd.DataFrame(records))
                else:
                    st.info("No records found in the database.")
            except Exception as e:
                st.error("An error occurred while fetching records.")
            

    if option == "Insert Data":
        st.header("Insert Data")
        if st.button("Insert Data"):
            try:
                manager.insert_data(df)
                st.success("Data inserted successfully")
            except Exception as e:
                st.error(f"Error: {e}")
    
    elif option == "Retrieve Data":
        st.header("Retrieve Data")
        card_holder=st.text_input("Enter Card Holder Name")
        if st.button("Retrieve Data"):
            try:
                data = manager.retrive_data(card_holder)
                st.write(data)
            except Exception as e:
                st.error(f"Error: {e}")

    elif option == "Modify Data":
        st.header("Modify Data")
        card_holder=st.text_input("Enter Card Holder Name")
        field_to_update = st.selectbox("Field to Update", [
        "Company_name", "Card_holder", "Designation", "Mobile_number",
        "Email", "Website", "Area", "City", "State", "Pin_code"])
        new_value = st.text_input("Enter new value")
        if st.button("Modify Data"):
            try:
                manager.modify_data(card_holder, field_to_update, new_value)
                st.success("Data modified successfully")
            except Exception as e:
                st.error(f"Error: {e}")

    elif option == "Delete Data":
        st.header("Delete Data")
        card_holder=st.text_input("Enter Card Holder Name")
        if st.button("Delete Data"):
            try:
                manager.delete_data(card_holder)
                st.success("Data deleted successfully")
            except Exception as e:
                st.error(f"Error: {e}")
            
        

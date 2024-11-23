Business Card Information Extractor Application 📇

This project is a Streamlit-based application that utilizes easyOCR to extract relevant information from an uploaded business card image and organizes it in a user-friendly interface. The application allows users to save the extracted information and the uploaded image into a database for easy retrieval and management.

🚀 Features
Business Card OCR: Extracts information from uploaded business card images using easyOCR.
Extracted fields include:
Company Name
Card Holder Name
Designation
Mobile Number
Email Address
Website URL
Area, City, State, and Pin Code
Database Integration:
Save extracted data along with the business card image into a database.
View and manage multiple entries efficiently.
Intuitive GUI:
Simple, guided process for uploading images and viewing results.
Clean and organized display of extracted information.
Scalable Design:
Supports multiple business card entries.
Extensible architecture for future enhancements



🛠️ Technologies Used
  *  Streamlit: For creating the web application.
  *  easyOCR: For Optical Character Recognition (OCR).
  *  mySQL: For storing extracted data and business card images.
  *  Pillow: For image handling and processing.
  *  Pandas: For organizing and displaying tabular data.


🎮 Usage
Upload Business Card:
1 Drag and drop or select an image file of a business card in the app.
2 Extract Information:
3 Click the "Extract" button to analyze the card and view the extracted details.
4 Save Data:
5 Save the extracted information and image into the database with a single click.
6 View Database:
7 View all saved entries in a tabular format with options to edit or delete entrie

📊 Example Workflows
Extracting Data
Upload a business card image (JPEG/PNG).
The app extracts details like name, email, phone, etc., using easyOCR.
Review the extracted details in the app.

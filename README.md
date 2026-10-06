# Smart Expiry Scanner

Smart Expiry Scanner is a Streamlit-based inventory management application that helps users track products, expiry dates, batches, quantities, and storage locations.

The system allows users to scan product barcodes, search product information online, register products manually, import products from Excel/CSV files, and monitor expiry status through a dashboard.

## Features

- User Login and Sign Up
- Product Barcode Scanning
- Product Image Upload
- Local Barcode Database
- Open Food Facts Online Product Search
- Manual Product Registration
- Automatic Expiry Status Calculation
- Inventory Dashboard
- Search and Filter Products
- Safe, Attention, Urgent and Expired Status
- Individual Product Deletion
- Delete All Products
- CSV/Excel Product Import
- Product Image Storage
- SQLite Database

## Expiry Status

The application automatically categorizes products based on their expiry date:

| Status | Condition |
|--------|-----------|
| Safe | More than 7 days remaining |
| Attention | 4–7 days remaining |
| Urgent | 0–3 days remaining |
| Expired | Expiry date has passed |
| Unknown | Invalid or missing expiry date |

## Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- NumPy
- OpenCV
- ZXing-C++
- Requests
- OpenPyXL
- Open Food Facts API

## Project Structure

```text
Smart Expiry Scanner/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── product_images/
│
└── expiry_scanner.db
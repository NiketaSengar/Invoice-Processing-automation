import re
from pdf2image import convert_from_bytes
from docquery import document, pipeline
import mysql.connector
import streamlit as st
import os
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium import webdriver
os.environ['STREAMLIT_WATCHDOG_MODE'] = 'none'

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='admin1234',
    database='invoice'
)
mycursor = mydb.cursor()

p = pipeline('document-question-answering',
             model="impira/layoutlm-invoices")

st.title('Upload Invoice pdf')
file = st.file_uploader('Choose pdf from your system', type=["pdf"])
questions = {
        "Row_id": "what is the invoice number?",
        "Order_date": "What is the order date mentioned the invoice?",
        "Ship_Mode": "what is the shipping mode?",
        "Balance_Due": "How much balance is due?",
        "Bill_To": "who is the bill issued?",
        "Item_Name": "what is the item name? ",
        "Quantity": "how much is the quantity",
        "Rate": "what is the Rate?(only float numerical value)",
        "Subtotal": "what is the subtotal amount in the invoice?",
        "Discount": "what is the discount? ",
        "Shipping_fee": "what is the shipping fee?",
        "Total_Amount": "what is the total amount?",
        "Order_ID": "what is the order ID?"
    }

if file is not None:
        st.write("Extracting invoice fields... ◌")
        images = convert_from_bytes(
            file.read(), poppler_path=r"C:/poppler/poppler-24.08.0/Library/bin")
        data = {}

        for field, question in questions.items():
            result = p(images[0], question)
            answer = result[0]['answer']
            clean = re.sub(r'[^\w\s\.\-:]', '', answer)  # simple clean
            data[field] = clean.strip()

            st.json(data)

        sql = '''
           INSERT INTO details(
           Row_id, Order_date, Ship_Mode, Bill_To,
           Balance_Due, Item_Name, Quantity, Rate,
           Subtotal, Discount, Shipping_fee, Total_Amount, Order_ID
           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           '''

        val = (
        data.get("Row_id"), datetime.strptime(data.get("Order_date"),"%b %d %Y").date(), 
        data.get("Ship_Mode"), data.get("Bill_To"),
        data.get("Balance_Due"),data.get("Item_Name"),
        int(data.get("Quantity", 0)), float(data.get("Rate", 0.0)),
        float(data.get("Subtotal", 0.0)),float(data.get("Discount", 0.0)),
        float(data.get("Shipping_fee", 0.0)),float(data.get("Total_Amount", 0.0)),
        data.get("Order_ID")
    )

        mycursor.execute(sql, val)
        mydb.commit()
        st.success(f"{mycursor.rowcount} record inserted successfully.")
else:
        st.warning("Upload the file first!")


query='SELECT * FROM details ORDER BY id DESC LIMIT 1'
mycursor.execute(query)
latest=mycursor.fetchone()
if latest:
    # Adjust index values based on column order in your table
    (
        id,Row_id, Order_date, Ship_Mode, Bill_To,
        Balance_Due, Item_Name, Quantity, Rate,
        Subtotal, Discount, Shipping_fee, Total_Amount, Order_ID
    ) = latest
    # selenium setup
    options = Options()
    options.add_experimental_option("detach", True)  # Keep browser open
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
   
    # form path location
    path='http://127.0.0.1:5500/index.html'
    driver.get(path)

    driver.find_element(By.NAME, "row_id").send_keys(str(Row_id))
    driver.find_element(By.NAME, "order_date").send_keys(str(Order_date))
    driver.find_element(By.NAME, "ship_mode").send_keys(str(Ship_Mode))
    driver.find_element(By.NAME, "bill_to").send_keys(str(Bill_To))
    driver.find_element(By.NAME, "balance_due").send_keys(str(Balance_Due))
    driver.find_element(By.NAME, "item_name").send_keys(str(Item_Name))
    driver.find_element(By.NAME, "quantity").send_keys(str(Quantity))
    driver.find_element(By.NAME, "rate").send_keys(str(Rate))
    driver.find_element(By.NAME, "subtotal").send_keys(str(Subtotal))
    driver.find_element(By.NAME, "discount").send_keys(str(Discount))
    driver.find_element(By.NAME, "shipping_fee").send_keys(str(Shipping_fee))
    driver.find_element(By.NAME, "total_amount").send_keys(str(Total_Amount))
    driver.find_element(By.NAME, "order_id").send_keys(str(Order_ID))

    st.success("Form auto-filled successfully in browser!")
else:
    st.error("No data found to autofill the form.")
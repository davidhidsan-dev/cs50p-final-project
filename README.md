# Bank Transactions & Patient Payment Analyzer

#### Video Demo: https://youtu.be/OyZnz8gsmys  

## Overview

This project is a Python application designed to automate the storage and analysis of bank transactions to determine whether each payment corresponds to a patient. It was developed as the final project for CS50P.

Using exported bank transaction files in `.xlsx` or `.xls` format together with a patient database, the program detects whether payments are made by existing or new clients. Its main purpose is to identify payments for psychology sessions, extract patient information, and organize the resulting data by financial quarters.

> **Important notes:**  
> This project was originally designed and implemented by the author in Spanish. For the CS50P submission, variable names, user messages, and documentation were translated into English by the author with the support of automated translation tools for consistency.  
> During development, ChatGPT was used strictly as a learning and debugging reference to clarify specific Python concepts. All program logic and final code structure were created, reviewed, and fully understood by the author.

---

## Description

This program automatically processes bank transactions in order to extract patient payments for psychology sessions. It applies several data processing techniques such as:

- Reading Excel files (`.xlsx`, `.xls`)
- Normalizing text to remove accents and formatting differences
- Extracting names from transaction descriptions
- Applying fuzzy string matching to detect approximate name matches

The system uses two main data sources:
1. A bank transaction export file.
2. A patient database file containing full names and ID numbers.

The program analyzes whether payments come directly from patients or from third parties (for example, a parent paying on behalf of a patient). When the payer name does not match directly, the script attempts to extract the patient name from the payment description using name and surname reference lists together with approximate matching techniques.

After all transactions are processed, the valid payments are grouped by financial quarters and exported into separate Excel reports.

This automation replaces a process that was previously performed entirely by hand, significantly reducing both human error and the time required for processing.

---

## How It Works

1. Bank transactions are loaded from an Excel file.
2. Only positive payments that match valid session amounts are selected.
3. The script extracts:
   - The payer name
   - The payment concept (description)
4. All extracted text is normalized to improve matching accuracy.
5. If the payer name matches an existing patient:
   - The payment is directly linked to that patient.
6. If the payer is different from the patient:
   - The program searches for a possible patient name inside the payment description using fuzzy matching.
7. If no patient is found:
   - The user is prompted to either add a new patient or skip the transaction.
8. All validated payments are stored in a results file.
9. A quarterly reporting function groups payments by 3-month periods and generates individual output files for each quarter.

---

## Features

- Automatic reading of bank transaction files.
- Text normalization and cleaning.
- Name and surname detection using reference lists.
- Fuzzy name matching for approximate identification.
- Detection of third-party payments.
- Interactive user confirmation for ambiguous cases.
- Automatic creation of a consolidated payments file.
- Automatic quarterly Excel reports generation.

---

## Project Structure
```
project/
│
├── project.py # Main program
├── patients.xlsx # Patient database (Name + ID Number)
├── names_list.csv # List of valid first names
├── surnames_list.csv # List of valid surnames
├── transactions.xlsx / .xls # Bank transaction export
├── README.md # Project documentation
├── requirements.txt # External dependencies
├── JAN-FEB-MAR.xlsx # 1 quarter 
├── APR-MAY-JUN.xlsx # 2 quarter 
├── JUL-AUG-SEP.xlsx # 3 quarter 
└── test_project.py
```

### Quarterly Example Files

The first three quarterly Excel files (JAN-FEB-MAR.xlsx, APR-MAY-JUN.xlsx and JUL-AUG-SEP.xlsx) are included in this repository only as example output files to demonstrate the continuous numbering logic of the program when generating the fourth quarter report.

---

## Technologies Used

- Python 3
- pandas
- rapidfuzz
- re
- unicodedata

- os


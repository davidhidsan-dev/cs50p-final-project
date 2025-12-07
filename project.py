import pandas as pd
import re
import unicodedata
from rapidfuzz import fuzz, process
import os

#Normalize text (lowercase, remove accents...)
def normalize(text):

    text = str(text)
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    clean_text = ""

    for c in text:
        if unicodedata.category(c) != "Mn":
            clean_text += c

    clean_text = re.sub(r"[^a-zñ ]", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text

#Match a word against known names and surnames
def detect_name(word, names_set, surnames_set, threshold=85):

    match_name, score_name, _ = process.extractOne(
        word, names_set, scorer = fuzz.ratio
    )
    match_surname, score_surname, _ = process.extractOne(
        word, surnames_set, scorer = fuzz.ratio
    )

    if score_name >= threshold and score_name >= score_surname:
        return match_name
    if score_surname >= threshold and score_surname >= score_name:
        return match_surname

    return None    

#Extract payer name and the concept description (if it exists)
def extract_payer(concept):

    regex = re.compile(
        r"(?:bizum from|transfer from|instant transfer from)\s+(.+?)(?:,)?(?: without concept| concept\s+(.+))?$",
        re.IGNORECASE,
    )

    concept_normalized = normalize(concept)
    matches = regex.search(concept_normalized)
    if not matches:
        return None, None, None

    name = matches.group(1).strip()

    if matches.group(2):
        concept_name = matches.group(2).strip()  
    else:
        concept_name = None

    matches_original = regex.search(concept)
    if matches_original:
        original_name = matches_original.group(1).strip()
    else:
        original_name = name.upper()

    return original_name, name, concept_name

#Extract names from concept description
def extract_names(concept, names_set, surnames_set):

    useless_words = {
        "without", "concept", "from", "bizum", "transfer",
        "instant", "session", "psychologist", "psychology", "payment",
    }

    words = concept.split()
    detected_names = []

    for word in words:
        word = word.strip()
        word = normalize(word)
        if word in useless_words:
            continue
        
        if word in names_set or word in surnames_set:
            detected_names.append(word)
            continue

        match = detect_name(word, names_set, surnames_set)
        if match:
            detected_names.append(match)

    return detected_names

#Check if extracted names from concept appear in the payer name
def payer_and_concept_match(payer, concept_names):

    if not concept_names:
        return True, []
    
    payer_normalized = normalize(payer)
    payer_words = set(payer_normalized.split())

    matches = []

    for word in concept_names:
        found = None
        for p in payer_words:
            if word in p:
                found = word
                matches.append(word)
                break

        if not found:
            return False, matches

    return True, matches

#Search for a similar patient in the database. Ask user if not found
def search_approx_patient(name, df_patients, name_col="Full Name"):

    name_norm = normalize(name)

    similarities = []
    for idx, row in df_patients.iterrows():
        patient_name = row[name_col]
        patient_name_norm = normalize(patient_name)

        score = fuzz.ratio(name_norm, patient_name_norm)
        if score >= 50:
            similarities.append((idx, patient_name, score))

    if not similarities:
        print("No patient found.")
        print("N) New patient.")
        print("S) Skip this transaction.")

        while True:
            choice = input("Choose an option (N/S): ").upper()

            if choice == "S":
                print("Transaction skipped")
                return None, None

            elif choice == "N":

                new_name = input("Enter full name of new patient: ").upper()
                new_dni = input("Enter ID Number of new patient: ").upper()

                df_patients.loc[len(df_patients)] = [new_name, new_dni]
                df_patients.to_excel("patients.xlsx", index=False)

                print(f"Patient added: {new_name}")
                return new_name, new_dni
            
            elif choice not in ("S", "N"):
                print("Invalid selection.")
                continue

    similarities.sort(key=lambda x: x[2], reverse=True)

    print("\nSimilar patients found:\n")
    for i, (real_idx, patient_name, score) in enumerate(similarities[:5]):  
        print(f"{i}) {patient_name}   —   {score}%")

    print("N) Add new patient.")
    print("S) Skip this transaction.")

    while True:
        choice = input("Select the correct patient number: ").upper()

        if choice == "S":
            print("Transaction skipped")
            return None, None

        elif choice == "N":
            new_name = input("Enter full name of new patient: ").upper()
            new_dni = input("Enter ID Number of new patient: ").upper()

            df_patients.loc[len(df_patients)] = [new_name, new_dni]
            df_patients.to_excel("patients.xlsx", index=False)

            print(f"Patient added: {new_name} with ID Number {new_dni}")
            return new_name, new_dni

        elif not choice.isdigit():
            print("Invalid input.")
            continue

        choice = int(choice)

        if 0 <= choice < len(similarities[:5]):
            real_idx = similarities[choice][0]
            selected_name = df_patients.loc[real_idx, "Full Name"]
            selected_dni = df_patients.loc[real_idx, "ID Number"]
            print(f"Patient selected: {selected_name}")
            return selected_name, selected_dni

        print("Invalid option, try again.")

#Generate a quarterly file that compiles information on payments made by customers
def quarterly():

    quarters = {
        1: {"months": [1, 2, 3], "filename": "JAN-FEB-MAR.xlsx"},
        2: {"months": [4, 5, 6], "filename": "APR-MAY-JUN.xlsx"},
        3: {"months": [7, 8, 9], "filename": "JUL-AUG-SEP.xlsx"},
        4: {"months": [10, 11, 12], "filename": "OCT-NOV-DEC.xlsx"},
    }

    while True:
        try:
            year = int(input("Enter the year of the quarter: "))
            if year < 0:
                print("Invalid year.")
            else:
                break
        except ValueError:
            print("Invalid year.")

    while True:
        try:
            quarter = int(input("Enter the quarter (1–4): "))
            if quarter < 1 or quarter > 4:
                print("Invalid quarter.")
            else:
                break
        except ValueError:
            print("Invalid quarter.")

    months = quarters[quarter]["months"]
    excel_filename = quarters[quarter]["filename"]

    df = pd.read_excel("transaction_results.xlsx")

    df["Transaction date"] = pd.to_datetime(df["Transaction date"], dayfirst=True)

    df_quarter = df[
        (df["Transaction date"].dt.year == year)
        & (df["Transaction date"].dt.month.isin(months))
    ].copy()

    if df_quarter.empty:
        print("No payments in this quarter.")
        exit()

    start_number = 1

    previous_quarters = []
    for q in range(1, quarter):
        if q in quarters:
            previous_quarters.append(q)

    for q in previous_quarters:
        prev_quarter_file = quarters[q]["filename"]

        if os.path.exists(prev_quarter_file):
            df_prev = pd.read_excel(prev_quarter_file)

            if not df_prev.empty:
                last_number = df_prev["Number"].max()
                start_number = last_number + 1

    df_quarter = df_quarter.sort_values("Transaction date")

    df_final = pd.DataFrame({
        "Number": range(start_number, start_number + len(df_quarter)),
        "Full Name": df_quarter["Full Name"],
        "ID Number": df_quarter["ID Number"],
        "Payment (€)": df_quarter["Amount"],
        "Date": df_quarter["Transaction date"].dt.strftime("%d/%m/%Y"),
        "Sessions": df_quarter["Sessions"]
    })

    if os.path.exists(excel_filename):
        print(f"Overwritting existing file: {excel_filename}")

    df_final.to_excel(excel_filename, index=False)

    print(f"File generated: {excel_filename}")


def main():

    df_names = pd.read_csv("names_list.csv")
    names_set = set()

    for name in df_names[df_names.columns[0]]:
        name_normalized = normalize(name)
        names_set.add(name_normalized)

    df_surnames = pd.read_csv("surnames_list.csv")
    surnames_set = set()

    for surname in df_surnames[df_surnames.columns[0]]:
        surname_normalized = normalize(surname)
        surnames_set.add(surname_normalized)

    df_patients = pd.read_excel("patients.xlsx")

    df_movements = pd.read_excel("transactions.xls", skiprows=7)
    df_movements = df_movements[
        (df_movements["AMOUNT (EUR)"] > 0) & (df_movements["AMOUNT (EUR)"] % 50 == 0)
    ]

    records = []

    for idx, row in df_movements.iterrows():
        concept = str(row["CONCEPT"])
        amount = row["AMOUNT (EUR)"]
        operation_date = row["TRANSACTION DATE"]

        bank_name, payer, payer_concept = extract_payer(concept)
        if payer_concept:
            concept_names = extract_names(payer_concept, names_set, surnames_set)
        else:
            concept_names = []

        same_client, _ = payer_and_concept_match(payer, concept_names)

        final_patient = None

        if same_client and bank_name:
            normalized_name = normalize(bank_name)
            match_list = df_patients[
                df_patients["Full Name"].apply(normalize) == normalized_name
            ]

            if not match_list.empty:
                final_patient = match_list.iloc[0]["Full Name"]
                final_dni = match_list.iloc[0]["ID Number"]
                print(f"Patient found: {final_patient} (ID Number: {final_dni})")

            else:
                print(f"Add new patient: {bank_name}")
                dni = input(f"Enter ID Number for {bank_name}: ").upper()
                final_dni = dni

                new_name = bank_name

                df_patients.loc[len(df_patients)] = [new_name, dni]
                df_patients.to_excel("patients.xlsx", index=False)

                print(f"Patient added: {new_name} (ID Number: {dni})")
                final_patient = new_name

        else:
            if concept_names:
                suspected_name = " ".join(concept_names)
            else:
                suspected_name = bank_name

            print(f"Unclear match. Searching similar patient for: {suspected_name}, {concept}")
            final_patient, final_dni = search_approx_patient(suspected_name, df_patients)

            if final_patient == None:
                continue
        
        records.append({
            "Full Name": final_patient,
            "ID Number": final_dni,
            "Amount": amount,
            "Transaction date": operation_date,
            "Sessions": int(amount / 50)
        })

    df_results = pd.DataFrame(records)

    df_results.to_excel("transaction_results.xlsx", index=False)

    print("'transaction_results.xlsx' generated!")

    quarterly()

if __name__ == "__main__":
    main()

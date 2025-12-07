from project import normalize
from project import payer_and_concept_match
from project import fuzzy_name
from project import extract_payer
from project import extract_names
from project import search_approx_patient
import pandas as pd

def test_normalize():
    assert normalize("María") == "maria"
    assert normalize("Ana??") == "ana"
    assert normalize("     María    José") == "maria jose"
    assert normalize("4manolo.") == "manolo"
    
def test_payer_and_concept_match():
    ok, palabras = payer_and_concept_match("María Lopez", ["maria", "lopez"])
    assert ok == True
    assert set(palabras) == {"maria", "lopez"}
    
    ok, palabras = payer_and_concept_match("María Lopez", ["maria", "garcia"])
    assert ok == False
    assert set(palabras) == {"maria"}

    ok, palabras = payer_and_concept_match("María Lopez García", ["maria", "garcia"])
    assert ok == True
    assert set(palabras) == {"maria", "garcia"}

    ok, palabras = payer_and_concept_match("María Lopez", [])
    assert ok == True
    assert palabras == []

def test_fuzzy_name():
    nombres_set = {"maria", "jose", "ana"}
    apellidos_set = {"gomez", "ruiz"}
    assert fuzzy_name("mari", nombres_set, apellidos_set) == "maria"
    assert fuzzy_name("gmez", nombres_set, apellidos_set) == "gomez"
    assert fuzzy_name("qwfs", nombres_set, apellidos_set) == None

def test_extract_payer():
    original, normalizado, concepto = extract_payer("Transfer from Pedro Gómez, Concept Session")
    assert original == "Pedro Gómez"
    assert normalizado == "pedro gomez"
    assert concepto == "session"

    original, normalizado, concepto = extract_payer("Transfer from Pedro Gómez")
    assert original == "Pedro Gómez"
    assert normalizado == "pedro gomez"
    assert concepto == None

    original, normalizado, concepto = extract_payer("Instant transfer from Pedro Gómez without concept")
    assert original == "Pedro Gómez"
    assert normalizado == "pedro gomez"
    assert concepto == None

def test_extract_names():
    nombres_set = {"maria", "ana"}
    apellidos_set = {"gomez", "ruiz"}
    assert set(extract_names("session María Gómez psychology session", nombres_set, apellidos_set)) == {"maria", "gomez"}
    assert set(extract_names("ana ruiz session 12", nombres_set, apellidos_set)) == {"ana", "ruiz"}
    assert extract_names("Without concept", nombres_set, apellidos_set) == []


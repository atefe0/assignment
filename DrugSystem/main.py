import gradio as gr
import pandas as pd
import os
import requests
import re
import spacy
from transformers import pipeline
import json
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt')

patient_columns = ["ID", "Name", "Age", "Gender", "Weight", "Height",
                   "Disease", "Conditions", "Allergies", "Current_Medications"]

excel_file = "patients.xlsx"

def load_patients():
    if os.path.exists(excel_file):
        return pd.read_excel(excel_file)
    else:
        return pd.DataFrame(columns=patient_columns)

def save_patients(df):
    df.to_excel(excel_file, index=False)

def add_patient(name, age, gender, weight, height, disease, conditions, allergies, current_medications):
    df = load_patients()
    if df.empty:
        new_id = 1
    else:
        new_id = df['ID'].max() + 1

    new_patient = {
        "ID": new_id,
        "Name": name,
        "Age": age,
        "Gender": gender,
        "Weight": weight,
        "Height": height,
        "Disease": disease,
        "Conditions": conditions,
        "Allergies": allergies,
        "Current_Medications": current_medications
    }
    df = pd.concat([df, pd.DataFrame([new_patient])], ignore_index=True)
    save_patients(df)
    return f"Patient added with ID {new_id}"

def find_patient_by_id(patient_id):
    df = load_patients()
    patient = df[df['ID'] == patient_id]
    if patient.empty:
        return "Patient not found", pd.DataFrame()
    return f"Patient ID {patient_id}", patient

def show_all_patients():
    df = load_patients()
    return df

def clean_text(text):
    text = re.sub(r'\(see[^\)]*\)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def summarize_text(text, max_sentences=6):
    if isinstance(text, list):
        text = " ".join(text)
    text = clean_text(text)
    sentences = sent_tokenize(text)
    return ' '.join(sentences[:max_sentences])

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
def summarize_short(text, max_tokens=500):
    short_summary = summarizer(text, max_length=max_tokens, min_length=3, do_sample=False)[0]['summary_text']
    return short_summary

with open("API.json") as f:
    file = json.load(f)

OPENFDA_URL = file["OPENFDA_URL"]

def analyze_patient(patient_id, option, limit_search):
    df = load_patients()
    nlp = spacy.load("en_ner_bc5cdr_md")
    patient = df[df['ID'] == patient_id]
    if patient.empty:
        return "Patient not found"
    
    patient_info = patient.iloc[0]
    disease = patient.iloc[0]['Disease']
    response = requests.get(OPENFDA_URL, params={"search": f"indications_and_usage:{disease}", "limit":limit_search})
    if response.status_code != 200:
        return "Failed to fetch data from OpenFDA. Check your connection."

    results = response.json().get('results', [])
    output_list = []

    for item in results:
        indications_list = item.get("indications_and_usage", [])
        indications_str = " ".join(indications_list) if isinstance(indications_list, list) else str(indications_list)
        doc = nlp(indications_str)
        openfda = item.get("openfda", {})
        brand_name = None

        if "brand_name" in openfda:
            if isinstance(openfda["brand_name"], list):
                brand_name = openfda["brand_name"][0]
            elif isinstance(openfda["brand_name"], str):
                brand_name = openfda["brand_name"]
        else:
            for ent in doc.ents:
                if ent.label_ == "CHEMICAL":
                    brand_name = ent.text
                    break
            else:
                brand_name = "unknown drug name"
        if use_bart == False:
            if option == "Drug interactions":
                interactions = item.get("drug_interactions", "")
                if interactions:
                    output_list.append(f"{brand_name} : {summarize_text(interactions, 9)}")
            
            elif option == "Patient's conditions (pregnancy, allergies, ...)":
                cond_text1 = str(item.get("pregnancy", "")).strip() if "pregnancy" in item else ""
                output_list.append(f"{brand_name} pregnancy : {summarize_text(cond_text1, 10)}")
                cond_text2 = str(item.get("nursing_mothers", "")).strip() if "nursing_mothers" in item else ""
                output_list.append(f"{brand_name} nursing_mothers : {cond_text2}")
                cond_text3 = str(item.get("use_in_specific_populations", "")).strip() if "use_in_specific_populations" in item else ""
                output_list.append(f"{brand_name} use_in_specific_populations : {summarize_text(cond_text3, 11)}")

            elif option == "Warnings":
                data1 = summarize_text(str(item.get("boxed_warning")).strip() if "boxed_warning" in item else "", 5)
                data2 = summarize_text(str(item.get("precautions")).strip() if "precautions"  in item else "", 10)
                data3 = summarize_text(str(item.get("warnings")).strip() if "warnings"  in item else "", 13)
                data4 = summarize_text(str(item.get("warnings_and_cautions")).strip() if "warnings_and_cautions"  in item else "", 10)
                warn_text = data1 + data2 + data3 + data4
                if warn_text.strip():
                    output_list.append(f"{brand_name} : {warn_text}")

            elif option == "Dosage forms":
                dosage_text = item.get("dosage_forms_and_strengths", "")
                if dosage_text:
                    output_list.append(f"{brand_name} : {str(dosage_text)}")

            elif option == "Dosage administration":
                dosage_and_administration = item.get("dosage_and_administration", "")
                if dosage_and_administration:
                    output_list.append(f"{brand_name} : {str(dosage_and_administration)}")

            elif option == "Adverse reactions":
                adv_text = item.get("adverse_reactions", "")
                if adv_text:
                    output_list.append(f"{brand_name} : {summarize_text(adv_text, 15)}")

            elif option == "Clinical studies":
                study_text = item.get("clinical_studies", "")
                if study_text:
                    output_list.append(f"{brand_name} : {summarize_text(study_text, 15)}")

            elif option == "Drug name":
                output_list.append(f"{brand_name}")
            
            elif option == "Contraindications":
                contraind_text = item.get("contraindications", "")
                if contraind_text:
                    output_list.append(f"{brand_name} : {str(contraind_text)}")

            elif option == "Drug RxCUI":
                if "rxcui" in openfda:
                    rxcui = openfda["rxcui"]
                if rxcui:
                    output_list.append(f"{brand_name} : {rxcui}")

            elif option == "Carcinogenesis and impairment of fertility":
                carcinogenesis = item.get("carcinogenesis_and_mutagenesis_and_impairment_of_fertility", "")
                if carcinogenesis:
                    output_list.append(f"{brand_name} : {str(carcinogenesis)}")

            elif option == "Drug route":
                if "route" in openfda:
                    route = openfda["route"]
                if route:
                    output_list.append(f"{brand_name} : {route}")

            elif option == "Overdosage":
                overdosage = item.get("overdosage", "")
                if overdosage:
                    output_list.append(f"{brand_name} : {summarize_text(overdosage, 8)}")

            elif option == "Teratogenic effects":
                teratogenic = item.get("teratogenic_effects", "")
                if teratogenic:
                    output_list.append(f"{brand_name} : {summarize_text(teratogenic, 3)}")

            elif option == "Mechanism of action":
                mechanism = item.get("mechanism_of_action", "")
                if mechanism:
                    output_list.append(f"{brand_name} : {summarize_text(mechanism, 9)}")

            elif option == "Nonclinical toxicology":
                toxicology = item.get("nonclinical_toxicology", "")
                if toxicology:
                    output_list.append(f"{brand_name} : {summarize_text(toxicology, 5)}")

            elif option == "Description":
                description = item.get("description", "")
                if description:
                    output_list.append(f"{brand_name} : {summarize_text(description, 6)}")

            elif option == "Pharmacokinetics":
                pharmacokinetics = item.get("pharmacokinetics", "")
                if pharmacokinetics :
                    output_list.append(f"{brand_name} : {summarize_text(pharmacokinetics, 9)}")

            elif option == "Geriatric use":
                geriatric = item.get("geriatric_use", "")
                if geriatric :
                    output_list.append(f"{brand_name} : {summarize_text(geriatric, 4)}")

            elif option == "Risks":
                risks = item.get("risks", "")
                if risks :
                    output_list.append(f"{brand_name} : {summarize_text(risks, 5)}")

            elif option =="Clinical pharmacology" :
                clinical_pharmacology = item.get("clinical_pharmacology", "")
                if clinical_pharmacology:
                    output_list.append(f"{brand_name} : {summarize_text(clinical_pharmacology, 20)}")

            elif option == "Pharmacodynamics":
                pharmacodynamics = item.get("pharmacodynamics", "")
                if  pharmacodynamics:
                    output_list.append(f"{brand_name} : {summarize_text(pharmacodynamics, 15)}")

        
        else:
            if option == "Drug interactions":
                interactions = item.get("drug_interactions", "")
                if interactions:
                    sumarry = summarize_text(interactions, 8)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 200)}")

            elif option == "Patient's conditions (pregnancy, allergies, ...)":
                cond_text1 = str(item.get("pregnancy", "")).strip() if "pregnancy" in item else ""
                output_list.append(f"{brand_name} pregnancy : {summarize_short(summarize_text(cond_text1, 5), 200)}")
                cond_text2 = str(item.get("nursing_mothers", "")).strip() if "nursing_mothers" in item else ""
                output_list.append(f"{brand_name} nursing_mothers : {summarize_short(summarize_text(cond_text2, 4), 150)}")
                cond_text3 = str(item.get("use_in_specific_populations", "")).strip() if "use_in_specific_populations" in item else ""
                output_list.append(f"{brand_name} use_in_specific_populations : {summarize_short(summarize_text(cond_text3, 10), 300)}")

            elif option == "Warnings":
                data1 = summarize_short(summarize_text(str(item.get("boxed_warning")).strip() if "boxed_warning" in item else "", "", 5), "", 100)
                data2 = summarize_short(summarize_text(str(item.get("precautions")).strip() if "precautions"  in item else "", "", 10), "", 300)
                data3 = summarize_short(summarize_text(str(item.get("warnings")).strip() if "warnings"  in item else "", ""), "")
                data4 = summarize_short(summarize_text(str(item.get("warnings_and_cautions")).strip() if "warnings_and_cautions"  in item else "", "", 10), "", 200)
                warn_text = data1 + data2 + data3 + data4
                if warn_text.strip():
                    output_list.append(f"{brand_name} : {warn_text}")

            elif option == "Dosage forms":
                dosage_text = item.get("dosage_forms_and_strengths", "")
                if dosage_text:
                    sumarry = dosage_text
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 50)}")

            elif option == "Dosage administration":
                dosage_and_administration = item.get("dosage_and_administration", "")
                if dosage_and_administration:
                    sumarry = dosage_and_administration
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 200)}")

            elif option == "Adverse reactions":
                adv_text = item.get("adverse_reactions", "")
                if adv_text:
                    sumarry = summarize_text(adv_text, 15)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 400)}")

            elif option == "Clinical studies":
                study_text = item.get("clinical_studies", "")
                if study_text:
                    sumarry = summarize_text(study_text, 15)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 500)}")
                    
            elif option == "Drug name":
                output_list.append(f"{brand_name}")
            
            elif option == "Contraindications":
                contraind_text = item.get("contraindications", "")
                if contraind_text:
                    sumarry = contraind_text
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 150)}")

            elif option == "Drug RxCUI":
                if "rxcui" in openfda:
                    rxcui = openfda["rxcui"]
                if rxcui:
                    output_list.append(f"{brand_name} : {rxcui}")

            elif option == "carcinogenesis impairment of fertility":
                carcinogenesis = item.get("carcinogenesis_and_mutagenesis_and_impairment_of_fertility", "")
                if carcinogenesis:
                    sumarry = carcinogenesis
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 150)}")

            elif option == "Drug route":
                if "route" in openfda:
                    route = openfda["route"]
                if route:
                    output_list.append(f"{brand_name} : {route}")

            elif option == "Overdosage":
                overdosage = item.get("overdosage", "")
                if overdosage:
                    sumarry = summarize_text(overdosage, 8)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 200)}")

            elif option == "Teratogenic effects":
                teratogenic = item.get("teratogenic_effects", "")
                if teratogenic:
                    sumarry = summarize_text(teratogenic, 6)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 200)}")


            elif option == "Mechanism of action":
                mechanism = item.get("mechanism_of_action", "")
                if mechanism:
                    sumarry = summarize_text(mechanism, 9)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 250)}")

            elif option == "Nonclinical toxicology":
                toxicology = item.get("nonclinical_toxicology", "")
                if toxicology:
                    sumarry = summarize_text(toxicology, 5)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 150)}")

            elif option == "Description":
                description = item.get("description", "")
                if description:
                    sumarry = summarize_text(description, 6)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 150)}")

            elif option == "Pharmacokinetics":
                pharmacokinetics = item.get("pharmacokinetics", "")
                if pharmacokinetics :
                    sumarry = summarize_text(pharmacokinetics)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry)}")

            elif option == "Pharmacokinetics":
                pharmacokinetics = item.get("pharmacodynamics", "")
                if pharmacokinetics :
                    sumarry = summarize_text(pharmacokinetics, 8)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 250)}")


            elif option == "Geriatric use":
                geriatric = item.get("geriatric_use", "")
                if geriatric :
                    sumarry = summarize_text(geriatric, 4)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 100)}")

            elif option == "Risks":
                risks = item.get("risks", "")
                if risks :
                    sumarry = summarize_text(risks, 6)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 200)}")

            elif option =="Clinical pharmacology" :
                clinical_pharmacology = item.get("clinical_pharmacology", "")
                if clinical_pharmacology:
                    sumarry = summarize_text(clinical_pharmacology, 15)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 250)}")

            elif option == "Pharmacodynamics":
                pharmacodynamics = item.get("pharmacodynamics", "")
                if pharmacodynamics:
                    sumarry = summarize_text(pharmacodynamics, 15)
                    output_list.append(f"{brand_name} : {summarize_short(sumarry, 400)}")

            



    return "\n\n".join(output_list) if output_list else "No information found for selected option"


with gr.Blocks() as demo:
    gr.Markdown("# Smart Drug Recommendation System")
    with gr.Tab("Add New Patient"):
        name = gr.Textbox(label="Name")
        age = gr.Number(label="Age")
        gender = gr.Dropdown(["Male", "Female"], label="Gender")
        weight = gr.Number(label="Weight")
        height = gr.Number(label="Height")
        disease = gr.Textbox(label="Disease")
        conditions = gr.Textbox(label="Conditions")
        allergies = gr.Textbox(label="Allergies")
        current_medications = gr.Textbox(label="Current Medications")
        add_button = gr.Button("Add Patient")
        add_output = gr.Textbox(label="Status")
        add_button.click(add_patient, 
                         inputs=[name, age, gender, weight, height, disease, conditions, allergies, current_medications],
                         outputs=add_output)

    with gr.Tab("Find Patient by ID"):
        patient_id_input = gr.Number(label="Patient ID")
        find_button = gr.Button("Find Patient")
        find_output = gr.Textbox(label="Patient Info")
        all_patients_button = gr.Button("Show All Patients")
        all_patients_output = gr.Dataframe(headers=patient_columns, datatype="str", label="Patient Data", row_count=(1, None), col_count=len(patient_columns), wrap=True)
        
        find_button.click(find_patient_by_id, inputs=patient_id_input, outputs=[find_output, all_patients_output])
        all_patients_button.click(show_all_patients, inputs=None, outputs=all_patients_output)

    with gr.Tab("Analyze Patient"):
        analyze_id_input = gr.Number(label="Patient ID")
        limit_search = gr.Number(label="Limit search", precision=0)
        use_bart = gr.Checkbox(value=False, label="Use DistilBART (condensed form)")
        option_select = gr.Dropdown([
            "Drug interactions",
            "Patient's conditions (pregnancy, allergies, ...)",
            "Warnings",
            "Dosage forms",
            "Dosage administration",
            "Adverse reactions",
            "Clinical studies",
            "Drug name",
            "Contraindications",
            "Geriatric use",
            "Pharmacodynamics",
            "Pharmacokinetics",
            "Description",
            "Nonclinical toxicology",
            "Mechanism of action",
            "Teratogenic effects",
            "Overdosage",
            "Drug route",
            "Drug RxCUI",
            "Carcinogenesis impairment of fertility",
            "Risks",
            "Clinical pharmacology"
        ], label="Select Option")
        analyze_button = gr.Button("Analyze")
        analyze_output = gr.Textbox(label="Analysis Result", lines=20)
        
        analyze_button.click(analyze_patient, inputs=[analyze_id_input, option_select, limit_search], outputs=analyze_output)

demo.launch(inbrowser=True, share=False)
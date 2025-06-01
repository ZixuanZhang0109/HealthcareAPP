# --- Cell ---
# app.py

import streamlit as st
import pandas as pd
from datetime import date

import db  # the file we just created

# =============================================================================
# 1. Basic Streamlit configuration
# =============================================================================
st.set_page_config(
    page_title="Healthcare Management Interface",
    layout="wide",
)

st.title("Healthcare Management Interface")

# =============================================================================
# 2. Sidebar: Choose your “role” mode
# =============================================================================
role = st.sidebar.selectbox(
    "Select your role:",
    ["Doctor", "Patient", "Admin"]
)

st.sidebar.write(
    """
    • Doctor: View/Add patients & medical records under doctor_schema.  
    • Patient: View only your own medical records under patient_schema (RLS).  
    • Admin: Manage doctors & hospitals under admin_schema.  
    """
)

# =============================================================================
# 3. Doctor Mode  
# =============================================================================
if role == "Doctor":
    st.header("👨‍⚕️ Doctor Dashboard")

    # 3.1 Show all patients (doctor_schema.patients)
    st.subheader("All Patients")
    try:
        all_patients = db.doctor_get_all_patients()
        if all_patients:
            df_patients = pd.DataFrame(all_patients)
            st.dataframe(df_patients, use_container_width=True)
        else:
            st.info("No patients found in doctor_schema.patients.")
    except Exception as e:
        st.error(f"Error loading patients: {e}")

    st.markdown("---")

    # 3.2 Form: Add a new patient
    st.subheader("Add New Patient")
    with st.form("add_patient_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            p_name = st.text_input("Name")
        with col2:
            p_age = st.number_input("Age", min_value=0, step=1, format="%d")
        with col3:
            p_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        with col4:
            p_blood = st.text_input("Blood Type (e.g. O+, A-)")

        submitted = st.form_submit_button("Add Patient")
        if submitted:
            if p_name.strip() == "" or p_blood.strip() == "":
                st.error("Name and Blood Type cannot be empty.")
            else:
                try:
                    db.doctor_insert_patient(
                        name=p_name.strip(),
                        age=int(p_age),
                        gender=p_gender,
                        blood_type=p_blood.strip()
                    )
                    st.success(f"Patient '{p_name}' added successfully.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to insert patient: {e}")

    st.markdown("---")

    # 3.3 Show all medical records (doctor_schema.medical_records)
    st.subheader("All Medical Records")
    try:
        records = db.doctor_get_all_medical_records()
        if records:
            df_records = pd.DataFrame(records)
            st.dataframe(df_records, use_container_width=True)
        else:
            st.info("No records found in doctor_schema.medical_records.")
    except Exception as e:
        st.error(f"Error loading records: {e}")

    st.markdown("---")

    # 3.4 Form: Add a new medical record
    st.subheader("Add New Medical Record")
    with st.form("add_record_form"):
        c1, c2 = st.columns(2)
        with c1:
            mr_patient_id   = st.number_input("Patient ID", min_value=1, step=1, format="%d")
            mr_doctor_id    = st.number_input("Doctor ID", min_value=1, step=1, format="%d")
            mr_hospital_id  = st.number_input("Hospital ID", min_value=1, step=1, format="%d")
            mr_provider_id  = st.number_input("Provider ID", min_value=1, step=1, format="%d")
            mr_medication_id= st.number_input("Medication ID", min_value=1, step=1, format="%d")
            mr_condition    = st.text_input("Medical Condition")
        with c2:
            mr_admission_date = st.date_input("Admission Date", value=date.today())
            mr_discharge_date = st.date_input("Discharge Date", value=date.today())
            mr_admission_type = st.selectbox(
                "Admission Type", ["Emergency", "Elective", "Routine"]
            )
            mr_room_number    = st.number_input(
                "Room Number", min_value=1, step=1, format="%d"
            )
            mr_billing_amount = st.number_input(
                "Billing Amount ($)", min_value=0.0, step=0.01, format="%.2f"
            )
            mr_length_of_stay = st.number_input(
                "Length of Stay (days)", min_value=0, step=1, format="%d"
            )

        rec_submitted = st.form_submit_button("Add Medical Record")
        if rec_submitted:
            if mr_condition.strip() == "":
                st.error("Medical Condition cannot be empty.")
            else:
                try:
                    db.doctor_insert_medical_record(
                        patient_id=int(mr_patient_id),
                        doctor_id=int(mr_doctor_id),
                        hospital_id=int(mr_hospital_id),
                        provider_id=int(mr_provider_id),
                        medication_id=int(mr_medication_id),
                        medical_condition=mr_condition.strip(),
                        date_of_admission=mr_admission_date,
                        discharge_date=mr_discharge_date,
                        admission_type=mr_admission_type,
                        room_number=int(mr_room_number),
                        billing_amount=float(mr_billing_amount),
                        length_of_stay=int(mr_length_of_stay)
                    )
                    st.success("Medical record added successfully.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to insert medical record: {e}")

# =============================================================================
# 4. Patient Mode
# =============================================================================
elif role == "Patient":
    st.header("🧑 Patient Dashboard")

    st.info(
        "Enter your Patient ID below. Row‐level security (RLS) will ensure you see only "
        "your own medical records."
    )
    pid = st.number_input("Patient ID", min_value=1, step=1, format="%d")

    if st.button("Load My Medical Records"):
        try:
            my_records = db.patient_get_own_medical_records(patient_id=int(pid))
            if my_records:
                df_my = pd.DataFrame(my_records)
                st.dataframe(df_my, use_container_width=True)
            else:
                st.warning(f"No medical records found for Patient ID {pid}.")
        except Exception as e:
            st.error(f"Error fetching your records: {e}")

# =============================================================================
# 5. Admin Mode
# =============================================================================
elif role == "Admin":
    st.header("🛠️ Admin Dashboard")

    # 5.1 Show all doctors (admin_schema.doctors)
    st.subheader("All Doctors")
    try:
        docs = db.admin_get_all_doctors()
        if docs:
            df_docs = pd.DataFrame(docs)
            st.dataframe(df_docs, use_container_width=True)
        else:
            st.info("No doctors found in admin_schema.doctors.")
    except Exception as e:
        st.error(f"Error loading doctors: {e}")

    st.markdown("---")

    # 5.2 Form: Add a new doctor
    st.subheader("Add New Doctor")
    with st.form("add_doctor_form"):
        dcol1, dcol2, dcol3 = st.columns(3)
        with dcol1:
            d_name      = st.text_input("Name")
        with dcol2:
            d_specialty = st.text_input("Specialty")
        with dcol3:
            d_phone     = st.text_input("Phone Number")

        doctor_sub = st.form_submit_button("Add Doctor")
        if doctor_sub:
            if d_name.strip() == "" or d_specialty.strip() == "":
                st.error("Name and Specialty cannot be empty.")
            else:
                try:
                    db.admin_insert_doctor(
                        name=d_name.strip(),
                        specialty=d_specialty.strip(),
                        phone_number=d_phone.strip()
                    )
                    st.success(f"Doctor '{d_name}' added.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to add doctor: {e}")

    st.markdown("---")

    # 5.3 Show all hospitals (admin_schema.hospitals)
    st.subheader("All Hospitals")
    try:
        hospitals = db.admin_get_all_hospitals()
        if hospitals:
            df_hosp = pd.DataFrame(hospitals)
            st.dataframe(df_hosp, use_container_width=True)
        else:
            st.info("No hospitals found in admin_schema.hospitals.")
    except Exception as e:
        st.error(f"Error loading hospitals: {e}")

    st.markdown("---")

    # 5.4 Form: Add new hospital
    st.subheader("Add New Hospital")
    with st.form("add_hospital_form"):
        hcol1, hcol2 = st.columns(2)
        with hcol1:
            h_name    = st.text_input("Hospital Name")
        with hcol2:
            h_address = st.text_input("Address")
        h_phone = st.text_input("Phone Number")

        hosp_sub = st.form_submit_button("Add Hospital")
        if hosp_sub:
            if h_name.strip() == "":
                st.error("Hospital Name cannot be empty.")
            else:
                try:
                    db.admin_insert_hospital(
                        name=h_name.strip(),
                        address=h_address.strip() or None,
                        phone_number=h_phone.strip() or None
                    )
                    st.success(f"Hospital '{h_name}' added.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to add hospital: {e}")

# --- Cell ---



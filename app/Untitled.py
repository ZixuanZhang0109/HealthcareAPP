# --- Cell ---
# app_combined.py

import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker

# =============================================================================
# 1. Database connection info (adjust as needed)
# =============================================================================
DB_USER     = "postgres"
DB_PASSWORD = "root"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "Healthcare"

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create the engine and session factory
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# =============================================================================
# 2. Reflect schemas into MetaData objects
# =============================================================================

# --- doctor_schema ---
doctor_meta = MetaData(schema="doctor_schema")
doctor_meta.reflect(bind=engine)
Patients_doctor        = Table("patients", doctor_meta, autoload_with=engine)
MedicalRecords_doctor  = Table("medical_records", doctor_meta, autoload_with=engine)
Medications_doctor     = Table("medications", doctor_meta, autoload_with=engine)

# --- patient_schema ---
patient_meta = MetaData(schema="patient_schema")
patient_meta.reflect(bind=engine)
Patients_patient       = Table("patients", patient_meta, autoload_with=engine)
MedicalRecords_patient = Table("medical_records", patient_meta, autoload_with=engine)

# --- admin_schema ---
admin_meta = MetaData(schema="admin_schema")
admin_meta.reflect(bind=engine)
Patients_admin           = Table("patients", admin_meta, autoload_with=engine)
Hospitals_admin          = Table("hospitals", admin_meta, autoload_with=engine)
Doctors_admin            = Table("doctors", admin_meta, autoload_with=engine)
Medications_admin        = Table("medications", admin_meta, autoload_with=engine)
InsuranceProviders_admin = Table("insurance_providers", admin_meta, autoload_with=engine)
MedicalRecords_admin     = Table("medical_records", admin_meta, autoload_with=engine)

# =============================================================================
# 3. Helper: SET ROLE + SET search_path + execute SQL
# =============================================================================

def _execute_with_role(sql_text: str, role: str, schema: str, **params):
    conn = engine.connect()
    conn.execute(text(f"SET search_path TO {schema}"))
    conn.execute(text(f"SET ROLE {role}"))
    result = conn.execute(text(sql_text), params)
    return result

# =============================================================================
# 4. Doctor‐side functions
# =============================================================================

def doctor_get_all_patients():
    sql = "SELECT * FROM patients"
    result = _execute_with_role(sql, role="doctor_user", schema="doctor_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows

def doctor_insert_patient(name: str, age: int, gender: str, blood_type: str):
    sql = """
    INSERT INTO patients (name, age, gender, blood_type)
    VALUES (:name, :age, :gender, :blood_type)
    """
    _execute_with_role(
        sql,
        role="doctor_user",
        schema="doctor_schema",
        name=name,
        age=age,
        gender=gender,
        blood_type=blood_type
    )

def doctor_get_all_medical_records():
    sql = "SELECT * FROM medical_records"
    result = _execute_with_role(sql, role="doctor_user", schema="doctor_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows

def doctor_insert_medical_record(
    patient_id: int,
    doctor_id: int,
    hospital_id: int,
    provider_id: int,
    medication_id: int,
    medical_condition: str,
    date_of_admission,
    discharge_date,
    admission_type: str,
    room_number: int,
    billing_amount: float,
    length_of_stay: int
):
    sql = """
    INSERT INTO medical_records (
        patient_id, doctor_id, hospital_id, provider_id, medication_id,
        medical_condition, date_of_admission, discharge_date,
        admission_type, room_number, billing_amount, length_of_stay
    ) VALUES (
        :patient_id, :doctor_id, :hospital_id, :provider_id, :medication_id,
        :medical_condition, :date_of_admission, :discharge_date,
        :admission_type, :room_number, :billing_amount, :length_of_stay
    )
    """
    _execute_with_role(
        sql,
        role="doctor_user",
        schema="doctor_schema",
        patient_id=patient_id,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        provider_id=provider_id,
        medication_id=medication_id,
        medical_condition=medical_condition,
        date_of_admission=date_of_admission,
        discharge_date=discharge_date,
        admission_type=admission_type,
        room_number=room_number,
        billing_amount=billing_amount,
        length_of_stay=length_of_stay
    )

# =============================================================================
# 5. Patient‐side function (with RLS)
# =============================================================================

def patient_get_own_medical_records(patient_id: int):
    conn = engine.connect()
    conn.execute(text("SET ROLE patient_user"))
    conn.execute(text("SET app.patient_id = :pid"), {"pid": patient_id})
    conn.execute(text("SET search_path TO patient_schema"))
    result = conn.execute(text("SELECT * FROM medical_records"))
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows

# =============================================================================
# 6. Admin‐side functions
# =============================================================================

def admin_get_all_doctors():
    sql = "SELECT * FROM doctors"
    result = _execute_with_role(sql, role="admin_user", schema="admin_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows

def admin_insert_doctor(name: str, specialty: str, phone_number: str):
    sql = """
    INSERT INTO doctors (name, specialty, phone_number)
    VALUES (:name, :specialty, :phone_number)
    """
    _execute_with_role(
        sql,
        role="admin_user",
        schema="admin_schema",
        name=name,
        specialty=specialty,
        phone_number=phone_number
    )

def admin_get_all_hospitals():
    sql = "SELECT * FROM hospitals"
    result = _execute_with_role(sql, role="admin_user", schema="admin_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows

def admin_insert_hospital(name: str, address: str = None, phone_number: str = None):
    sql = """
    INSERT INTO hospitals (name, address, phone_number)
    VALUES (:name, :address, :phone_number)
    """
    _execute_with_role(
        sql,
        role="admin_user",
        schema="admin_schema",
        name=name,
        address=address,
        phone_number=phone_number
    )

# =============================================================================
# 7. Streamlit UI
# =============================================================================

st.set_page_config(
    page_title="Healthcare Management Interface",
    layout="wide",
)

st.title("Healthcare Management Interface")

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

if role == "Doctor":
    st.header("👨‍⚕️ Doctor Dashboard")

    # Show all patients
    st.subheader("All Patients")
    try:
        all_patients = doctor_get_all_patients()
        if all_patients:
            df_patients = pd.DataFrame(all_patients)
            st.dataframe(df_patients, use_container_width=True)
        else:
            st.info("No patients found in doctor_schema.patients.")
    except Exception as e:
        st.error(f"Error loading patients: {e}")

    st.markdown("---")

    # Add new patient
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
                    doctor_insert_patient(
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

    # Show all medical records
    st.subheader("All Medical Records")
    try:
        records = doctor_get_all_medical_records()
        if records:
            df_records = pd.DataFrame(records)
            st.dataframe(df_records, use_container_width=True)
        else:
            st.info("No records found in doctor_schema.medical_records.")
    except Exception as e:
        st.error(f"Error loading records: {e}")

    st.markdown("---")

    # Add new medical record
    st.subheader("Add New Medical Record")
    with st.form("add_record_form"):
        c1, c2 = st.columns(2)
        with c1:
            mr_patient_id    = st.number_input("Patient ID", min_value=1, step=1, format="%d")
            mr_doctor_id     = st.number_input("Doctor ID", min_value=1, step=1, format="%d")
            mr_hospital_id   = st.number_input("Hospital ID", min_value=1, step=1, format="%d")
            mr_provider_id   = st.number_input("Provider ID", min_value=1, step=1, format="%d")
            mr_medication_id = st.number_input("Medication ID", min_value=1, step=1, format="%d")
            mr_condition     = st.text_input("Medical Condition")
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
                    doctor_insert_medical_record(
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

elif role == "Patient":
    st.header("🧑 Patient Dashboard")

    st.info(
        "Enter your Patient ID below. Row‐level security (RLS) will ensure you see only "
        "your own medical records."
    )
    pid = st.number_input("Patient ID", min_value=1, step=1, format="%d")

    if st.button("Load My Medical Records"):
        try:
            my_records = patient_get_own_medical_records(patient_id=int(pid))
            if my_records:
                df_my = pd.DataFrame(my_records)
                st.dataframe(df_my, use_container_width=True)
            else:
                st.warning(f"No medical records found for Patient ID {pid}.")
        except Exception as e:
            st.error(f"Error fetching your records: {e}")

elif role == "Admin":
    st.header("🛠️ Admin Dashboard")

    # Show all doctors
    st.subheader("All Doctors")
    try:
        docs = admin_get_all_doctors()
        if docs:
            df_docs = pd.DataFrame(docs)
            st.dataframe(df_docs, use_container_width=True)
        else:
            st.info("No doctors found in admin_schema.doctors.")
    except Exception as e:
        st.error(f"Error loading doctors: {e}")

    st.markdown("---")

    # Add new doctor
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
                    admin_insert_doctor(
                        name=d_name.strip(),
                        specialty=d_specialty.strip(),
                        phone_number=d_phone.strip()
                    )
                    st.success(f"Doctor '{d_name}' added.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to add doctor: {e}")

    st.markdown("---")

    # Show all hospitals
    st.subheader("All Hospitals")
    try:
        hospitals = admin_get_all_hospitals()
        if hospitals:
            df_hosp = pd.DataFrame(hospitals)
            st.dataframe(df_hosp, use_container_width=True)
        else:
            st.info("No hospitals found in admin_schema.hospitals.")
    except Exception as e:
        st.error(f"Error loading hospitals: {e}")

    st.markdown("---")

    # Add new hospital
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
                    admin_insert_hospital(
                        name=h_name.strip(),
                        address=h_address.strip() or None,
                        phone_number=h_phone.strip() or None
                    )
                    st.success(f"Hospital '{h_name}' added.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to add hospital: {e}")

# --- Cell ---



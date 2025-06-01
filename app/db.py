# --- Cell ---
# db.py

from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker

# =============================================================================
# 1. Set your actual DB connection info here
# =============================================================================
DB_USER = "postgres"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Healthcare"

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create a single Engine that everyone will share
engine = create_engine(DATABASE_URL, echo=False)

# Session factory (if ever needed)
SessionLocal = sessionmaker(bind=engine)

# =============================================================================
# 2. Reflect each schema into its own MetaData object
# =============================================================================

# NOTE: The SQL you ran created these three schemas and copied "LIKE public…"
#       for each table. So we know exactly which tables live under which schema.

# --- doctor_schema: contains patients, medical_records, medications ---
doctor_meta = MetaData(schema="doctor_schema")
doctor_meta.reflect(bind=engine)

Patients_doctor        = Table("patients", doctor_meta, autoload_with=engine)
MedicalRecords_doctor  = Table("medical_records", doctor_meta, autoload_with=engine)
Medications_doctor     = Table("medications", doctor_meta, autoload_with=engine)

# --- patient_schema: contains patients, medical_records ---
patient_meta = MetaData(schema="patient_schema")
patient_meta.reflect(bind=engine)

Patients_patient       = Table("patients", patient_meta, autoload_with=engine)
MedicalRecords_patient = Table("medical_records", patient_meta, autoload_with=engine)

# --- admin_schema: contains patients, hospitals, doctors, medications, 
#     insurance_providers, medical_records ---
admin_meta = MetaData(schema="admin_schema")
admin_meta.reflect(bind=engine)

Patients_admin          = Table("patients", admin_meta, autoload_with=engine)
Hospitals_admin         = Table("hospitals", admin_meta, autoload_with=engine)
Doctors_admin           = Table("doctors", admin_meta, autoload_with=engine)
Medications_admin       = Table("medications", admin_meta, autoload_with=engine)
InsuranceProviders_admin= Table("insurance_providers", admin_meta, autoload_with=engine)
MedicalRecords_admin    = Table("medical_records", admin_meta, autoload_with=engine)

# =============================================================================
# 3. A helper to “SET ROLE” + “SET search_path” + run your SQL
# =============================================================================

def _execute_with_role(sql_text: str, role: str, schema: str, **params):
    """
    Open a new Connection, do SET search_path and SET ROLE, then execute sql_text.
    - sql_text: a SQL string (it can use :param placeholders).
    - role: the exact Postgres role name (“doctor_user”, “patient_user”, “admin_user”).
    - schema: the schema we want on the search_path (e.g. "doctor_schema").
    - params: any bind parameters for the SQL.

    Returns a ResultProxy if it’s a SELECT, or None for INSERT/UPDATE/DELETE.
    """
    conn = engine.connect()
    # 1) set the schema search_path
    conn.execute(text(f"SET search_path TO {schema}"))
    # 2) switch to the given role
    conn.execute(text(f"SET ROLE {role}"))
    # 3) run the actual query
    result = conn.execute(text(sql_text), params)  # pass **params for :placeholders
    return result


# =============================================================================
# 4. Doctor‐side functions (runs as doctor_user on doctor_schema)
# =============================================================================

def doctor_get_all_patients():
    """
    Returns all rows from doctor_schema.patients as a list of dicts.
    """
    sql = "SELECT * FROM patients"  # search_path is already set to doctor_schema
    result = _execute_with_role(sql, role="doctor_user", schema="doctor_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows


def doctor_insert_patient(name: str, age: int, gender: str, blood_type: str):
    """
    Inserts a new row into doctor_schema.patients.
    """
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
    """
    Returns all rows from doctor_schema.medical_records as a list of dicts.
    """
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
    """
    Inserts a new row into doctor_schema.medical_records.
    """
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
# 5. Patient‐side functions (runs as patient_user on patient_schema, with RLS)
# =============================================================================

def patient_get_own_medical_records(patient_id: int):
    """
    Returns only those rows from patient_schema.medical_records where 
    patient_id = given patient_id. This relies on your RLS policy
    using session variable app.patient_id.

    We do, in order:
      1) SET ROLE patient_user
      2) SET app.patient_id = <patient_id>
      3) SET search_path TO patient_schema
      4) SELECT * FROM medical_records
    """
    conn = engine.connect()
    # 1. switch to patient_user
    conn.execute(text("SET ROLE patient_user"))
    # 2. establish the session variable RLS expects
    conn.execute(text("SET app.patient_id = :pid"), {"pid": patient_id})
    # 3. set schema to patient_schema
    conn.execute(text("SET search_path TO patient_schema"))
    # 4. run the SELECT
    result = conn.execute(text("SELECT * FROM medical_records"))
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows


# =============================================================================
# 6. Admin‐side functions (runs as admin_user on admin_schema)
# =============================================================================

def admin_get_all_doctors():
    """
    Returns all rows from admin_schema.doctors as a list of dicts.
    """
    sql = "SELECT * FROM doctors"
    result = _execute_with_role(sql, role="admin_user", schema="admin_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows


def admin_insert_doctor(name: str, specialty: str, phone_number: str):
    """
    Inserts a new doctor into admin_schema.doctors.
    """
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
    """
    Returns all rows from admin_schema.hospitals.
    """
    sql = "SELECT * FROM hospitals"
    result = _execute_with_role(sql, role="admin_user", schema="admin_schema")
    rows = [dict(r) for r in result.fetchall()]
    result.close()
    return rows


def admin_insert_hospital(name: str, address: str = None, phone_number: str = None):
    """
    Inserts a new hospital into admin_schema.hospitals.
    """
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

# --- Cell ---



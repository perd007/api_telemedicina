"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, Blueprint
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Doctor, Patient, Appointment, Record
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
# JWT TOKEN
from flask_jwt_extended import JWTManager
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
jwt = JWTManager(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


# aqui cominezas mis rutas
# login doctor
# validamos al usuario y le asignamos un token
@app.route("/login", methods=["POST"])
def doctor_login():

    data = request.get_json()
    email = data.get("email", None)
    password = data.get("password", None)
    # Reserva.query.filter_by(fecha=fecha, time=time, id_place=id).first()
    # validamos que el usario exista
    doctor_exist = Doctor.query.filter_by(email=email).first()
    patient_exist = Patient.query.filter_by(email=email).first()
    if not doctor_exist:
        if not patient_exist:
            return jsonify({"error": "User not found"}), 404
        else:
            user_exit = patient_exist
            type_user = "patient"
    else:
        user_exit = doctor_exist
        type_user = "doctor"

    # obtenemos el password y lo comparamos
    password_check = check_password_hash(user_exit.password, password)
    if not password_check:
        return jsonify({"error": "Password incorrecto"}), 401

    # se crea el token
    token_data = {"id": user_exit.id, "email": user_exit.email, "type": type_user}
    token = create_access_token(token_data)
    return jsonify({"token": token, "type": type_user}), 200


##########################CRUD DOCTOR#########################################
# get doctor by id
@app.route("/doctor/<int:id>", methods=["GET"])
def get_doctor_by_id(id):
    current_doctor = Doctor.query.get(id)
    if not current_doctor:
        return jsonify({"error": "doctor not found"}), 404
    return jsonify(current_doctor.serialize()), 200


# create a doctor
@app.route("/doctor", methods=["POST"])
def create_doctor():
    data = request.get_json()
    name = data.get("name", None)
    dni = data.get("dni", None)
    email = data.get("email", None)
    password = data.get("password", None)
    registrattiont = data.get("registrationt", None)
    specialty = data.get("specialty", None)
    number = data.get("number", None)

    # validamos que el doctor no exista
    doctor_exist = Doctor.query.filter_by(email=email).first()
    if doctor_exist:
        return jsonify({"error": "Doctor exist"}), 404

    # si no existe continuamos
    hashed_password = generate_password_hash(password)

    try:
        new_doctor = Doctor(
            name=name,
            email=email,
            password=hashed_password,
            dni=dni,
            registrationt=registrattiont,
            specialty=specialty,
            number=number,
            is_active=True,
        )
        db.session.add(new_doctor)
        db.session.commit()

        return jsonify(new_doctor.serialize()), 201

    except Exception as error:
        db.session.rollback()
        return jsonify(error.args), 500


# edict a doctor
@app.route("/doctor/<int:id>", methods=["PUT"])
@jwt_required()
def edit_doctor(id):
    data = request.get_json()
    name = data.get("name", None)
    dni = data.get("dni", None)
    email = data.get("email", None)
    password = data.get("password", None)
    registrattiont = data.get("registrationt", None)
    specialty = data.get("specialty", None)
    number = data.get("number", None)

    # validamos que el doctor no exista
    doctor_exist = Doctor.query.filter_by(id=id).first()
    if not doctor_exist:
        return jsonify({"error": "Doctor not exist"}), 404

    # si no existe el paswword se le asigna su mismo valor
    if not password:
        password = doctor_exist.password

    # de los contrario se hashead el nuevo
    password = generate_password_hash(password)

    try:
        update_doctor = Doctor.query.get(id)
        if not update_doctor:
            return jsonify({"error": "doctor not found"}), 404

        update_doctor.name = name
        update_doctor.password = password
        update_doctor.email = email
        update_doctor.password = (password,)
        update_doctor.dni = (dni,)
        update_doctor.registrationt = (registrattiont,)
        update_doctor.specialty = (specialty,)
        update_doctor.number = (number,)
        db.session.commit()
        return jsonify({"Doctor": update_doctor.serialize()}), 200

    except Exception as error:
        db.session.rollback()
        return jsonify(error), 500


# delete doctor
@app.route("/doctor/<int:id>", methods=["DELETE"])
def delete_doctor_by_id(id):
    doctor_to_delete = Doctor.query.get(id)
    if not doctor_to_delete:
        return jsonify({"error": "user not found"}), 404

    try:
        db.session.delete(doctor_to_delete)
        db.session.commit()
        return jsonify("doctor deleted successfully"), 200

    except Exception as error:
        db.session.rollback()
        return error, 500


##########################CRUD PATIENT#########################################


# get patient by id
@app.route("/patient/<int:id>", methods=["GET"])
@jwt_required()
def get_patient_by_id(id):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        current_patient = Patient.query.get(id)
        if not current_patient:
            return jsonify({"error": "patient not found"}), 404
        return jsonify(current_patient.serialize()), 200
    else:
        return jsonify({"error": "this user is not a doctor"}), 404


# get patients
@app.route("/patients", methods=["GET"])
#@jwt_required()
def get_patients():
    patients = Patient.query.all()
    return jsonify({"patienst": [patient.serialize() for patient in patients]}), 200
    # serialized_pacient = [patients.serialize() for patient in patients]
    # serialized_pacient = []
    # for patient in patients:
    #    serialized_pacient.append(patient.serialize())
    # return jsonify({"patienst": serialized_pacient}), 200


# create a patient
@app.route("/patient", methods=["POST"])
def create_patient():
    data = request.get_json()
    name = data.get("name", None)
    dni = data.get("dni", None)
    email = data.get("email", None)
    password = data.get("password", None)
    city = data.get("city", None)
    country = data.get("country", None)
    age = data.get("age", None)
    gender = data.get("gender", None)
    number = data.get("number", None)

    # validamos que el patient no exista
    patient_exist = Patient.query.filter_by(email=email).first()
    if patient_exist:
        return jsonify({"error": "patient exist"}), 404

    # si no existe continuamos
    hashed_password = generate_password_hash(password)

    try:
        new_patient = Patient(
            name=name,
            email=email,
            password=hashed_password,
            dni=dni,
            city=city,
            country=country,
            age=age,
            gender=gender,
            number=number,
            is_active=True,
        )
        db.session.add(new_patient)
        db.session.commit()

        return jsonify(new_patient.serialize()), 201

    except Exception as error:
        db.session.rollback()
        return jsonify(error.args), 500


# edit a patient
@app.route("/patient/<int:id>", methods=["PUT"])
@jwt_required()
def edit_patient(id):
    data = request.get_json()
    name = data.get("name", None)
    dni = data.get("dni", None)
    email = data.get("email", None)
    password = data.get("password", None)
    city = data.get("city", None)
    country = data.get("country", None)
    age = data.get("age", None)
    gender = data.get("gender", None)
    number = data.get("number", None)

    # validamos que el patient no exista

    patient_exist = Patient.query.filter_by(id=id).first()
    if not patient_exist:
        return jsonify({"error": "patient not exist"}), 404

    # si no existe el paswword se le asigna su mismo valor
    if not password:
        password = patient_exist.password

    # de los contrario se hashead el nuevo
    password = generate_password_hash(password)

    try:
        update_patient = Patient.query.get(id)
        if not update_patient:
            return jsonify({"error": "patient not found"}), 404

        update_patient.password = password
        update_patient.email = email
        update_patient.password = password
        update_patient.dni = dni
        update_patient.country = country
        update_patient.city = city
        update_patient.age = age
        update_patient.gender = gender
        update_patient.number = number
        db.session.commit()
        return jsonify({"Patient": update_patient.serialize()}), 200

    except Exception as error:
        db.session.rollback()
        return jsonify(error), 500


# delete patient
@app.route("/patient/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_patient_by_id(id):
    patient_to_delete = Patient.query.get(id)

    if not patient_to_delete:
        return jsonify({"error": "patient not found"}), 404

    try:
        db.session.delete(patient_to_delete)
        db.session.commit()
        return jsonify("patient deleted successfully"), 200

    except Exception as error:
        db.session.rollback()
        return error, 500


##########################CRUD APPOINTMENT#########################################


# get appointment by id
@app.route("/appointment/<int:id>", methods=["GET"])
@jwt_required()
def get_appointment_by_id(id):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        current_appointment = Appointment.query.get(id)
        if not current_appointment:
            return jsonify({"error": "appointment not found"}), 404
        return jsonify(current_appointment.serialize()), 200
    else:
        return jsonify({"error": "this useris not a doctor"}), 404


# get all appointments
@app.route("/appointments", methods=["GET"])
@jwt_required()
def get_appointments():
    user = get_jwt_identity()
    if user["type"] == "doctor":
        appointments = Appointment.query.all()
        return (
            jsonify(
                {
                    "appointment": [
                        appointment.serialize() for appointment in appointments
                    ]
                }
            ),
            200,
        )
    else:
        return jsonify({"error": "this useris not a doctor"}), 404
    # serialized_appointment = [appointment.serialize() for appointment in appointments]
    # serialized_appointment = []
    # for appointment in appointments:
    #    serialized_appointment.append(appointment.serialize())
    # return jsonify({"appointment": serialized_appointment}), 200


# get appointment by status
@app.route("/appointment/status", methods=["POST"])
@jwt_required()
def get_appointments_status():
    data = request.get_json()
    user = get_jwt_identity()
    if user["type"] == "doctor":
        status = data.get("confirmation", None)
        appointments = Appointment.query.filter_by(confirmation=status).all()
        return (
            jsonify(
                {
                    "appointment": [
                        appointment.serialize() for appointment in appointments
                    ]
                }
            ),
            200,
        )
    else:
        return jsonify({"error": "this useris not a doctor"}), 404

    # serialized_appointment = [appointment.serialize() for appointment in current_appointment]
    # serialized_appointment = []
    # for appointment in appointments:
    #   serialized_appointment.append(appointment.serialize())
    # return jsonify({"appointment": serialized_appointment}), 200


# create a appointment
@app.route("/appointment/<int:id_doctor>/<int:id_patient>", methods=["POST"])
@jwt_required()
def create_appointment(id_doctor, id_patient):
    data = request.get_json()
    date = data.get("date", None)
    reason = data.get("reason", None)
    mode = data.get("mode", None)
    confirmation = data.get("confirmation", None)

    try:
        new_appointment = Appointment(
            date=date,
            reason=reason,
            mode=mode,
            confirmation=confirmation,
            id_doctor=id_doctor,
            id_patient=id_patient,
        )
        db.session.add(new_appointment)
        db.session.commit()

        return jsonify(new_appointment.serialize()), 201

    except Exception as error:
        db.session.rollback()
        return jsonify(error.args), 500


# edit a appointment
@app.route("/appointment/<int:id>", methods=["PUT"])
@jwt_required()
def edit_appointment(id):
    data = request.get_json()
    date = data.get("date", None)
    reason = data.get("reason", None)
    mode = data.get("mode", None)
    confirmation = data.get("confirmation", None)

    # validamos que el appointment no exista
    appointment_exist = Appointment.query.filter_by(id=id).first()
    if not appointment_exist:
        return jsonify({"error": "appointment not exist"}), 404

    try:
        update_appointment = Appointment.query.get(id)
        if not update_appointment:
            return jsonify({"error": "appointment not found"}), 404

        update_appointment.date = date
        update_appointment.reason = reason
        update_appointment.mode = mode
        update_appointment.confirmation = confirmation

        db.session.commit()
        return jsonify({"appointment": update_appointment.serialize()}), 200

    except Exception as error:
        db.session.rollback()
        return jsonify(error), 500


# delete appointment
@app.route("/appointment/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_appointment_by_id(id):
    appointment_to_delete = Appointment.query.get(id)

    if not appointment_to_delete:
        return jsonify({"error": "appointment not found"}), 404

    try:
        db.session.delete(appointment_to_delete)
        db.session.commit()
        return jsonify("appointment deleted successfully"), 200

    except Exception as error:
        db.session.rollback()
        return error, 500

    ##########################CRUD RECORD#########################################


# get record by id
@app.route("/record/<int:id>", methods=["GET"])
@jwt_required()
def get_record_by_id(id):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        record = Record.query.get(id)
        if not record:
            return jsonify({"error": "record not found"}), 404

        return jsonify(record.serialize()), 200
    else:
        return jsonify({"error": "this useris not a doctor"}), 404


# get record by appoitnment
@app.route("/record/appointment/<int:id_appointment>", methods=["GET"])
@jwt_required()
def get_record_by_id_appointment(id_appointment):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        record = Record.query.filter_by(id_appointment=id_appointment)
        if not record:
            return jsonify({"error": "record not found"}), 404
        return jsonify(record.serialize()), 200
    else:
        return jsonify({"error": "this useris not a doctor"}), 404


# create a record
@app.route("/record/<int:id_appointment>/", methods=["POST"])
@jwt_required()
def create_record(id_appointment):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        data = request.get_json()
        date = data.get("date", None)
        diagnosis = data.get("diagnosis", None)
        treatment = data.get("treatment", None)
        recommendations = data.get("recommendations", None)

        try:
            new_record = Record(
                date=date,
                diagnosis=diagnosis,
                treatment=treatment,
                recommendations=recommendations,
                id_appointment=id_appointment,
            )
            db.session.add(new_record)
            db.session.commit()

            return jsonify(new_record.serialize()), 201

        except Exception as error:
            db.session.rollback()
            return jsonify(error.args), 500

    else:
        return jsonify({"error": "this useris not a doctor"}), 404


# edict a record
@app.route("/record/<int:id>", methods=["PUT"])
@jwt_required()
def edit_record(id):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        data = request.get_json()
        date = data.get("date", None)
        diagnosis = data.get("diagnosis", None)
        treatment = data.get("treatment", None)
        recommendations = data.get("recommendations", None)

        # validamos que el record no exista
        record_exist = Record.query.filter_by(id=id).first()
        if not record_exist:
            return jsonify({"error": "record not exist"}), 404

        try:
            update_record = Record.query.get(id)
            if not update_record:
                return jsonify({"error": "record not found"}), 404

            update_record.date = date
            update_record.diagnosis = diagnosis
            update_record.treatment = treatment
            update_record.recommendations = recommendations

            db.session.commit()
            return jsonify({"record": update_record.serialize()}), 200

        except Exception as error:
            db.session.rollback()
            return jsonify(error), 500
    else:
        return jsonify({"error": "this useris not a doctor"}), 404


# delete record
@app.route("/record/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_record_by_id(id):
    user = get_jwt_identity()
    if user["type"] == "doctor":
        record_to_delete = Record.query.get(id)
        if not record_to_delete:
            return jsonify({"error": "record not found"}), 404

        try:
            db.session.delete(record_to_delete)
            db.session.commit()
            return jsonify("record deleted successfully"), 200

        except Exception as error:
            db.session.rollback()
            return error, 500
    else:
        return jsonify({"error": "this useris not a doctor"}), 404


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

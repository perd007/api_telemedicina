from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
        }


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, nullable=False)
    dni = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), unique=False, nullable=False)
    registrationt = db.Column(db.String(200), unique=True, nullable=False)
    specialty = db.Column(db.String(30), unique=False, nullable=False)
    number = db.Column(db.Integer, unique=False, nullable=False)
    appointment = db.relationship("Appointment", backref="doctor", lazy=True)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)

    def __repr__(self):
        return f"<Doctor {self.name}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "dni": self.dni,
            "email": self.email,
            "registrationt": self.registrationt,
            "specialty": self.specialty,
            "number": self.number,
        }


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, nullable=False)
    dni = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), unique=False, nullable=False)
    city = db.Column(db.String(50), unique=False, nullable=False)
    country = db.Column(db.String(40), unique=False, nullable=False)
    age = db.Column(db.Integer, unique=False, nullable=False)
    gender = db.Column(db.String(20), unique=False, nullable=False)
    number = db.Column(db.Integer, unique=False, nullable=False)
    appointment = db.relationship("Appointment", backref="patient", lazy=True)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)

    def __repr__(self):
        return f"<Patient {self.name}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "dni": self.dni,
            "email": self.email,
            "city": self.city,
            "country": self.country,
            "age": self.age,
            "gender": self.gender,
            "number": self.number,
        }


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, nullable=False)
    reason = db.Column(db.String(200), unique=False, nullable=False)
    mode = db.Column(db.String(30), unique=False, nullable=False)
    confirmation = db.Column(db.String(20), unique=False, nullable=False)
    id_doctor = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    id_patient = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    record = db.relationship("Record", backref="appointment", lazy=True)

    def __repr__(self):
        return f"<Appointment {self.date}>"

    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "reason": self.reason,
            "mode": self.mode,
            "confirmation": self.confirmation,
            "id_doctor": self.id_doctor,
            "id_patient": self.id_patient,
        }


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diagnosis = db.Column(db.String(1000), unique=False, nullable=False)
    recommendations = db.Column(db.String(1000), unique=False, nullable=False)
    treatment = db.Column(db.String(1000), unique=False, nullable=False)
    date = db.Column(db.Date, unique=False, nullable=False)
    id_appointment = db.Column(
        db.Integer, db.ForeignKey("appointment.id"), nullable=False
    )

    def __repr__(self):
        return f"<Record {self.date}>"

    def serialize(self):
        return {
            "id": self.id,
            "diagnosis": self.diagnosis,
            "recommendations": self.recommendations,
            "treatment": self.treatment,
            "date": self.date,
            "id_patient": self.id_appointment,
        }

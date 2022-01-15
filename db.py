from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os
import datetime
import hashlib

db = SQLAlchemy()

# many users and many times
# many users and one location

association_table = db.Table(
    "association",
    db.Model.metadata,
    db.Column("users", db.Integer, db.ForeignKey("users.id")),
    db.Column("times", db.String, db.ForeignKey("times.id")),
)


# your classes here

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    times = db.relationship("Times", secondary=association_table, back_populates="users")
    session_token = db.Column(db.String, nullable=False, unique=True)
    update_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)

    def __init__(self, **kwargs):
        self.username=kwargs.get("username")
        self.password=bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.location_id=kwargs.get("location_id")
        self.renew_session()

    def _urlsafe_base_64(self):
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()
        print(self.session_token)

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode("utf8"), self.password)

    def verify_session_token(self, session_token):
        return session_token ==self.session_token and datetime.datetime.now() < self.session_expiration
    
    def subsubserialize(self):
        return{
            "id": self.id,
            "username": self.username,
        }

    def subserialize(self):
        loc = Locations.query.filter_by(id=self.location_id).first()
        return{
            "id": self.id,
            "username": self.username,
            "lat":loc.lat,
            "lon":loc.lon
                    }
    
    def serialize(self):
        loc = Locations.query.filter_by(id=self.location_id).first()
        return{
            "id": self.id,
            "username": self.username,
            "lat":loc.lat,
            "lon":loc.lon,
            "times": [t.subserialize() for t in self.times]
        }


class Times(db.Model):
    __tablename__ = "times"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String, nullable = False) 
    users = db.relationship("Users", secondary=association_table, back_populates="times")

    def __init__(self, **kwargs):        
        self.time = kwargs.get("time")

    def subserialize(self):
        return{
            "id": self.id,
            "time": self.time
        }
    
    def serialize(self):
        return{
            "id": self.id,
            "time": self.time,
            "users": [t.subserialize() for t in self.users]
        }


class Locations(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    lon = db.Column(db.String, nullable=False)
    lat = db.Column(db.String, nullable=False)
    country_code = db.Column(db.String, nullable=False)
    users = db.relationship("Users")

    def __init__(self, **kwargs):
        self.lon=kwargs.get("lon")
        self.lat=kwargs.get("lat")
        self.country_code=kwargs.get("country_code")


    def subserialize(self):
        return{
            "id": self.id,
            "lon": self.lon,
            "lat": self.lat,
            "country_code": self.country_code
        }
    
    def serialize(self):
        return{
            "id": self.id,
            "lon": self.lon,
            "lat": self.lat,
            "country_code": self.country_code,
            "users": [t.subsubserialize() for t in self.users]
        }
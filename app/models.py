from app import db
import enum


class CourierType(enum.Enum):
    foot = 1
    bike = 2
    car = 3


class Courier(db.Model):
    __tablename__ = 'Courier'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(CourierType))
    last_delivery = db.Column(db.DateTime)


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    courier_id = db.Column(db.Integer, db.ForeignKey('Courier.id'), 
                           nullable=False, index=True)
    region_id = db.Column(db.Integer, nullable=False, index=True)


class WorkTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    courier_id = db.Column(db.Integer, db.ForeignKey('Courier.id'), nullable=False)
    start = db.Column(db.String(5), index=True)
    end = db.Column(db.String(5), index=True)
    
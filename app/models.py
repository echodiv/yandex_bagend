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
    
    def get_rating():
        """
        (60*60 - min(t, 60*60))/(60*60) * 5 
        где  t  - минимальное из средних времен доставки по районам (в секундах),
        t = min(td[1], td[2], ..., td[n]) 
        td[i]  - среднее время доставки заказов по району  i  (в секундах).
        """
        pass

    def get_earning():
        """
        Заработок рассчитывается как сумма оплаты за каждый завершенный развоз:
        sum = ∑(500 * C) ,
        C  — коэффициент, зависящий от типа курьера 
        (пеший — 2, велокурьер — 5, авто — 9) на момент формирования развоза.
        """
        pass


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
    
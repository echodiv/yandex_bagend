from app import db
import enum


class CourierType(enum.Enum):
    """
    Тип курьера. Возможные значения:
        foot  — пеший курьер
        bike  — велокурьер
        car  — курьер на автомобиле
    """
    foot = 1
    bike = 2
    car = 3


class Courier(db.Model):
    __tablename__ = 'Courier'

    id = db.Column(db.Integer, primary_key=True)
    fake_id = db.Column(db.Integer, index=True)
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
    __tablename__ = 'Region'

    id = db.Column(db.Integer, primary_key=True)
    courier_id = db.Column(db.Integer, db.ForeignKey('Courier.fake_id'), 
                           nullable=False, index=True)
    region_id = db.Column(db.Integer, nullable=False, index=True)


class WorkTime(db.Model):
    __tablename__ = 'WorkTime'

    id = db.Column(db.Integer, primary_key=True)
    courier_id = db.Column(db.Integer, db.ForeignKey('Courier.fake_id'), nullable=False)
    start = db.Column(db.String(5), index=True)
    end = db.Column(db.String(5), index=True)


class Order(db.Model):
    """
    weight         Вес заказа в кг. 2 значащих разряда после запятой.
                   Значения меньше 0.01 и больше 50 невалидны.
    region         Регион доставки
    """
    __tablename__ = 'Order'

    id = db.Column(db.Integer, primary_key=True)
    fake_id = db.Column(db.Integer, index=True)
    weight = db.Column(db.Float, nullable=False)
    region = db.Column(db.Integer, nullable=False)
    executor = db.Column(db.Integer, db.ForeignKey('Courier.fake_id'), nullable=True)
    assign_time = db.Column(db.DateTime, nullable=True)
    complete_time = db.Column(db.DateTime, nullable=True)


class DeliveryTime(db.Model):    
    """
    Промежутки, в которые клиенту удобно принять заказ. 
    
    delivery_from  Время после которого можно совершать доставку
    delivery_to    Время до которого нужно завершить доставку
    """
    __tablename__ = 'DeliveryTime'

    id = db.Column(db.Integer, primary_key=True)
    delivery_from = db.Column(db.String(5), nullable=False)
    delivery_to = db.Column(db.String(5), nullable=False)
    order = db.Column(db.Integer, db.ForeignKey('Order.fake_id'), index=True)



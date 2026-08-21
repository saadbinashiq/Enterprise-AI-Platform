from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Store(Base):
    __tablename__ = "stores"
    store_id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    size_sqft = Column(Integer)


class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    price = Column(Float)
    cost = Column(Float)


class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(Integer, primary_key=True)
    name = Column(String)
    department = Column(String)
    store_id = Column(Integer, ForeignKey("stores.store_id"))
    salary = Column(Float)
    hire_date = Column(Date)


class Vendor(Base):
    __tablename__ = "vendors"
    vendor_id = Column(Integer, primary_key=True)
    name = Column(String)
    reliability_score = Column(Float)
    avg_lead_time_days = Column(Integer)


class Campaign(Base):
    __tablename__ = "campaigns"
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    channel = Column(String)
    budget = Column(Float)
    start_date = Column(Date)
    end_date = Column(Date)


class Sale(Base):
    __tablename__ = "sales"
    sale_id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.store_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    date = Column(Date)
    quantity = Column(Integer)
    revenue = Column(Float)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    ticket_id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.store_id"))
    issue_type = Column(String)
    date = Column(Date)
    resolved_in_hours = Column(Float)

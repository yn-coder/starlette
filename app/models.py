from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from datetime import datetime

class Base(DeclarativeBase):
    pass

# System of units
class System_of_Unit(Base):
    __tablename__ = "system_of_unit"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]

# Physical quantity
class Physical_Quantity(Base):
    __tablename__ = "physical_quantity"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]

# Units
class Unit(Base):
    __tablename__ = "unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    short_name: Mapped[str]
    convrsion_coefficient : Mapped[float] = mapped_column(default=1)

    system_of_unit_id = mapped_column(ForeignKey("system_of_unit.id"), nullable=False )
    system_of_unit = relationship("System_of_Unit")

    physical_quantity_id = mapped_column(ForeignKey("physical_quantity.id"), nullable=False )
    physical_quantity = relationship("Physical_Quantity")

# Physical property
class Physical_Property(Base):
    __tablename__ = "physical_property"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    physical_quantity_id = mapped_column(ForeignKey("physical_quantity.id"), nullable=False )
    physical_quantity = relationship("Physical_Quantity")

# Product
class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    out_cost: Mapped[float]
    
# Node type
class Node_Type(Base):
    __tablename__ = "node_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    
    in_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    in_product = relationship( "Product", foreign_keys=[in_product_id])

    out_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    out_product = relationship( "Product", foreign_keys=[out_product_id])
    
    value : Mapped[float]
    power : Mapped[float]
    capex_cost : Mapped[float]
    opex_cost : Mapped[float]

# Product physical property
class Product_Physical_Property(Base):
    __tablename__ = "product_physical_property"
    id: Mapped[int] = mapped_column(primary_key=True)
    value : Mapped[float]
    physical_property_id = mapped_column(ForeignKey("physical_property.id"), nullable=False )
    physical_property = relationship("Physical_Property")
    product_id = mapped_column(ForeignKey("product.id"), nullable=False )
    product = relationship("Product")

# Project
class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    name : Mapped[str]
   
    ininital_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    ininital_product = relationship( "Product", foreign_keys=[ininital_product_id])

    finit_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    finit_product = relationship( "Product", foreign_keys=[finit_product_id])

    cost_coef : Mapped[float]
    power_cost : Mapped[float]

# Project nodes
class Project_Node(Base):
    __tablename__ = "project_nodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    step : Mapped[int]

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False )
    project = relationship( "Project", foreign_keys=[project_id])
   
    node_type_id: Mapped[int] = mapped_column(ForeignKey("node_type.id"), nullable=False )
    node_type = relationship( "Node_Type", foreign_keys=[node_type_id])
    
    equipent_count : Mapped[int]

    value : Mapped[float]
    power : Mapped[float]
    capex_cost : Mapped[float]
    opex_cost : Mapped[float]


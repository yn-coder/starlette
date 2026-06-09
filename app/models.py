from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, select

from datetime import datetime

from .tech_tree import make_graph

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

    value : Mapped[float]
    power : Mapped[float]
    capex_cost : Mapped[float]
    opex_cost : Mapped[float]

# Node type to products link (many to many)
class Node_Type_Product(Base):
    __tablename__ = "node_type_product"
    id: Mapped[int] = mapped_column(primary_key=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=False )
    product = relationship( "Product", foreign_keys=[product_id])

    # False for input product
    # True for output product
    out_flag : Mapped[bool] = mapped_column(nullable=False)

    node_type_id: Mapped[int] = mapped_column(ForeignKey("node_type.id"), nullable=False )
    node_type = relationship( "Node_Type", foreign_keys=[node_type_id])

    share : Mapped[float]

def make_graph_from_DB( arg_session ):
    products = arg_session.execute( select(Product) ).scalars().all()
    node_type = arg_session.execute( select(Node_Type) ).scalars().all()
    node_link = arg_session.execute( select(Node_Type_Product) ).scalars().all()

    return make_graph( products, node_type, node_link )

def get_shortest_path( G, ininital_product_id, finit_product_id ):
    import networkx as nx
    return nx.shortest_path( G, source = "p" + str( ininital_product_id ), target = "p" + str( finit_product_id ) )

def extract_node_id_list_from_path( arg_path ):
    res_list = ()
    for p in arg_path:
        if p[0] == 'n':
            res_list = res_list + ( int( p[1:] ), )

    return res_list

def get_finit_products( G, ininital_product_id ):
    import networkx as nx
    paths = nx.descendants( G, source = "p" + str( ininital_product_id ) )
    #print( paths )    
    
    res_list = ()
    for p in paths:
        if p[0] == 'p':
            res_list = res_list + ( int( p[1:] ), )
   
    return res_list

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
    lon : Mapped[float] = mapped_column( nullable=True )
    lat : Mapped[float] = mapped_column( nullable=True )

    ininital_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    ininital_product = relationship( "Product", foreign_keys=[ininital_product_id])

    finit_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    finit_product = relationship( "Product", foreign_keys=[finit_product_id])

    cost_coef : Mapped[float]
    power_cost : Mapped[float]

    @property
    def can_calculate(self) -> bool:
        return not ( self.ininital_product_id is None )

# Project model (variant)
class Project_Model(Base):
    __tablename__ = "project_model"
    id: Mapped[int] = mapped_column(primary_key=True)

    created_dt: Mapped[datetime]
    # 0 - success
    # 1 - fail
    tech_result : Mapped[bool] = mapped_column(nullable=False)
    log : Mapped[str] = mapped_column(nullable=True )

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False )
    project = relationship( "Project", foreign_keys=[project_id])

    ininital_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    ininital_product = relationship( "Product", foreign_keys=[ininital_product_id])

    finit_product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=True )
    finit_product = relationship( "Product", foreign_keys=[finit_product_id])

    total_capex : Mapped[float]
    value : Mapped[float]
    power : Mapped[float]

    reg_opex : Mapped[float]
    reg_income : Mapped[float]
    reg_power_cost : Mapped[float]

    bottleneck_node_id : Mapped[int] = mapped_column(ForeignKey("project_model_node.id"), nullable=True )
    bottleneck_node = relationship( "Project_Model_Node", foreign_keys=[bottleneck_node_id])

    building_delay : Mapped[float]
    project_payback : Mapped[float]

# Project model nodes
class Project_Model_Node(Base):
    __tablename__ = "project_model_node"
    id: Mapped[int] = mapped_column(primary_key=True)
    step : Mapped[int]

    project_model_id: Mapped[int] = mapped_column(ForeignKey("project_model.id"), nullable=False )
    project_model = relationship( "Project_Model", foreign_keys=[project_model_id])
    # yes, it's a cash for project_model.project_id
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False )
    project = relationship( "Project", foreign_keys=[project_id])

    node_type_id: Mapped[int] = mapped_column(ForeignKey("node_type.id"), nullable=False )
    node_type = relationship( "Node_Type", foreign_keys=[node_type_id])

    equipent_count : Mapped[int]

    value : Mapped[float]
    power : Mapped[float]
    capex_cost : Mapped[float]
    opex_cost : Mapped[float]

# Project model cashflow
class Project_Model_Cashflow(Base):
    __tablename__ = "project_model_cashflow"
    id: Mapped[int] = mapped_column(primary_key=True)

    project_model_id: Mapped[int] = mapped_column(ForeignKey("project_model.id"), nullable=False )
    project_model = relationship( "Project_Model", foreign_keys=[project_model_id])
    # yes, it's a cash for project_model.project_id
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False )
    project = relationship( "Project", foreign_keys=[project_id])

    year : Mapped[int]
    balance : Mapped[float]
    income : Mapped[float]
    opex  : Mapped[float]

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session

from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse, HTMLResponse

from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.views import Link
import jinja2

from .models import *
from .tech_tree import *
from .populate import do_populate
from .project_calc import *

engine = create_engine("sqlite:///concepts.db", connect_args={"check_same_thread": False})

templates = Jinja2Templates(directory='templates')


Base.metadata.create_all(engine)
session = Session(engine)
# if base is empty - populate with init data
is_empty = session.query( Product ).first() is None
if is_empty:
    do_populate(session)

async def homepage(request):

    p_table = select(Project)
    projects = session.execute(p_table).scalars().all()

    return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={  "projects" : projects,
               "menu_item" : "project",
               }
    )

# project page
async def get_project(request):
    project_id = request.path_params['project_id']
    project = session.get(Project, project_id )

    # view model page? Optional. So "get"
    view_model_id = request.path_params.get('model_id')

    pm = select(Project_Model).where( Project_Model.project_id == project_id )
    project_models = session.execute(pm).scalars().all()

    total_capex = 0
    reg_opex = 0
    reg_income = 0
    reg_power_cost = 0

    project_payback = 0
    bottleneck_value = float( 'inf' ) # unlimited flow
    bottleneck_node = None

    project_nodes = None
    view_model = None
    model_cashflow = None

    if view_model_id:
        view_model = session.get(Project_Model, view_model_id )
        total_capex = view_model.total_capex
        reg_opex = view_model.reg_opex
        reg_income = view_model.reg_income
        reg_power_cost = view_model.reg_power_cost
        bottleneck_value = view_model.value
        if view_model.bottleneck_node:
            bottleneck_node = view_model.bottleneck_node
            project_payback = view_model.project_payback

        pn = select(Project_Model_Node).where( Project_Model_Node.project_model_id == view_model_id )
        project_nodes = session.execute( pn ).scalars().all()
        cf = select(Project_Model_Cashflow).where( Project_Model_Cashflow.project_model_id == view_model_id )
        model_cashflow = session.execute( cf ).scalars().all()

    can_calculate_flag = project.can_calculate

    return templates.TemplateResponse(
        request=request,
        name = "project.html",
        context = { "project" : project,
                    "menu_item" : "project",
                    "project_models" : project_models,
                    "can_calculate_flag" : can_calculate_flag, "view_model_id" : view_model_id, 'view_model' : view_model,
                    "project_nodes" : project_nodes,
                    "reg_income" : reg_income, "total_capex" : total_capex, "reg_power_cost" : reg_power_cost, "reg_opex" : reg_opex, "model_cashflow" : model_cashflow,
                    "bottleneck_value" : bottleneck_value,
                    "bottleneck_node" : bottleneck_node,
                    'project_payback' : project_payback,
                          }
    )

# calcualte project
async def calc_project(request):
    project_id = request.path_params['project_id']
    project = session.get(Project, project_id )

    Calc_Project( project, session )

    return RedirectResponse(url=f"/view/project/{project_id}", status_code=302)

# product list
async def get_product_list(request):
    p_table = select(Product)
    products = session.execute(p_table).scalars().all()

    return templates.TemplateResponse(
    request=request,
    name="products.html",
    context={ "products" : products,
              "menu_item" : "product",
            }
    )

# product page
async def get_product(request):
    product_id = request.path_params['product_id']
    product = session.get(Product, product_id )

    fn = select(Node_Type_Product).where( Node_Type_Product.product_id == product_id, Node_Type_Product.out_flag == True )
    from_nodes = session.execute( fn ).scalars().all()

    tn = select(Node_Type_Product).where( Node_Type_Product.product_id == product_id, Node_Type_Product.out_flag == False )
    to_nodes = session.execute( tn ).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="product.html",
        context = { "product" : product,
                    "menu_item" : "product",
                    "from_nodes" : from_nodes, "to_nodes" : to_nodes,
                  }
    )

# node type list
async def get_node_type_list(request):
    p_table = select(Node_Type)
    node_types = session.execute(p_table).scalars().all()

    return templates.TemplateResponse(
    request=request,
    name="node_types.html",
    context={ "node_types" : node_types,
              "menu_item" : "node",
            }
    )

# node type page
async def get_node_type(request):
    node_type_id = request.path_params['node_type_id']
    node_type = session.get(Node_Type, node_type_id )

    ip = select(Node_Type_Product).where( Node_Type_Product.node_type_id == node_type_id, Node_Type_Product.out_flag == False )
    in_products = session.execute( ip ).scalars().all()

    op = select(Node_Type_Product).where( Node_Type_Product.node_type_id == node_type_id, Node_Type_Product.out_flag == True )
    out_products = session.execute( op ).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="node_type.html",
        context = { "node_type" : node_type,
                    "menu_item" : "node",
                    "in_products" : in_products,
                    "out_products" : out_products,
                  }
    )


# get technology tree
async def get_technology_tree(request):
    return templates.TemplateResponse(
        request=request,
        name="technology_tree.html",
        context = { "menu_item" : "tree", }
    )

async def tech_graph_json(request):
    G = make_graph_from_DB( session )
    spec = graph_to_plotly_data(G)
    return JSONResponse(spec)


# test page
async def get_test(request):

    return PlainTextResponse("Test!")

# test page template
async def get_test2(request):

    # Define your template directly as a raw Python string
    template_str = """
    <!DOCTYPE html>
    <html>
    <head><title>Inline Template</title></head>
    <body>
        <h1>Hello, {{ name }}!</h1>
        <p>Welcome to Starlette without external HTML files.</p>
    </body>
    </html>
    """

    # Compile the template string dynamically
    template = jinja2.Template(template_str)

    # Render the dynamic content with your context variables
    rendered_html = template.render(name="Developer")

    # Return the final content inside an HTMLResponse
    return HTMLResponse(content=rendered_html, status_code=200)


app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/view/test", get_test ),
        Route("/view/test2", get_test2 ),
        Route("/view/project/{project_id}", get_project),
        Route("/view/project/{project_id}/view_model/{model_id}", get_project),
        Route("/view/project/{project_id}/calc", calc_project),
        Route("/view/products", get_product_list),
        Route("/view/product/{product_id}", get_product),
        Route("/view/node_types", get_node_type_list),
        Route("/view/node_type/{node_type_id}", get_node_type),
        Route("/view/technology_tree", get_technology_tree),

        Route("/api/get_tech_graph.json", endpoint=tech_graph_json),


        Mount("/statics", app=StaticFiles(directory="statics"), name="statics"),



    ]
)


# Create an empty admin interface
admin = Admin(engine,
    title="Concept projects",
    base_url="/admin",
    route_name="admin",
    templates_dir="templates/admin",

)


# Add view
# admin.add_view(ModelView(System_of_Unit, icon="fas fa-list"))
# admin.add_view(ModelView(Physical_Quantity, icon="fas fa-list"))
# admin.add_view(ModelView(Physical_Property, icon="fas fa-list"))
# admin.add_view(ModelView(Unit, icon="fas fa-list"))
#admin.add_view(ModelView(Product_Physical_Property, icon="fas fa-list"))

admin.add_view(ModelView(Product, icon="fas fa-list"))
admin.add_view(ModelView(Node_Type, icon="fas fa-list"))
admin.add_view(ModelView(Node_Type_Product, icon="fas fa-list"))

admin.add_view(ModelView(Project, icon="fas fa-list"))
admin.add_view(ModelView(Project_Model, icon="fas fa-list"))
admin.add_view(ModelView(Project_Model_Node, icon="fas fa-list"))
admin.add_view(ModelView(Project_Model_Cashflow, icon="fas fa-list"))


# test links

admin.add_view(Link(label="Test page", icon="fa fa-link", url="/view/test"))
admin.add_view(Link(label="Templated test page", icon="fa fa-link", url="/view/test2"))
admin.add_view(Link(label="Technology tree json", icon="fa fa-link", url="/api/get_tech_graph.json"))


# to main page
admin.add_view(Link(label="Main page view", icon="fa fa-link", url="/"))


# Mount admin to your app
admin.mount_to(app)


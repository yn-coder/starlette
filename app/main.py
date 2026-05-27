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
from datetime import datetime

engine = create_engine("sqlite:///concepts.db", connect_args={"check_same_thread": False})

templates = Jinja2Templates(directory='templates')


Base.metadata.create_all(engine)
session = Session(engine)

async def homepage(request):

    p_table = select(Project)
    projects = session.execute(p_table).scalars().all()

    return Jinja2Templates("templates").TemplateResponse(
        "index.html", {"request": request, "projects" : projects }


        
    )

# project page
async def get_project(request):
    project_id = request.path_params['project_id']
    project = session.get(Project, project_id )

    pn = select(Project_Node).where( Project_Node.project_id == project_id )
    project_nodes = session.execute(pn).scalars().all()

    # calculate cost    
    total_capex = 0
    reg_opex = 0
    reg_income = 0
    reg_power_cost = 0
    y_rec = []
    project_payback = 0
    bottleneck_value = float( 'inf' ) # unlimited flow
    bottleneck_node = None
    
    if len( project_nodes ) > 0:
        for pn in project_nodes:
            total_capex = total_capex + pn.capex_cost
            reg_power_cost_one = pn.power * project.power_cost
            reg_power_cost = reg_power_cost + reg_power_cost_one 
            reg_opex = reg_opex + pn.opex_cost + reg_power_cost_one
            
            # detect flow bottleneck - limit for all flow and reg_income
            if pn.value < bottleneck_value:
                bottleneck_value = pn.value
                bottleneck_node = pn
    
        reg_income = project.finit_product.out_cost * bottleneck_value
        
        y_rec = [ ]
        for i in range(10):
            y_rec.append( { 'cost' : - total_capex + ( i * ( reg_income - reg_opex ) ), 
                            'income' : reg_income,
                            'opex' : reg_opex,
                            'year' : i } )
            
        if reg_income > reg_opex:
            project_payback = total_capex / ( reg_income - reg_opex )
    
    return Jinja2Templates("templates").TemplateResponse(
        "project.html", { "request": request, "project" : project, "project_nodes" : project_nodes, 
                          "reg_income" : reg_income, "total_capex" : total_capex, "reg_power_cost" : reg_power_cost, "reg_opex" : reg_opex, "y_rec" : y_rec,
                          "bottleneck_value" : bottleneck_value,
                          "bottleneck_node" : bottleneck_node,
                          'project_payback' : project_payback,
                          }
    )

# calcualte project
async def calc_project(request):
    project_id = request.path_params['project_id']
    project = session.get(Project, project_id )

    pk = project.id
    p_cost_coef = project.cost_coef

    # drop old calculation results
    stmt = delete(Project_Node).where(Project_Node.project_id == pk )
    session.execute(stmt)
    session.commit()

    node_types = session.execute(select(Node_Type)).scalars().all()
    n_step = 0
    for nt in node_types:
        n_step = n_step + 1

        new_node = Project_Node( project_id = pk,
                                 step = n_step,
                                 node_type_id = nt.id,
                                 equipent_count = 1,
                                 value = nt.value,
                                 power = nt.power,
                                 capex_cost = nt.capex_cost * p_cost_coef,
                                 opex_cost = nt.opex_cost * p_cost_coef,
                                 )
        session.add(new_node)
        session.commit()

    return RedirectResponse(url=f"/view/project/{pk}", status_code=302)


# product list
async def get_product_list(request):
    p_table = select(Product)
    products = session.execute(p_table).scalars().all()

    return Jinja2Templates("templates").TemplateResponse(
        "products.html", {"request": request, "products" : products, }
    )

# node type list
async def get_node_type_list(request):
    p_table = select(Node_Type)
    node_types = session.execute(p_table).scalars().all()

    return Jinja2Templates("templates").TemplateResponse(
        "node_types.html", {"request": request, "node_types" : node_types, }
    )
    
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
        Route("/test", get_test ),
        Route("/test2", get_test2 ),
        Route("/view/project/{project_id}", get_project),
        Route("/view/project/{project_id}/calc", calc_project),
        Route("/view/products", get_product_list),
        Route("/view/node_types", get_node_type_list),
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
admin.add_view(ModelView(System_of_Unit, icon="fas fa-list"))
admin.add_view(ModelView(Physical_Quantity, icon="fas fa-list"))
admin.add_view(ModelView(Physical_Property, icon="fas fa-list"))

admin.add_view(ModelView(Unit, icon="fas fa-list"))

admin.add_view(ModelView(Product, icon="fas fa-list"))
admin.add_view(ModelView(Node_Type, icon="fas fa-list"))
admin.add_view(ModelView(Product_Physical_Property, icon="fas fa-list"))

admin.add_view(ModelView(Project, icon="fas fa-list"))
admin.add_view(ModelView(Project_Node, icon="fas fa-list"))


# к основному сайту
admin.add_view(Link(label="Main page view", icon="fa fa-link", url="/"))

# Mount admin to your app
admin.mount_to(app)


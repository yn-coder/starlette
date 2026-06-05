from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, delete

import random

from .models import *

def Calc_Project( project, session ):

    pk = project.id
    p_cost_coef = project.cost_coef

    # drop old calculation results
    prop_old_pn = delete(Project_Model_Node).where(Project_Model_Node.project_id == pk )
    session.execute(prop_old_pn)
    session.commit()

    drop_old_cf = delete(Project_Model_Cashflow).where(Project_Model_Cashflow.project_id == pk )
    session.execute(drop_old_cf)
    session.commit()

    drop_old_pm = delete(Project_Model).where(Project_Model.project_id == pk )
    session.execute(drop_old_pm)
    session.commit()

    project_ininital_product = project.ininital_product
    project_finit_product = project.finit_product

    # can't calculate
    if not project_ininital_product:
        return 0

    # model_finit_product, paths
    # ( None, [] )
    model_array = [  ]

    if project_finit_product:
        # we must to find all paths from project_ininital_product to project_finit_product
        G = make_graph_from_DB( session )
        nx_tree_line = get_shortest_path( G, project_ininital_product.id, project_finit_product.id )
        # becouse of shortest path, it's only one
        model_array = [ ( project_finit_product, extract_node_id_list_from_path( nx_tree_line ) ) ]
    else:
        # we must to find all accessible products
        G = make_graph_from_DB( session )
        nx_finit_products = get_finit_products( G, project_ininital_product.id )
        
        print( nx_finit_products )
        
        for f in nx_finit_products:
            nx_tree_line = get_shortest_path( G, project_ininital_product.id, f )

            extr = extract_node_id_list_from_path( nx_tree_line )
            model_array.append( ( session.get( Product, f ), extr ) )

    # calculate
    for finit_product, path in model_array:
        new_project_model = Project_Model(
                project_id = pk,
                ininital_product_id = project.ininital_product_id,
                created_dt = datetime.now(),
                tech_result = 0,
                total_capex = 0,
                value = 0,
                power = 0,

                reg_opex = 0,
                reg_income = 0,
                reg_power_cost = 0,
                #bottleneck_node_id = None,

                project_payback = 0
                )

        if finit_product:
            new_project_model.finit_product = finit_product

        session.add(new_project_model)
        session.commit()

        # calculate cost
        total_capex = 0
        power = 0
        reg_nodes_opex = 0
        reg_power_cost = 0
        reg_opex = 0
        y_rec = []
        reg_income = 0
        project_payback = 0
        bottleneck_value = float( 'inf' ) # unlimited flow
        bottleneck_node = None

        gg = select(Node_Type).where( Node_Type.id.in_( path ) )
        node_types = session.execute( gg ).scalars().all()
        n_step = 0
        for nt in node_types:
            n_step = n_step + 1

            new_node = Project_Model_Node( project_model_id = new_project_model.id,
                                     project_id = pk,
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

            total_capex = total_capex + new_node.capex_cost
            power = power + new_node.power
            reg_power_cost_one = new_node.power * project.power_cost
            reg_power_cost = reg_power_cost + reg_power_cost_one
            reg_opex = reg_opex + new_node.opex_cost + reg_power_cost_one

            # detect flow bottleneck - limit for all flow and reg_income
            if new_node.value < bottleneck_value:
                bottleneck_value = new_node.value
                bottleneck_node = new_node

        if finit_product:
            reg_income = finit_product.out_cost * bottleneck_value

        if reg_income > reg_opex:
            project_payback = total_capex / ( reg_income - reg_opex )

        #print( reg_income )
        #print( reg_opex )
        #print( total_capex )
        #print( project_payback )

        new_project_model.total_capex = total_capex
        new_project_model.value = bottleneck_value
        new_project_model.power = power

        new_project_model.reg_opex = reg_opex
        new_project_model.reg_income = reg_income
        new_project_model.reg_power_cost = reg_power_cost

        if bottleneck_node:
            new_project_model.bottleneck_node_id = bottleneck_node.id

        new_project_model.project_payback = project_payback
        session.add(new_project_model)
        session.commit()

        for i in range(10):
            pm_cf = Project_Model_Cashflow(
                project_model_id = new_project_model.id,
                project_id = pk,
                year = i,
                balance = ( i * ( reg_income - reg_opex ) ) - total_capex,
                income = reg_income,
                opex = reg_opex
              )
            session.add(pm_cf)
            session.commit()

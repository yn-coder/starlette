from sqlalchemy.orm import Session
import random

from .models import *

# populate with initial data
def do_populate( session ):

    products = ( 'Well fluid', 'Crude oil emulsion', 'Stabilized crude oil', 'Pipeline-grade oil',
                 'Well gas', 'Pipeline-grade gas'
    )

    nodes = ( 'GOSP — Gas Oil Separation Plant', 'Stage separation unit / Stabilization unit',
    #'Demister', 'Free Water Knock-Out vessel — FWKO', 'Oil Treatment Facility (OTF)',
        #'Desulfurization'
      'Storage tank battery / LACT unit (Lease Automatic Custody Transfer)', 
      'Gas lease unit'

      )
    links = [ ( 1, 1, False ), ( 2, 1, True ), ( 2, 2, False ), ( 3, 2, True ), ( 3, 3, False ), ( 4, 3, True ),
              ( 5, 4, False ), ( 6, 4, True )
    ]

    for p in products:
        new_product = Product( full_name = p,
                               out_cost = 0
                      )
        session.add(new_product)
        session.commit()


    for n in nodes:
        new_node = Node_Type( full_name = n,
                              value = random.randint(1, 100),
                              power = random.randint(1, 100000),
                              capex_cost = random.randint(1, 1000),
                              opex_cost = random.randint(1, 100) )
        session.add(new_node)
        session.commit()

    for id_p, id_n, out_flag in links:
        new_ntp = Node_Type_Product(
            product_id = id_p,
            out_flag = out_flag,
            node_type_id = id_n,
            share = 500 )
        session.add(new_ntp)
        session.commit()


    new_project = Project(
          name = "Oil project",
          ininital_product_id = 1,
    #      #finit_product_id
          cost_coef = 5,
          power_cost = 2
      )
    session.add( new_project )
    session.commit()

    new_project = Project(
          name = "Gas project",
          ininital_product_id = 5,
    #      #finit_product_id
          cost_coef = 5,
          power_cost = 20
      )
    session.add( new_project )
    session.commit()
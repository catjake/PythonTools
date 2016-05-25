# import pygraphviz as pgv
# from subprocess import check_call
import pydot
from cStringIO import StringIO

import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def set_graph_attributes(p_obj_func, *xargs, **kwargs):
    if kwargs:
        p_obj = p_obj_func(*xargs, **kwargs)
    else:
        p_obj = p_obj_func(*xargs)
    return p_obj


def mk_tree(elements_dict=None, clusters_dict=None, **graph_kwargs):
    """
    elements_dict = {
        "element_name": (**attr, [element_attributes]), ...
    }
    element_attributes = (**attr, [attribs])
    attribs = str|list
    """
    elements_dict = elements_dict or {}
    clusters_dict = clusters_dict or {}
    G = pydot.Dot(**graph_kwargs)
    for element_name, (node_kwargs, element_attributes) in elements_dict.iteritems():
        G.add_node(set_graph_attributes(pydot.Node, *[element_name], **node_kwargs))
        if not isinstance(element_attributes, list):
            element_attributes = [element_attributes]
        for (edge_kwargs, attrib) in element_attributes:
            if not isinstance(attrib, list):
                attrib = [attrib]
            for sub_attrib in attrib:
                G.add_edge(set_graph_attributes(pydot.Edge, *[element_name, sub_attrib], **edge_kwargs))
    node_names_dict = {a_node.get_name(): a_node for a_node in G.get_node_list()}
    for cluster_name, (attribs, nodes) in sorted(clusters_dict.iteritems(), key=lambda x: x[0]):
        a_cluster = set_graph_attributes(pydot.Cluster, *[cluster_name], **attribs)
        for node_name in nodes:
            a_cluster.add_node(node_names_dict[node_name])
        G.add_subgraph(a_cluster)
    return G

def display_graph(pydot_graph):
    png_str = pydot_graph.create_png(prog="dot")
    # treat the dot output string as an image file
    sio = StringIO()
    sio.write(png_str)
    sio.seek(0)
    img = mpimg.imread(sio)
    #plot the image
    imgplot = plt.imshow(img, aspect="equal")
    plt.show(block=False)


def __debug_interactive_delete__():
    """
    import sandbox_graphviz
    from sandbox_graphviz import display_graph, mk_tree
    """
    pass


def main():
    # all with pydot
    top_level_nodes = ["ComponentName"]
    input_level_nodes = ["CadModel", "Static_Cad_Outputs", "Cad_Output_Parameters", "zodb_object"]
    element_level_nodes = ["Param_Assoc", "Cad_Output_Param"]
    param_input_level_nodes = ["type", "value", "to", "name"]
    cad_model_level_nodes = ["CadModelParamValue", "CadModelParamType", "CadModelParamName"]
    engine_level_nodes = ["db_field_data_type", "db_field_name", "db_field_value", ]
    output_level_nodes = ["AVM"]
    tree_dict = {
        "ComponentName": ({"group": "GroupA", "shape": "rect"},
                          [({"xlabel": "Creo File"}, "CadModel"),
                           ({}, "Cad_Output_Parameters"),
                           ({}, "Static_Cad_Outputs"),
                           ({}, "zodb_object")
                          ]),
        "AVM": ({"group": "GroupZ", "shape": "rect"},
                [({"dir": "back", "xlabel": "CadModelParamValue"}, "value"),
                 ({"dir": "back", "xlabel": "CadModelParamType"}, "type")]),
        "CadModel": ({"group": "GroupB", "style": "filled", "fillcolor": "palegreen"},
                         [({"color": "palegreen"}, "CadModelParamValue"),
                          ({"color": "palegreen"}, "CadModelParamType")]),
        "CadModelParamValue": ({"group": "GroupC", "style": "filled", "fillcolor": "palegreen"},
                          [({"color": "palegreen"}, "Cad_Output_Param")]),
        "CadModelParamName": ({"group": "GroupC", "style": "filled", "fillcolor": "palegreen"},
                         [({"color": "palegreen4"}, "CadModel")]),
        "CadModelParamType": ({"group": "GroupC", "style": "filled", "fillcolor": "palegreen"},
                         [({"color": "palegreen"}, "Cad_Output_Param")]),
        "zodb_object": ({}, []),
        "db_field_data_type": ({"group": "GroupE", }, [({"color": "aquamarine3", "dir": "both"}, "zodb_object")]),
        "db_field_name": ({"group": "GroupE", }, [({"color": "palegreen4"}, "zodb_object")]),
        "db_field_value": ({"group": "GroupE", }, [({"color": "powderblue"}, "zodb_object")]),
        "Static_Cad_Outputs": ({"group": "GroupC", "xlabel": "assoc_cad_instance_xml\nStatic_Cad_Outputs",
                                "style": "filled", "fillcolor": "palegreen4"},
                               [({"color": "palegreen4"}, "Param_Assoc")]),
        "Param_Assoc": ({"group": "GroupD", "style": "filled", "fillcolor": "palegreen4"},
                               [({"color": "palegreen4"}, "to"),
                                ({"color": "palegreen4"}, "name"),
                                ({"color": "palegreen4"}, "type")]),
        "Cad_Output_Parameters": ({"group": "GroupC", "xlabel": "cad_log_db_xml\nCad_Output_Parameters",
                                   "style": "filled", "fillcolor": "powderblue"},
                                  [({"color": "powderblue"}, "Cad_Output_Param")]),
        "Cad_Output_Param": ({"group": "GroupD", "xlabel": "CML_Physical_Quantity,\nCML_Mapping",
                              "style": "filled", "fillcolor": "powderblue"},
                                  [({"color": "powderblue"}, "type"),
                                   ({"color": "powderblue", "dir": "both"}, "name"),
                                   ({"color": "powderblue"}, "value")]),
        "to": ({"group": "GroupE", "style": "filled", "fillcolor": "palegreen4"},
               [({"color": "palegreen4"}, "db_field_name")]),
        "value": ({"group": "GroupE", "style": "filled", "fillcolor": "powderblue"},
                  [({"color": "powderblue"}, "db_field_value")]),
        "type": ({"group": "GroupE", "style": "filled", "fillcolor": "aquamarine3"},
                 [({"color": "aquamarine3"}, "db_field_data_type")]),
        "name": ({"group": "GroupE", "style": "filled", "fillcolor": "aquamarine3"},
                 [({"color": "palegreen4"}, "CadModelParamName")])
    }
    tree_clusters = {
        "000_TopLevelCluster": ({"style": "invis"}, top_level_nodes),
        "001_InputLevelCluster": ({"style": "invis"}, input_level_nodes),
        "002_ElementLevelCluster": ({}, element_level_nodes),
        "003_ParamInputLevelCluster": ({}, param_input_level_nodes),
        "004_CadModelLevelCluster": ({}, cad_model_level_nodes),
        "005_EngineLevelCluster": ({}, engine_level_nodes),
        "006_OutputLevelCluster": ({}, output_level_nodes),
    }
    G = mk_tree(tree_dict, tree_clusters, graph_type="digraph", outputMode="edgesfirst", splines="ortho", rankdir="TB")
    G = mk_tree(tree_dict, graph_type="digraph", outputMode="edgesfirst", splines="ortho", rankdir="TB")
    # display_graph(G)
    G.write("FullPicture.png", format="png")
    debug_str = """from pycharm, ctrl+alt+e to execute in python console:
        G.write("example2.dot", format="dot")
        chk_list = G.create(format="plain")
    """
    top_level_dict = {
        "Cad_Output_Parameters":({"color": "blue4", "label": "cad_db_xml\nCad_Output_Parameters"},
                                 [({}, "Cad_Db_ParamName"), ({}, "Cad_Db_ParamType"), ({}, "Cad_Db_ParamValue")]),
        "Static_Cad_Outputs":({"color": "darkgreen", "label": "assoc_cad_instance_xml\nStatic_Cad_Outputs"},
                              [({}, "to"), ({"dir": "both"}, "name"), ({"dir": "both"}, "type")]),
        "name": ({"color": "cyan"}, [({}, "Cad_Db_ParamName")]),
        "to": ({"color": "darkgreen"}, [({}, "zodb_field_name")]),
        "type": ({"color": "cyan"}, [({}, "zodb_field_data_type"),
                                          ({"dir": "both"}, "Cad_Db_ParamType")]),
        "value": ({"color": "blue4"}, [({}, "zodb_field_value"),
                                       ({"dir": "back"}, "Cad_Db_ParamValue")]),
        "Cad_Db_Model": ({"color": "blue"}, [({}, "Cad_Db_ParamType"), ({}, "Cad_Db_ParamValue")]),
        "Cad_Db_ParamName": ({"color": "blue"}, [({}, "Cad_Db_Model")]),
        "Cad_Db_ParamType": ({"color": "blue"}, []),
        "Cad_Db_ParamValue": ({"color": "blue"}, []),
        "Zodb_Instance":({}, [({"dir": "back"}, "zodb_field_name"),
                              ({"dir": "back"}, "zodb_field_data_type"),
                              ({"dir": "back"}, "zodb_field_value")]),
        "zodb_field_value": ({"color": "blue4"}, []),
        "zodb_field_data_type": ({"color": "cyan"}, []),
        "zodb_field_name": ({"color": "darkgreen"}, []),
        }
    G = mk_tree(top_level_dict)
    G.write("HighLevel.png", format="png")


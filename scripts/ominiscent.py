#   /--------------------------------------------------------------------------------------------------------------\
#   --------------------------------------------------] OMINISCENT [------------------------------------------------
#   \--------------------------------------------------------------------------------------------------------------/
#   
#    A script used to perform simple optimization tasks on a few parameters used thoughout the code, for the 
#    simulation of the freight train aerodynamics. The approach adopted is that of sequential and proogressive optimization of
#    the parameters: we will try to explore the parameter spaces, considering those one by one,first optimizing the most 
#    important parameters and then moving on to the less important ones. 
#    This, in general, won't allow to find the global minimum, but it will considerably reduce the complexity of the problem 
#    and the time required to solve it. In this regard, no gradient-based optimization method will be used, nor end-to-end 
#    training will be performed, also due to the lack of a proper dataset, i.e a proper solution for each problem/case
#    explored during the optimization process.
#
#    The optimization of the paramethers, in general, is carried out by plotting the results of the simulations and choosing
#    best parameters by considering the trade-off between the computational time and the accuracy of the results. The script
#    will also provide a few plots to show the results of the simulations and the optimization process, while trying to provide
#    also the best choice for the parameters.
#    
#    The parameters to be optimized are:
#    - the dimensions of the box (length, width, height)
#    - the dimension for a sigle (lower lever) cell
#    - the number of refinement blocks
#    - the dimension for the refinement blocks
#    - the rotation/not rotation of the refinment blocks
#
# The general outline for the script it the following: it will run a few simulations by changing a single parameter at a time,
# while keeping the others fixed. The results of the simulations will be plotted and the best choice for the parameter will be
# chosen. The process will be repeated for all the parameters to be optimized. To do so, the script will rely on also on the 
# ./Allrun script

import os


# Dafault case

box = [(-1.268, 0, -1.22), (2.812, 0, -1.22), (2.812, 1.3, -1.22), (-1.268, 1.3, -1.22),
         (-1.268, 0, 1.22), (2.812, 0, 1.22), (2.812, 1.3, 1.22), (-1.268, 1.3, 1.22)]
cells = [40, 13, 24]
refinement_boxes = [["true", 2, (3.612, 0.5, 1), -0.9, -0.5],["true", 3, (3.1, 0.4, 0.7), -0.65, -0.35],["true", 4, (2.6, 0.3, 0.55), -0.55, -0.3],["false", 5 , (2.2, 0.25, 0.4),-0.4 , -0.25]]
refinement_train = ["false", 0.07, 5]

# Function to trasform the box data structures into strings
# es box = [(-1.268, 0, -1.22), (2.812, 0, -1.22), (2.812, 1.3, -1.22), (-1.268, 1.3, -1.22),...] becomes
# "{(-1.268 0 -1.22), (2.812 0 -1.22), (2.812 1.3 -1.22), (-1.268 1.3 -1.22),...}"
def box_string(l):
    s = "\"{"
    for i in range(len(l)):
        s += "(" + str(l[i][0]) + " " + str(l[i][1]) + " " + str(l[i][2]) + ")"
        if i != len(l) - 1:
            s += ", "
    s += "}\""
    return s

#Function to transform the refinement_boxes data structures into strings
# es refinement_boxes = [["true", 2, (3.612, 0.5, 1), -0.9, -0.5],["true", 3, (3.1, 0.4, 0.7), -0.65, -0.35],["true", 4, (2.6, 0.3, 0.55), -0.55, -0.3],["false", 5 , (2.2, 0.25, 0.4),-0.4 , -0.25]] becomes
# "{{true, 2, (3.612 0.5 1), -0.9, -0.5}, {true, 3, (3.1 0.4 0.7), -0.65, -0.35}, {true, 4, (2.6 0.3 0.55), -0.55, -0.3}, {false, 5, (2.2 0.25 0.4), -0.4, -0.25}}"
def refinement_boxes_string(l):
    s = "\"" 
    for i in range(len(l)):
        s += "{" + l[i][0] + ", " + str(l[i][1]) + ", (" + str(l[i][2][0]) + " " + str(l[i][2][1]) + " " + str(l[i][2][2]) + "), " + str(l[i][3]) + ", " + str(l[i][4]) + "}"
        if i != len(l) - 1:
            s += "; "
    s += "\""
    return s

# Function to transform the refinement_train data structures into strings
# es refinement_train = ["false", 0.07, 5] becomes "{false, 0.07, 5}"
def refinement_train_string(l):
    s = "\"{" + l[0] + ", " + str(l[1]) + ", " + str(l[2]) + "}\""
    return s

# Function t transform the cells data structures into strings
# es cells = [40, 13, 24] becomes "{40, 13, 24}"
def cells_string(l):
    s = "\"{"
    for i in range(len(l)):
        s += str(l[i])
        if i != len(l) - 1:
            s += ", "
    s += "}\""
    return s

# Function to call the allrun script given the list of parametersn on local
def run_simulation_local(box, cells, refinement_boxes, refinement_train, PATH = "../simulation/Allrun"):
    # Convert the data structures into strings
    box = box_string(box)
    cells = cells_string(cells)
    refinement_boxes = refinement_boxes_string(refinement_boxes)
    refinement_train = refinement_train_string(refinement_train)
    # Call the allrun script givin the parameters (strings) as arguments to the options
    # ./Allrun -b box -c cells -r refinement_boxes -t refinement_train
    print("Fino a qui tutto bene")
    os.system(PATH + " -b " + box + " -c " + cells + " -r " + refinement_boxes + " -t " + refinement_train)

# Function to call the allrun script given the list of parametersn on the cluster
def run_simulation_cluster(box, cells, refinement_boxes, refinement_train, PATH = "/home/meccanica/ecabiati/freight_train_CFD/simulation/train_run_single.sh"):
    # Convert the data structures into strings
    box = box_string(box)
    cells = cells_string(cells)
    refinement_boxes = refinement_boxes_string(refinement_boxes)
    refinement_train = refinement_train_string(refinement_train)
    # Call the allrun script givin the parameters (strings) as arguments to the options
    # ./Allrun -b box -c cells -r refinement_boxes -t refinement_train
    os.system("qsub " + PATH + " -b " + box + " -c " + cells + " -r " + refinement_boxes + " -t " + refinement_train)

# ===============================================================================================================================


print("Running the simulation with the current parameters:")
print("*--------------------------------------------------------------------------------*")
print("Box: ", box_string(box))
print("Cells: ", cells_string(cells))
print("Refinement boxes: ", refinement_boxes_string(refinement_boxes))
print("Refinement train: ", refinement_train_string(refinement_train))
print("*--------------------------------------------------------------------------------*")
# Run the simulation with the current parameters
run_simulation_cluster(box, cells, refinement_boxes, refinement_train)

# Substitute the coordinates of the vertices
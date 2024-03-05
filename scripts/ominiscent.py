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
import sys
import getopt


# Dafault case

box = [(-1., 0, -1.25), (5, 0, -1.25), (5, 1.5, -1.25), (-1., 1.5, -1.25),
         (-1., 0, 1.25), (5, 0, 1.25), (5, 1.5, 1.25), (-1., 1.5, 1.25)]
cells = [80, 40, 24]
refinement_boxes = [["true", 2, (3.5, 0.5, 0.8), -0.7, -0.5],["true", 3, (3., 0.4, 0.65), -0.65, -0.35],["true", 4, (2.6, 0.3, 0.4), -0.55, -0.3],["false", 5 , (2.2, 0.25, 0.35),-0.4 , -0.25]]
refinement_train = ["false", 0.07, 5]



# =================================================]* USE CASES *[=================================================

deltas = [0.3, 0.25, 0.2, 0.1, 0, -0.1, -0.2, -0.25, -0.3]
# Use case 1: BOXES
# Define a boxes list with different options for the box coordinates
# The box coordinates are defined as a list of 8 tuples, each containing the coordinates of a vertex of the box
# es box = [(-1.268, 0, -1.22), (2.812, 0, -1.22), (2.812, 1.3, -1.22), (-1.268, 1.3, -1.22),...]

boxes = []

for delta in deltas:
    box_temp = [(-1. + (-1)*delta, 0 , -1.25 + (-1.25)*delta), (5 + 5*delta, 0, -1.25 + (-1.25)*delta), (5 + 5*delta, 1.5 + delta, -1.25 + (-1.25)*delta), (-1. + (-1)*delta, 1.5 + delta, -1.25 + (-1.25)*delta),
                (-1. + (-1)*delta, 0, 1.25 + 1.25*delta), (5 + 5*delta, 0, 1.25 + 1.25*delta), (5 + 5*delta, 1.5 + delta, 1.25 + 1.25*delta), (-1. + (-1)*delta, 1.5 + delta, 1.25 + 1.25*delta)]
    boxes.append(box_temp)
            

# Use case 2: CELLS
    
cells = []

for delta in deltas:
    cells_temp = [80, 40, 24]
    cells_temp[0] = int(80 + 80*delta)
    cells_temp[1] = int(40 + 40*delta)
    cells_temp[2] = int(24 + 24*delta)
    cells.append(cells_temp)

# Use case 3: REFINEMENT BOXES
    
refinement_boxes= []

for delta in deltas:
    refinement_boxes_temp = [["true", 2, (3.5, 0.5, 0.8), -0.7, -0.5],["true", 3, (3., 0.4, 0.65), -0.65, -0.35],["true", 4, (2.6, 0.3, 0.4), -0.55, -0.30],["false", 5 , (2.2, 0.25, 0.35),-0.5 , -0.25]]
    for i in range(len(refinement_boxes_temp)):
        refinement_boxes_temp[i][2] = (refinement_boxes_temp[i][2][0] + refinement_boxes_temp[i][2][0]*delta, refinement_boxes_temp[i][2][1] + refinement_boxes_temp[i][2][1]*delta, refinement_boxes_temp[i][2][2] + refinement_boxes_temp[i][2][2]*delta)
        refinement_boxes_temp[i][3] = refinement_boxes_temp[i][3] + refinement_boxes_temp[i][3]*delta
        refinement_boxes_temp[i][4] = refinement_boxes_temp[i][4] + refinement_boxes_temp[i][4]*delta
    refinement_boxes.append(refinement_boxes_temp)

# Use case 4: REFINEMENT TRAIN

refinement_train = []

for delta in deltas:
    refinement_train_temp = ["true", 0.08, 5]
    refinement_train_temp[1] = refinement_train_temp[1] + refinement_train_temp[1]*delta
    refinement_train.append(refinement_train_temp)


# ===========================================]* UTILITIES *[========================================


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

# Function to extract the results of the simulation: the function shall take as input the path to a coefficient.dat file
# and return the values of the Cx, Cy and Cl coefficients at the end of the simulation
    
def extract_results(path, angle = 0, velocity = 20):
    # Define some constants for the computation of the coefficients
    A_ref = 0.00739277;	# Reference area
    rho = 1;        # Air density
    theta = angle;  # Angle of attack
    U= velocity;          # Freestream velocity
    p_dyn_f = 0.5*rho*U**2; # Dynamic pressure
    #Open up the file and read the lines
    f = open(path, "r")
    lines = f.readlines()
    # Dump the first 12 lines
    lines = lines[12:] 
    #Extract the values in the file
    # Time, Cd, Cd(f), Cd(r), Cl, Cl(f), Cl(r), CmPitch, CmRoll, CmYaw,	Cs, Cs(f),Cs(r)         
    # We are interested only in the values of the first 2:4 columns
    Fx = []
    Fy = []
    Fz = []

    for line in lines:
        line = line.split()
        Fx.append(float(line[1]))
        Fy.append(float(line[2]))
        Fz.append(float(line[3]))
    # Compute the coefficients
    Cx = []
    Cy = []
    Cl = []
    Cd = []
    for i in range(len(Fx)):
        Cx.append(Fx[i]/p_dyn_f/A_ref)
        Cy.append(Fy[i]/p_dyn_f/A_ref)
        Cl.append(Fz[i]/p_dyn_f/A_ref)
        Cd.append(Cx[i]**2 + Cy[i]**2)
    # Select the number of steps to consider for the computation of the mean value of the coefficients
    n = 100
    # Compute the mean value of the coefficients
    Cx_mean = sum(Cx[-n:])/n
    #Cy_mean = sum(Cy[-n:])/n
    #Cl_mean = sum(Cl[-n:])/n

    # Compute the standard deviation of the coefficients
    Cx_std = sum([(Cx[i] - Cx_mean)**2 for i in range(len(Cx[-n:]))])/n
    return Cx_mean, Cx_std
    

# Function to extract the times to perform the simulation on the log.time file 
def extract_times(path):
    # Open the file and read the lines
    f = open(path, "r")
    lines = f.readlines()
    # Extract the times:
    # SnappyHexMesh_Time: $execution_time
    # SimpleFoam_Time: $execution_time

    t = []
    for line in lines:
        if "SnappyHexMesh_Time" in line:
            t.append(float(line.split()[1]))
        if "SimpleFoam_Time" in line:
            t.append(float(line.split()[1]))
    
    return t[0]+t[1],t[0],t[1]



# ========================================================================================================



# ===================================================]* OPTIMIZATION ROUTINES *[=================================================

# Function to run the optimization of the box dimensions based on the use cases defined in the script

def run_optimization_box():
    print("*----------------------------------------------------------------------------------------*")
    print("*---------------------------------]* OPTIMIZING BOXES *[---------------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    for i in range(len(boxes)):
        
        print("                         <<<<<<< RUNNING BOX CASE n " +i+" >>>>>>>")
        print("Running the simulation with the current parameters:")
        print("*----------------------------------------------------------------------------------------*")
        print("Box: ", box_string(boxes[i]))
        print("Cells: ", cells_string(cells))
        print("Refinement boxes: ", refinement_boxes_string(refinement_boxes))
        print("Refinement train: ", refinement_train_string(refinement_train))
        print("*----------------------------------------------------------------------------------------*")
        # Run the simulation with the current parameters
        run_simulation_cluster(boxes[i], cells, refinement_boxes, refinement_train) 
        # Move the results of the simulation (in '/global-scratch/ecabiati/simulations') to '/global-scratch/ecabiati/results'
        os.system("mv /global-scratch/ecabiati/simulations/simulation/0.orig /global-scratch/ecabiati/results/box_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/box_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/box_case_" + str(i))
        # Run the allclean script to clean the simulation folder
        os.system("/global-scratch/ecabiati/simulations/simulation/Allclean")

# Function to run the optimization of the cells dimensions based on the use cases defined in the script

def run_optimization_cells():
    print("*----------------------------------------------------------------------------------------*")
    print("*---------------------------------]* OPTIMIZING CELLS *[---------------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    for i in range(len(cells)):
        print("                        <<<<<<< RUNNING CELLS CASE n " +i+" >>>>>>>")
        print("Running the simulation with the current parameters:")
        print("*--------------------------------------------------------------------------------*")
        print("Box: ", box_string(box))
        print("Cells: ", cells_string(cells[i]))
        print("Refinement boxes: ", refinement_boxes_string(refinement_boxes))
        print("Refinement train: ", refinement_train_string(refinement_train))
        print("*--------------------------------------------------------------------------------*")
        # Run the simulation with the current parameters
        run_simulation_cluster(box, cells[i], refinement_boxes, refinement_train)
        # Move the results of the simulation (in '/global-scratch/ecabiati/simulations') to '/global-scratch/ecabiati/results'
        os.system("mv /global-scratch/ecabiati/simulations/simulation/0.orig /global-scratch/ecabiati/results/cells_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/cells_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/cells_case_" + str(i))
        # Run the allclean script to clean the simulation folder
        os.system("/global-scratch/ecabiati/simulations/simulation/Allclean")
    

# Function to run the optimization of the refinement boxes based on the use cases defined in the script

def run_optimization_refinement_boxes():
    print("*----------------------------------------------------------------------------------------*")
    print("*--------------------------]* OPTIMIZING REFINEMENT BOXES *[-----------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    for i in range(len(refinement_boxes)):
        print("                        <<<<<<< RUNNING REFINEMENT BOXES CASE n " +i+" >>>>>>>")
        print("Running the simulation with the current parameters:")
        print("*--------------------------------------------------------------------------------*")
        print("Box: ", box_string(box))
        print("Cells: ", cells_string(cells))
        print("Refinement boxes: ", refinement_boxes_string(refinement_boxes[i]))
        print("Refinement train: ", refinement_train_string(refinement_train))
        print("*--------------------------------------------------------------------------------*")
        # Run the simulation with the current parameters
        run_simulation_cluster(box, cells, refinement_boxes[i], refinement_train)
        # Move the results of the simulation (in '/global-scratch/ecabiati/simulations') to '/global-scratch/ecabiati/results'
        os.system("mv /global-scratch/ecabiati/simulations/simulation/0.orig /global-scratch/ecabiati/results/refinement_boxes_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/refinement_boxes_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/refinement_boxes_case_" + str(i))
        # Run the allclean script to clean the simulation folder
        os.system("/global-scratch/ecabiati/simulations/simulation/Allclean")

    

# Function to run the optimization of the refinement train based on the use cases defined in the script
        
def run_optimization_refinement_train():
    print("*----------------------------------------------------------------------------------------*")
    print("*--------------------------]* OPTIMIZING REFINEMENT TRAIN *[-----------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    for i in range(len(refinement_train)):
        print("                        <<<<<<< RUNNING REFINEMENT TRAIN CASE n " +i+" >>>>>>>")
        print("Running the simulation with the current parameters:")
        print("*--------------------------------------------------------------------------------*")
        print("Box: ", box_string(box))
        print("Cells: ", cells_string(cells))
        print("Refinement boxes: ", refinement_boxes_string(refinement_boxes))
        print("Refinement train: ", refinement_train_string(refinement_train[i]))
        print("*--------------------------------------------------------------------------------*")
        # Run the simulation with the current parameters
        run_simulation_cluster(box, cells, refinement_boxes, refinement_train[i])
        # Move the results of the simulation (in '/global-scratch/ecabiati/simulations') to '/global-scratch/ecabiati/results'
        os.system("mv /global-scratch/ecabiati/simulations/simulation/0.orig /global-scratch/ecabiati/results/refinement_train_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/refinement_train_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/refinement_train_case_" + str(i))
        # Run the allclean script to clean the simulation folder
        os.system("/global-scratch/ecabiati/simulations/simulation/Allclean")



# Define the general function to perform the optimization, based on the results of the use cases and their time of execution
# The function will return the best choice for the parameters, based on the trade-off between the computational time and the accuracy of the results
        
def optimize(optimization_case):
    match optimization_case:
        case "box":
            
        case "cells":
            run_optimization_cells()
        case "refinement_boxes":
            run_optimization_refinement_boxes()
        case "refinement_train":
            run_optimization_refinement_train()
        case _:
            print("Invalid optimization case")
            sys.exit(2)
# ===============================================================================================================================

# Now parse the options to the python scipt and run the optimization process based on those:
# -b : optimization of on the box dimensions (based on the use cases defined in the script)
# -c : optimization of the cells dimensions (based on the use cases defined in the script)
# -r : optimization of the refinement boxes (based on the use cases defined in the script)
# -t : optimization of the refinement train (based on the use cases defined in the script)
    
#Parse the options
def main(argv):
    try:
        opts, args = getopt.getopt(argv, "b:c:r:t:", ["box=", "cells=", "refinement_boxes=", "refinement_train="])
    except getopt.GetoptError:
        print("ominiscent.py -b <box> -c <cells> -r <refinement_boxes> -t <refinement_train>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-b", "--box"):
            print("Optimizing the box dimensions")
            # Run the optimization of the box dimensions
            run_optimization_box()
        elif opt in ("-c", "--cells"):
            print("Optimizing the cells dimensions")
            # Run the optimization of the cells dimensions
            run_optimization_cells()
        elif opt in ("-r", "--refinement_boxes"):
            print("Optimizing the refinement boxes")
            # Run the optimization of the refinement boxes
            run_optimization_refinement_boxes()
        elif opt in ("-t", "--refinement_train"):
            print("Optimizing the refinement train")
            # Run the optimization of the refinement train
            run_optimization_refinement_train()

# print("Running the simulation with the current parameters:")
# print("*--------------------------------------------------------------------------------*")
# print("Box: ", box_string(box))
# print("Cells: ", cells_string(cells))
# print("Refinement boxes: ", refinement_boxes_string(refinement_boxes))
# print("Refinement train: ", refinement_train_string(refinement_train))
# print("*--------------------------------------------------------------------------------*")
# # Run the simulation with the current parameters
# run_simulation_cluster(box, cells, refinement_boxes, refinement_train)

# Substitute the coordinates of the vertices
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

box_0 = [(-1., 0, -1.25), (5, 0, -1.25), (5, 1.5, -1.25), (-1., 1.5, -1.25),
         (-1., 0, 1.25), (5, 0, 1.25), (5, 1.5, 1.25), (-1., 1.5, 1.25)]
cells_0 = [80, 40, 24]
refinement_boxes_0 = [["true", 2, (3.5, 0.5, 0.8), -0.7, -0.5],["true", 3, (3., 0.4, 0.65), -0.65, -0.35],["true", 4, (2.6, 0.3, 0.4), -0.55, -0.3],["false", 5 , (2.2, 0.25, 0.35),-0.4 , -0.25]]
refinement_train_0 = ["false", 0.07, 5]



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
    # Move to the simulation folder
    os.chdir("../simulation")
    # Convert the data structures into strings
    box = box_string(box)
    cells = cells_string(cells)
    refinement_boxes = refinement_boxes_string(refinement_boxes)
    refinement_train = refinement_train_string(refinement_train)
    # Call the allrun script givin the parameters (strings) as arguments to the options
    # ./Allrun -b box -c cells -r refinement_boxes -t refinement_train
    os.system(PATH + " -b " + box + " -c " + cells + " -r " + refinement_boxes + " -t " + refinement_train)

# Function to call the allrun script given the list of parametersn on the cluster
def run_simulation_cluster(box, cells, refinement_boxes, refinement_train, PATH = "/home/meccanica/ecabiati/freight_train_CFD/simulation/train_run_scratch.sh"):
    # Move to the simulation folder
    os.chdir("/home/meccanica/ecabiati/freight_train_CFD/simulation")
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
    # Time, total_x, total_y, total_z,	pressure_x, pressure_y, pressure_z,	viscous_x, viscous_y, viscous_z         
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


# A test function to extract the results of the simulation and times
def test(path_results, path_times):
    # Extract the results
    Cx, Cx_std = extract_results(path_results)
    print("Cx: ", Cx)
    print("Cx_std: ", Cx_std)
    # Extract the times
    total_time, mesh_time, foam_time = extract_times(path_times)
    print("Total time: ", total_time)
    print("Mesh time: ", mesh_time)
    print("Foam time: ", foam_time)
    return Cx, Cx_std, total_time, mesh_time, foam_time



# ========================================================================================================



# ===================================================]* OPTIMIZATION ROUTINES *[=================================================

# Function to run the optimization of the box dimensions based on the use cases defined in the script

def run_box():
    os.system('''
    echo "*----------------------------------------------------------------------------------------*"
    echo "*---------------------------------]* OPTIMIZING BOXES *[---------------------------------*"
    echo "*----------------------------------------------------------------------------------------*"
    ''')
    # for i in range(len(boxes)):
        
    #     print("                         <<<<<<< RUNNING BOX CASE n " +i+" >>>>>>>")
    #     print("Running the simulation with the current parameters:")
    #     print("*----------------------------------------------------------------------------------------*")
    #     print("Box: ", box_string(boxes[i]))
    #     print("Cells: ", cells_string(cells))
    #     print("Refinement boxes: ", refinement_boxes_string(refinement_boxes))
    #     print("Refinement train: ", refinement_train_string(refinement_train))
    #     print("*----------------------------------------------------------------------------------------*")
    #     # Run the simulation with the current parameters
    #     run_simulation_cluster(boxes[i], cells, refinement_boxes, refinement_train) 
    #     # Move the results of the simulation (in '/global-scratch/ecabiati/simulations') to '/global-scratch/ecabiati/results'
    #     os.system("mv /global-scratch/ecabiati/simulations/simulation/0.orig /global-scratch/ecabiati/results/box_case_" + str(i))
    #     os.system("mv /global-scratch/ecabiati/simulations/simulation/constant /global-scratch/ecabiati/results/box_case_" + str(i))
    #     os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/box_case_" + str(i))
    #     os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/box_case_" + str(i))
    #     # Remove the simulation folder
    #     os.system("rm -r /global-scratch/ecabiati/simulations/simulation")
    #     # Run the allclean script to clean the /home/meccanica/ecabiati/freight_train_CFD/simulation folder
    #     os.system("/home/meccanica/ecabiati/freight_train_CFD/simulation/Allclean")
        
        # Import the different cases into a list in shell
    
    for i in range(len(boxes)):
        box_s = box_string(boxes[i])
        os.environ["box_"+str(i)] = box_s[i]
    cells_s = cells_string(cells_0)
    refinement_boxes_s = refinement_boxes_string(refinement_boxes_0)
    refinement_train_s = refinement_train_string(refinement_train_0)
    # Export the variables to the shell
    os.environ["Ncases"] = str(len(boxes)-1)
    os.environ["cells"] = cells_s
    os.environ["refinement_boxes"] = refinement_boxes_s
    os.environ["refinement_train"] = refinement_train_s

    os.system('''
        for i in {0..$Ncases}; do
            echo "Running the simulation with the current parameters:"
            echo "*--------------------------------------------------------------------------------*"
            echo "Box: ${box_$i}"
            echo "Cells: $cells"
            echo "Refinement boxes: $refinement_boxes"
            echo "Refinement train: $refinement_train"
            echo "*--------------------------------------------------------------------------------*"
            # Move to the simulation folder
            cd /home/meccanica/ecabiati/freight_train_CFD/simulation
            # Run the simulation with the current parameters
            qsub train_run_scratch.sh -b {box_$i} -c $cells -r $refinement_boxes -t $refinement_train
            mv /global-scratch/ecabiati/simulations/simulation/0.orig /global-scratch/ecabiati/results/box_case_$i
            mv /global-scratch/ecabiati/simulations/simulation/constant /global-scratch/ecabiati/results/box_case_$i
            mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/box_case_$i
            mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/box_case_$i
            rm -r /global-scratch/ecabiati/simulations/simulation
            /home/meccanica/ecabiati/freight_train_CFD/simulation/Allclean
        done

    ''')

    # Clean the environment
    os.environ["box_@"] = ""
    os.environ["cells"] = ""
    os.environ["refinement_boxes"] = ""
    os.environ["refinement_train"] = ""
    # 
    
    # DO ACTUAL OPTIMIZATION HERE

# Function to run the optimization of the cells dimensions based on the use cases defined in the script

def run_cells():
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
        os.system("mv /global-scratch/ecabiati/simulations/simulation/constant /global-scratch/ecabiati/results/cells_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/cells_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/cells_case_" + str(i))
        # Remove the simulation folder
        os.system("rm -r /global-scratch/ecabiati/simulations/simulation")
        # Run the allclean script to clean the /home/meccanica/ecabiati/freight_train_CFD/simulation folder
        os.system("/home/meccanica/ecabiati/freight_train_CFD/simulation/Allclean")
    # DO ACTUAL OPTIMIZATION HERE
    

# Function to run the optimization of the refinement boxes based on the use cases defined in the script

def run_refinement_box():
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
        os.system("mv /global-scratch/ecabiati/simulations/simulation/constant /global-scratch/ecabiati/results/refinement_boxes_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/refinement_boxes_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/refinement_boxes_case_" + str(i))
        # Remove the simulation folder
        os.system("rm -r /global-scratch/ecabiati/simulations/simulation")
        # Run the allclean script to clean the /home/meccanica/ecabiati/freight_train_CFD/simulation folder
        os.system("/home/meccanica/ecabiati/freight_train_CFD/simulation/Allclean")
    # DO ACTUAL OPTIMIZATION HERE

    

# Function to run the optimization of the refinement train based on the use cases defined in the script
        
def run_refinement_train():
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
        os.system("mv /global-scratch/ecabiati/simulations/simulation/postProcessing /global-scratch/ecabiati/results/refinement_train_case_" + str(i))
        os.system("mv /global-scratch/ecabiati/simulations/simulation/logs /global-scratch/ecabiati/results/refinement_train_case_" + str(i))
        # Remove the simulation folder
        os.system("rm -r /global-scratch/ecabiati/simulations/simulation")
        # Run the allclean script to clean the /home/meccanica/ecabiati/freight_train_CFD/simulation folder
        os.system("/home/meccanica/ecabiati/freight_train_CFD/simulation/Allclean")



# Define the general function to perform the optimization, based on the results of the use cases and their time of execution
# The function will return the best choice for the parameters, based on the trade-off between the computational time and the accuracy of the results
        
def optimize(optimization_case):
    # Define a list to store the results of the simulations
    results = []
    # Define a list to store the times of the simulations
    times = []
    # Define a list to store the best choice for the parameters
    best_choice = []
    # Run the optimization based on the use cases
    if optimization_case == "box":
        run_box()
    elif optimization_case == "cells":
        run_cells()
    elif optimization_case == "refinement_boxes":
        run_refinement_box()
    elif optimization_case == "refinement_train":
        run_refinement_train()
    # Extract the results and the times of the simulations
    for i in range(len(use_cases)):
        # Extract the results
        Cx, Cx_std = extract_results("/global-scratch/ecabiati/results/" + optimization_case + "_case_" + str(i) + "/postProcessing/forces1/0/force.dat")
        # Extract the times
        total_time, mesh_time, foam_time = extract_times("/global-scratch/ecabiati/results/" + optimization_case + "_case_" + str(i) + "/logs/log.time")
        # Append the results and the times to the lists
        results.append([Cx, Cx_std])
        times.append([total_time, mesh_time, foam_time])

    # Choose the best choice for the parameters based on the trade-off between the computational time and the accuracy of the results
    # For each use case, we define a score which purpouse is to give a measure of the trade-off between the computational time and the accuracy of the results:
    # - first term of the score: the computational time multiplied by a constant aplha (to be defined)
    # - second term of the score: the difference between the Cx and a reference value, computed as the mean value of the Cx over all the use cases, weighted by a factor 1 + deltas[i] (1-delta[i] if case = "box")
    
    # Define the reference value for the Cx
    if optimization_case == "box":
        ref_Cx = sum([results[i][0]*(1-deltas[i]) for i in range(len(results))])/len(results)
    else:
        ref_Cx = sum([results[i][0]*(1+deltas[i]) for i in range(len(results))])/len(results)
    
    alpha = 100
    # Compute the scores
    scores = []
    for i in range(len(results)):
        scores.append(times[i][0]*alpha + 1/abs(results[i][0] - ref_Cx))
    
    # Choose the best choice for the parameters based on the scores
    best_choice = scores.index(min(scores))
    print("The best choice for the parameters is delta = ", deltas[best_choice])

    return best_choice
# ===============================================================================================================================

# Now parse the options to the python scipt and run the optimization process based on those:
# -b : optimization of on the box dimensions (based on the use cases defined in the script)
# -c : optimization of the cells dimensions (based on the use cases defined in the script)
# -r : optimization of the refinement boxes (based on the use cases defined in the script)
# -t : optimization of the refinement train (based on the use cases defined in the script)
    
#Parse the options
# def main(argv):
#     try:
#         opts, args = getopt.getopt(argv, "b:c:r:t:", ["box=", "cells=", "refinement_boxes=", "refinement_train="])
#     except getopt.GetoptError:
#         print("ominiscent.py -b <box> -c <cells> -r <refinement_boxes> -t <refinement_train>")
#         sys.exit(2)
#     for opt, arg in opts:
#         if opt in ("-b", "--box"):
#             print("Optimizing the box dimensions")
#             # Run the optimization of the box dimensions
#             run_box()
#         elif opt in ("-c", "--cells"):
#             print("Optimizing the cells dimensions")
#             # Run the optimization of the cells dimensions
#             run_cells()
#         elif opt in ("-r", "--refinement_boxes"):
#             print("Optimizing the refinement boxes")
#             # Run the optimization of the refinement boxes
#             run_refinement_box()
#         elif opt in ("-t", "--refinement_train"):
#             print("Optimizing the refinement train")
#             # Run the optimization of the refinement train
#             run_optimization_refinement_train()

# Test run_simulation_cluster

run_box()


#   /--------------------------------------------------------------------------------------------------------------\
#   --------------------------------------------------]   OSCENT   [------------------------------------------------
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
#    The script will need to be called multiple times, after each bacth of simulations, to perform the optimization of the
#    chosen parameters. It will then require to modify the standard parameters used to perform the successive simulations to 
#    to one use case deemed to be the best choice for the parameters.
#
#    The optimization of the paramethers, in general, is carried out by plotting the results of the simulations and choosing
#    best parameters by considering the trade-off between the computational time and the accuracy of the results. The script
#    will try to mimic this process by running the simulations and choosing the best parameters based an empirical algorithm
#    of our choosing.
#    
#    The parameters to be optimized are:
#    - the dimensions of the box (length, width, height)
#    - the dimension for a sigle (lower lever) cell
#    - the number of refinement blocks
#    - the dimension for the refinement blocks
#    PLEASE NOTE: the parameters that could be optimized are not limited to the ones listed above. Still, as to keep the
#    complexity of the problem low, we will just consider the optimization to the parameters listed above. Nonetheless, the
#    structure of the script can be easily extended to consider more parameters.
#
# The general outline for the script it the following: it will run a few simulations by changing a single parameter at a time,
# while keeping the others fixed. The results for the different simulations will be store and the best choice for the chosed
# parameter will be derived. The process will be repeated for all the parameters to be optimized. To do so, the script will 
# rely on also on the parametric ./Allrun script

import os
import sys
import getopt
import math


# Dafault case

box_0 = [(-1.27, 0, -1.25), (3.7, 0, -1.25), (3.7, 1.5, -1.25), (-1.27, 1.5, -1.25),
         (-1.27, 0, 1.25), (3.7, 0, 1.25), (3.7, 1.5, 1.25), (-1.27, 1.5, 1.25)]
cells_0 = [90, 45, 27]
refinement_boxes_0 = [["true", 2, (4.1, 0.7, 1.4), -0.77, -0.6],["true", 3, (3.4, 0.5, 0.8), -0.47, -0.4],["true", 4, (2.9, 0.35, 0.5), -0.37, -0.25],["false", 5 , (2.5, 0.2, 0.3),-0.27 ,-0.15]]
refinement_train_0 = ["false", 0.07, 5]


# =================================================]* USE CASES *[=================================================

deltas = [0.3, 0.25, 0.2, 0.1, 0, -0.1, -0.2, -0.25, -0.3]
# Use case 1: BOXES
# Define a boxes list with different options for the box coordinates
# The box coordinates are defined as a list of 8 tuples, each containing the coordinates of a vertex of the box
# es box = [(-1.268, 0, -1.22), (2.812, 0, -1.22), (2.812, 1.3, -1.22), (-1.268, 1.3, -1.22),...]

boxes = []

for delta in deltas:
    box_temp = []
    for i in range(len(box_0)):
        box_temp.append((box_0[i][0] + box_0[i][0]*delta, box_0[i][1] + box_0[i][1]*delta, box_0[i][2] + box_0[i][2]*delta))    
    boxes.append(box_temp)


            

# Use case 2: CELLS
    
cells = []

for delta in deltas:
    cells_temp = []
    for i in range(len(cells_0)):
        cells_temp.append(cells_0[i] + cells_0[i]*delta)
    cells.append(cells_temp)

# Use case 3: REFINEMENT BOXES
    
refinement_boxes= []

for delta in deltas:
    refinement_boxes_temp = []
    for i in range(len(refinement_boxes_0)):
        refinement_boxes_temp.append([refinement_boxes_0[i][0], 
                                      refinement_boxes_0[i][1], 
                                      (refinement_boxes_0[i][2][0] + refinement_boxes_0[i][2][0]*delta, refinement_boxes_0[i][2][1] + refinement_boxes_0[i][2][1]*delta, refinement_boxes_0[i][2][2] + refinement_boxes_0[i][2][2]*delta),
                                        refinement_boxes_0[i][3] + refinement_boxes_0[i][3]*delta,
                                        refinement_boxes_0[i][4] + refinement_boxes_0[i][4]*delta
                                    ])
    refinement_boxes.append(refinement_boxes_temp)

# Use case 4: REFINEMENT TRAIN

refinement_train = []

for delta in deltas:
    refinement_train_temp = []
    for i in range(len(refinement_train_0)):
        if i == 1:
            refinement_train_temp.append(refinement_train_0[i] + refinement_train_0[i]*delta)
        else:
            refinement_train_temp.append(refinement_train_0[i])
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
    
def extract_results(path, n_0 = 150, angle = 0, velocity = 20):
    # Define some constants for the computation of the coefficients
    A_ref = 0.00739277;	# Reference area
    rho = 1;        # Air density
    theta = angle;  # Angle of attack
    U= velocity;          # Freestream velocity
    p_dyn_f = 0.5*rho*U**2; # Dynamic pressure
    # If the file is not found, return an error
    if not os.path.exists(path):
        print("File:"+ path + " not found")
        return -1
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
    n = n_0
    # Compute the mean value of the coefficients
    Cx_mean = sum(Cx[-n:])/n
    #Cy_mean = sum(Cy[-n:])/n
    #Cl_mean = sum(Cl[-n:])/n

    # Compute the standard deviation of the coefficients
    Cx_std = sum([(Cx[i] - Cx_mean)**2 for i in range(len(Cx[-n:]))])/n
    return Cx_mean, Cx_std
    

# Function to extract the times to perform the simulation on the log.time file 
def extract_times(path):
    # If the file is not found, return an error
    if not os.path.exists(path):
        print("File:"+ path + " not found")
        return -1
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

def run_box(boxes, cells_0, refinement_boxes_0, refinement_train_0):
    os.system('''
    echo "*----------------------------------------------------------------------------------------*"
    echo "*---------------------------------]* OPTIMIZING BOXES *[---------------------------------*"
    echo "*----------------------------------------------------------------------------------------*"
    ''')
    # Import the different cases into a list in shell
    # Create a list for the boxes
    for i in range(len(boxes)):
        os.environ["box_" + str(i)] = box_string(boxes[i])
    os.environ["Ncases"] = str(len(boxes)-1)
    os.environ["cells"] = cells_string(cells_0)
    os.environ["refinement_boxes"] = refinement_boxes_string(refinement_boxes_0)
    os.environ["refinement_train"] = refinement_train_string(refinement_train_0)
    
    # Run the simulation with the current parameters
    os.system('''
    for i in $(seq 0 $Ncases); do
        box="box_$i"
        echo "                             <<<<<<< RUNNING BOX CASE n $i >>>>>>>"
        echo "Running the simulation with the current parameters:"
        echo "*--------------------------------------------------------------------------------*"
        echo "Box: ${!box}"
        echo "Cells: $cells"
        echo "Refinement boxes: $refinement_boxes"
        echo "Refinement train: $refinement_train"
        echo "*--------------------------------------------------------------------------------*"
        # Append the command to a job file
        echo "qsub /home/meccanica/ecabiati/freight_train_CFD/simulation/train_run_scratch.sh -n $box -b ${!box} -c $cells -r $refinement_boxes -t $refinement_train" >> job_file
    done     
    ''')
    
    # Clean the environment
    for i in range(len(boxes)):
        os.environ["box_" + str(i)] = ""
    os.environ["cells"] = ""
    os.environ["refinement_boxes"] = ""
    os.environ["refinement_train"] = ""

# Function to run the optimization of the cells dimensions based on the use cases defined in the script

def run_cells(box_0, cells, refinement_boxes_0, refinement_train_0):
    print("*----------------------------------------------------------------------------------------*")
    print("*---------------------------------]* OPTIMIZING CELLS *[---------------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    # Import the different cases into a list in shell
    # Create a list for the cells
    for i in range(len(cells)):
        os.environ["cells_" + str(i)] = cells_string(cells[i])
    os.environ["Ncases"] = str(len(cells)-1)
    os.environ["box"] = box_string(box_0)
    os.environ["refinement_boxes"] = refinement_boxes_string(refinement_boxes_0)
    os.environ["refinement_train"] = refinement_train_string(refinement_train_0)

    # Run the simulation with the current parameters
    os.system('''
    for i in $(seq 0 $Ncases); do
        cells="cells_$i"
        echo "                             <<<<<<< RUNNING CELLS CASE n $i >>>>>>>"
        echo "Running the simulation with the current parameters:"
        echo "*--------------------------------------------------------------------------------*"
        echo "Box: $box"
        echo "Cells: ${!cells}"
        echo "Refinement boxes: $refinement_boxes"
        echo "Refinement train: $refinement_train"
        echo "*--------------------------------------------------------------------------------*"
        # Append the command to a job file
        echo "qsub /home/meccanica/ecabiati/freight_train_CFD/simulation/train_run_scratch.sh -n $cells -b $box -c ${!cells} -r $refinement_boxes -t $refinement_train" >> job_file
    done
    ''')


    # Clean the environment
    for i in range(len(cells)):
        os.environ["cells_" + str(i)] = ""
    os.environ["box"] = ""
    os.environ["refinement_boxes"] = ""
    os.environ["refinement_train"] = ""
    

# Function to run the optimization of the refinement boxes based on the use cases defined in the script
def run_refinement_box(box_0, cells_0, refinement_boxes, refinement_train_0):
    print("*----------------------------------------------------------------------------------------*")
    print("*--------------------------]* OPTIMIZING REFINEMENT BOXES *[-----------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    # Import the different cases into a list in shell
    # Create a list for the refinement boxes
    for i in range(len(refinement_boxes)):
        os.environ["refinement_boxes_" + str(i)] = refinement_boxes_string(refinement_boxes[i])
    os.environ["Ncases"] = str(len(refinement_boxes)-1)
    os.environ["box"] = box_string(box_0)
    os.environ["cells"] = cells_string(cells_0)
    os.environ["refinement_train"] = refinement_train_string(refinement_train_0)

    # Run the simulation with the current parameters
    os.system('''
    for i in $(seq 0 $Ncases); do
        refinement_boxes="refinement_boxes_$i"
        echo "                             <<<<<<< RUNNING REFINEMENT BOXES CASE n $i >>>>>>>"
        echo "Running the simulation with the current parameters:"
        echo "*--------------------------------------------------------------------------------*"
        echo "Box: $box"
        echo "Cells: $cells"
        echo "Refinement boxes: ${!refinement_boxes}"
        echo "Refinement train: $refinement_train"
        echo "*--------------------------------------------------------------------------------*"
        # Append the command to a job file
        echo "qsub /home/meccanica/ecabiati/freight_train_CFD/simulation/train_run_scratch.sh -n $refinement_boxes -b $box -c $cells -r ${!refinement_boxes} -t $refinement_train" >> job_file
    done
    ''')

    # Clean the environment
    for i in range(len(refinement_boxes)):
        os.environ["refinement_boxes_" + str(i)] = ""
    os.environ["box"] = ""
    os.environ["cells"] = ""
    os.environ["refinement_train"] = ""
    

# Function to run the optimization of the refinement train based on the use cases defined in the script
        
def run_refinement_train(box_0, cells_0, refinement_boxes_0, refinement_train):
    print("*----------------------------------------------------------------------------------------*")
    print("*--------------------------]* OPTIMIZING REFINEMENT TRAIN *[-----------------------------*")
    print("*----------------------------------------------------------------------------------------*")
    # Import the different cases into a list in shell
    # Create a list for the refinement train
    for i in range(len(refinement_train)):
        os.environ["refinement_train_" + str(i)] = refinement_train_string(refinement_train[i])
    os.environ["Ncases"] = str(len(refinement_train)-1)
    os.environ["box"] = box_string(box_0)
    os.environ["cells"] = cells_string(cells_0)
    os.environ["refinement_boxes"] = refinement_boxes_string(refinement_boxes_0)

    # Run the simulation with the current parameters
    os.system('''
    for i in $(seq 0 $Ncases); do
        refinement_train="refinement_train_$i"
        echo "                             <<<<<<< RUNNING REFINEMENT TRAIN CASE n $i >>>>>>>"
        echo "Running the simulation with the current parameters:"
        echo "*--------------------------------------------------------------------------------*"
        echo "Box: $box"
        echo "Cells: $cells"
        echo "Refinement boxes: $refinement_boxes"
        echo "Refinement train: ${!refinement_train}"
        echo "*--------------------------------------------------------------------------------*"
        # Append the command to a job file
        echo "qsub /home/meccanica/ecabiati/freight_train_CFD/simulation/train_run_scratch.sh -n $refinement_train -b $box -c $cells -r $refinement_boxes -t ${!refinement_train}" >> job_file
    done
    ''')

    # Clean the environment
    for i in range(len(refinement_train)):
        os.environ["refinement_train_" + str(i)] = ""
    os.environ["box"] = ""
    os.environ["cells"] = ""
    os.environ["refinement_boxes"] = ""

# Define the general function to perform the optimization, based on the results of the use cases and their time of execution
# The function will return the best choice for the parameters, based on the trade-off between the computational time and the accuracy of the results
def run_cases(optimization_case, box_0 = box_0, cells_0 = cells_0, refinement_boxes_0 = refinement_boxes_0, refinement_train_0 = refinement_train_0, boxes = boxes, cells = cells, refinement_boxes= refinement_boxes, refinement_train = refinement_train):
    # Create the job file to be executed
    os.system("touch /home/meccanica/ecabiati/freight_train_CFD/simulation/job_file")
    os.system("chmod +x /home/meccanica/ecabiati/freight_train_CFD/simulation/job_file")
    # The job file will contain the commands to run the simulations
    os.system("echo \"#!/bin/bash\" >> job_file")
    os.system("cd /home/meccanica/ecabiati/freight_train_CFD/simulation")

    # Run the optimization based on the use cases
    if optimization_case == "box":
        run_box(boxes, cells_0, refinement_boxes_0, refinement_train_0)
    elif optimization_case == "cells":
        run_cells(box_0, cells, refinement_boxes_0, refinement_train_0)
    elif optimization_case == "refinement_boxes":
        run_refinement_box(box_0, cells_0, refinement_boxes, refinement_train_0)
    elif optimization_case == "refinement_train":
        run_refinement_train(box_0, cells_0, refinement_boxes_0, refinement_train)
    # Exxecute the job file
    os.system('''
    /home/meccanica/ecabiati/freight_train_CFD/simulation/job_file
    ''')

    # Remove the job file
    os.system("rm /home/meccanica/ecabiati/freight_train_CFD/simulation/job_file")

def optimize(optimization_case,use_cases,deltas):
    # Define a list to store the results of the simulations
    results = []
    # Define a list to store the times of the simulations
    times = []
    # Define a list to store the best choice for the parameters
    best_choice = []
    # Extract the results and the times of the simulations
    for i in range(len(use_cases)):
        # Extract the results
        Cx, Cx_std = extract_results("/global-scratch/ecabiati/simulations/results/" + optimization_case + "_" + str(i) + "/postProcessing/forces1/0/force.dat")
        # Extract the times
        total_time, mesh_time, foam_time = extract_times("/global-scratch/ecabiati/simulations/results/" + optimization_case + "_" + str(i) + "/logs/log.time")
        # Append the results and the times to the lists
        results.append([Cx, Cx_std])
        times.append([total_time, mesh_time, foam_time])

    # Choose the best choice for the parameters based on the trade-off between the computational time and the accuracy of the results
    # For each use case, we define a score which purpouse is to give a measure of the trade-off between the computational time and the accuracy of the results:
    # - first term: the logarithm of the total time of the simulation
    # - second term: a measure of the difference between the results and the reference value for the Cx
    # Define the reference value for the Cx
    if optimization_case == "box":
        ref_Cx = sum([results[i][0]*(1.-deltas[i]) for i in range(len(results))])/sum([1.-deltas[i] for i in range(len(results))])
    else:
        ref_Cx = sum([results[i][0]*(1.+deltas[i]) for i in range(len(results))])/sum([1.+deltas[i] for i in range(len(results))])
    print("The reference value for the Cx is: ", ref_Cx)
    # Define the constant alpha
    alpha = 150

    # Compute the scores
    scores = []
    for i in range(len(use_cases)):
        scores.append(math.log(times[i][0]) + alpha * abs(results[i][0] - ref_Cx))

    # Print a summary of the scores for the use cases, divided in the two terms of the score: we use a tabular format
    # Clip to the 2nd decimal digit
    print("Use case |  Time  | Cx | First_Term | Second_Term | Score")
    for i in range(len(use_cases)):
        print(i, "   |", round(times[i][0],2), "|", round(results[i][0],2), "|", round(math.log(times[i][0]),2), "|", round(alpha * abs(results[i][0] - ref_Cx),2), "|", round(scores[i],2))
    
    
    # Choose the best choice for the parameters based on the scores
    best_choice = scores.index(min(scores))
    print("The best delta is: ", deltas[best_choice])
    print("The best choice for the choosen parameter is: ", use_cases[best_choice])

    return best_choice
# ===============================================================================================================================

# Move to the simulation folder
os.chdir("/home/meccanica/ecabiati/freight_train_CFD/simulation")

# The main function shall parse the options ( two options: either run a batch of simulations or optimize the parameters on the 
# previously run simulations) and call the appropriate functions

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hb:o:",["batch=","optimize="])
    except getopt.GetoptError:
        print("ominiscent.py -b <case> -o <optimize>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("ominiscent.py -b <case> -o <optimize>")
            print(" - b <case> : run a batch of simulations for the case <case>")
            print(" - o <optimize> : optimize the parameters based on the results of the simulations")
            sys.exit()
        elif opt in ("-b", "--batch"):
            print("Running a batch of simulations on the case: ", arg)
            if arg == "box" or arg == "cells" or arg == "refinement_boxes" or arg == "refinement_train":
                run_cases(arg)
            else:
                print("Invalid case: ", arg, " please choose one of the following cases: box, cells, refinement_boxes, refinement_train")
                sys.exit(2)
        elif opt in ("-o", "--optimize"):
            print("Optimizing the parameters based on the results of the simulations for the case: ", arg)
            if arg == "box":
                best_choice = optimize(arg,boxes,deltas)
            elif arg == "cells":
                best_choice = optimize(arg,cells,deltas)
            elif arg == "refinement_boxes":
                best_choice = optimize(arg,refinement_boxes,deltas)
            elif arg == "refinement_train":
                best_choice = optimize(arg,refinement_train,deltas)
            else:
                print("Invalid case: ", arg, " please choose one of the following cases: box, cells, refinement_boxes, refinement_train")
                sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])

# ===============================================================================================================================
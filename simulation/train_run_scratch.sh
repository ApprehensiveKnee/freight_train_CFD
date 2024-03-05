#!/bin/bash             # use bash as command interpreter
#$ -cwd
#$ -N freight_train           # jobName
#$ -j y                 # merges output and errors
#$ -S /bin/bash         # scripting language
#$ -l h_rt=1:00:00      # jobDuration hh:mm:ss
#$ -q all.q             # queueName
#$ -pe mpi 32           # cpuNumber

process=32

# /----------------------------------------------------------------------------\
#                             USAGE OF THIS SCRIPT:
# The script is used to run the simulation. It allows the user to set some parameters
# to be used in the simulation. These parameters shall be passed as arguments to the script.
# Parameters:
# 1. The first parameter is a flag to indicate whether the simulation should be run 
#   with the train angulated or not. The default value is false.
# 2. The second parameter is the angle to be used for the simulation. The default value is 0.
# 3. The third parameter is a flag to indicate whether the gallery should be included in the 
#   simulation. The default value is false.
# 4. The fourth parameter is a flag to indicate whether the refinement boxes should be rotated.
#   The default value is false. This last parameter was added to the script since it would allow
#   for a better constructed mesh even in the eventuality that the case considered is rotated.
# \----------------------------------------------------------------------------/

# Define the local directory where the simulation is run
localDir='/home/meccanica/ecabiati/freight_train_CFD'
scratchDir='"$scratchDir"'
name="simulation"
case_name="train"

echo "Start Parallel Run":

echo "- Importing OpenFOAM"

source "/home/meccanica/ecabiati/.openfoam_modules"

echo "- Preparing the simulation environment..."

# Copy the case to "$scratchDir"/ inside a directory named after the string passed as the first argument to the script
echo "- Copying the case to the global scratch space..."
cp -r "$localDir"/simulation "$scratchDir"
# Remove the Allrun, Allrun_autoangle and train_run_single.sh files from the simulation directory
rm -f "$scratchDir"/"$name"/Allrun
rm -f "$scratchDir"/"$name"/Allrun_autoangle
rm -f "$scratchDir"/"$name"/train_run_local.sh
rm -f "$scratchDir"/"$name"/train_run_scratch.sh
rm -f "$scratchDir"/"$name"/Allclean
# Make the constant/triSurface directory if it does not exist
mkdir -p "$scratchDir"/"$name"/constant/triSurface

# cp -f \
#     "$scratchDir"/objects/motrice_rescaled.stl \
#     constant/triSurface/

cp -f \
    "$localDir"/objects/box_galleria.stl \
    "$scratchDir"/"$name"/constant/triSurface/

cp -f \
    "$localDir"/objects/frontInternalWall.stl \
    "$scratchDir"/"$name"/constant/triSurface/   

cp -f \
    "$localDir"/objects/backInternalWall.stl \
    "$scratchDir"/"$name"/constant/triSurface/

cp -f \
    "$localDir"/objects/train.stl \
    "$scratchDir"/"$name"/constant/triSurface/



# Move to the global scratch space
cd "$scratchDir"/"$name"

# ----------------------------* PARAMETER PARSING *--------------------------
# Define some default values
angulation_flag="false"
angle_value=0
gallery_included="false"
rotated_refinement="false"

OPTSTRING="n:av:gor:t:b:c:"

# Copy the original refinementParameters_0 (template) file to the refinementParameters file
cp 0.orig/include/refinementParameters_0 0.orig/include/refinementParameters
cp 0.orig/include/angulationParameters_0 0.orig/include/angulationParameters
cp 0.orig/include/blockParameters_0 0.orig/include/blockParameters

# Parse the arguments passed to the script
while getopts ${OPTSTRING} opt; do
  case $opt in
    n)
        # Use this option to later move the simulation results to a directory named after the case name
        name_case="$OPTARG"
    ;;
    a) 
        angulation_flag="true"
        echo "The angulation flag is set to: $angulation_flag"
         
    ;;
    v) 
        angle_value="$OPTARG"
        echo "The angle is $angle_value"
    ;;
    g) 
        gallery_included="true"
        echo "The gallery is included in the simulation: $gallery_included"
    ;;
    o) 
        rotated_refinement="true"
        echo "The refinement boxes are rotated: $rotated_refinement"
    ;;
    r) # This case is used to parse the refinement box parameters
        # We need to parse as input a string with the following format:
        #"{REFINEMENT_BOX_N,REFINEMENT_LEVEL_N,(SPAN_N_x SPAN_N_y SPAN_N_z),orig_N0_x,oirg_N0_z},..."
        # example: "{{true,2,(0.1 0.1 0.1),0,0},{false,1,(0.1 0.1 0.1),0,0}}"
        # where N is the number of the refinement box
        # and orig_N0_x and orig_N0_z are the coordinates of the origin of the refinement box
        # and SPAN_N is the span of the refinement box
        # The string is parsed and the values are saved in the refinementParameters file
        # by replacing the placeholders with the actual values

        echo "=========================* REFINEMENT - BOXES *========================="

        echo "The refinement boxes included in the simulation at hand  are:"

        # Parse the string, split it by the ; character and save the result in an array.
        # Then iterate over each element of the array and extract the values of the refinement box represented by the element of the array
        # Note that the index of the array is the number of the refinement box, while the first token extracted from each element of the array
        # is a flag to indicate whether the refinement box is included in the simulation or not.
        IFS=';' read -ra refinementBoxes <<< "$OPTARG"
        for i in "${!refinementBoxes[@]}"; do
            IFS=',' read -ra refinementBox <<< "${refinementBoxes[i]//[\{\}]/}"
            echo "REFINEMENT_BOX_$i is included in the simulation: ${refinementBox[0]}"
            echo "Refinement level for box $i is: ${refinementBox[1]}"
            echo "Span for box $i is: ${refinementBox[2]}"
            echo "Origin_x for box $i is: ${refinementBox[3]}"
            echo "Origin_z for box $i is: ${refinementBox[4]}"

            # Replace the placeholders in the refinementParameters file with the actual values and save the result in the refinementParameters file
            sed -i "s/REFINEMENT_BOX_PLACEHOLDER_$i/${refinementBox[0]}/g" "0.orig/include/refinementParameters"
            sed -i "s/REFINEMENT_LEVEL_PLACEHOLDER_$i/${refinementBox[1]}/g" "0.orig/include/refinementParameters"
            sed -i "s/SPAN_PLACEHOLDER_$i/${refinementBox[2]}/g" "0.orig/include/refinementParameters"
            sed -i "s/ORIG_X_PLACEHOLDER_$i/${refinementBox[3]}/g" "0.orig/include/refinementParameters"
            sed -i "s/ORIG_Z_PLACEHOLDER_$i/${refinementBox[4]}/g" "0.orig/include/refinementParameters"
        done

        # In case a refinement box is excluded from the simulation, (refinementBoxes[i] is not in the refinementBoxes array),
        # we need to replace the placeholders in the refinementParameters file with some default values:
        # there are up to 4 refinement boxes in the simulation

        for i in {0..3}; do
            if [ -z "${refinementBoxes[i]}" ]; then
                echo "${refinementBoxes[i]}"
                echo "REFINEMENT_BOX_$i is included in the simulation: false  --- NO DEFINITION GIVEN"
                # Replace the placeholders in the refinementParameters file with the actual values and save the result in the refinementParameters file
                sed -i "s/REFINEMENT_BOX_PLACEHOLDER_$i/false/g" "0.orig/include/refinementParameters"
                sed -i "s/REFINEMENT_LEVEL_PLACEHOLDER_$i/1/g" "0.orig/include/refinementParameters"
                sed -i "s/SPAN_PLACEHOLDER_$i/(0.1 0.1 0.1)/g" "0.orig/include/refinementParameters"
                sed -i "s/ORIG_X_PLACEHOLDER_$i/0/g" "0.orig/include/refinementParameters"
                sed -i "s/ORIG_Z_PLACEHOLDER_$i/0/g" "0.orig/include/refinementParameters"
            fi
        done

        echo "========================================================================"
        
    ;;
    t)  # The option lets insert the parameters to define eventual refinement at a certain distance from the train
        # The string is parsed and the values are saved in the refinementParameters file
        # by replacing the placeholders with the actual values
        # The format of the string is the following:
        # {REFINEMENT_TRAIN_PLACHOLDER, REFINEMENT_DISTANCE_PLACEHOLDER, REFINEMENT_LEVEL_TRAIN_PLACEHOLDER}
        echo "=========================* REFINEMENT - TRAIN *========================="
        
        OPTARG=${OPTARG//[\{\}]/}

        IFS=',' read -ra refinementTrain <<< "$OPTARG"
        echo " Refinement of the train is included in the simulation: ${refinementTrain[0]}"
        echo " Refinement distance from the train is: ${refinementTrain[1]}"
        echo " Refinement level for the train is: ${refinementTrain[2]}"

        # Replace the placeholders in the refinementParameters file with the actual values and save the result in the refinementParameters file
        sed -i "s/REFINEMENT_TRAIN_PLACEHOLDER/${refinementTrain[0]}/g" "0.orig/include/refinementParameters"
        sed -i "s/REFINEMENT_DISTANCE_PLACEHOLDER/${refinementTrain[1]}/g" "0.orig/include/refinementParameters"
        sed -i "s/REFINEMENT_LEVEL_TRAIN_PLACEHOLDER/${refinementTrain[2]}/g" "0.orig/include/refinementParameters"

        echo "========================================================================"

    ;;
    b)
        # The option lets insert the parameters to define the dimensions of the block mesh
        # The string is parsed and the values are saved in the blockMeshDict file
        # by replacing the placeholders with the actual values
        # The format of the string is the following ):
        #{ OUTER_0, OUTER_1, OUTER_2, ...} 
        # example: {(-1.268 0 -1.22),(2.812 0 -1.22), (2.812 1.3 -1.22), (-1.268 1.3 -1.22), (-1.268  0 1.22),(2.812  0 1.22) , (2.812  0 1.22), (2.812  0 1.22)}
        # To run the simulation, the option would require 8 vertices: the correcteness is left to the user.
        # Yet, some default values are set in the blockMeshDict file if no value for the vertices is given.
        echo "=============================* BLOCK MESH *============================="
        
        OPTARG=${OPTARG//[\{\}]/}

        IFS=',' read -ra blockMeshVertices <<< "$OPTARG"
        echo "The vertices of the block mesh are:"
        for i in "${!blockMeshVertices[@]}"; do
            echo "OUTER_$i: ${blockMeshVertices[i]}"
        done
        # Replace the placeholders in the blockMeshDict file with the actual values and save the result in the blockMeshDict file
        for i in "${!blockMeshVertices[@]}"; do
            sed -i "s/OUTER_PLACEHOLDER_$i/${blockMeshVertices[i]}/g" "0.orig/include/blockParameters"
        done

        echo "========================================================================"

    ;;
    c) 
        # The option lets insert the parameters to define the dimensions for the cells at the lowest level of refinement in the blockMesh
        # The string is parsed and the values are saved in the blockMeshDict file
        # by replacing the placeholders with the actual values
        # The format of the string is the following ):
        #{ NCELLS_X, NCELLS_Y, NCELLS_Z}
        #{40, 13, 24}

        echo "=============================* NUM. CELLS *============================="

        OPTARG=${OPTARG//[\{\}]/}

        IFS=',' read -ra blockMeshCells <<< "$OPTARG"
        echo "The number of cells at the lowest level of refinement in the block mesh are:"
        echo "${blockMeshCells[@]}"
        # Replace the placeholders in the blockMeshDict file with the actual values and save the result in the blockMeshDict file
        for i in "${!blockMeshCells[@]}"; do
            sed -i "s/NCELLS_PLACEHOLDER_$i/${blockMeshCells[i]}/g" "0.orig/include/blockParameters"
        done

        echo "========================================================================"

    ;;
    :)
        echo "Option -${OPTARG} requires an argument."
        exit 1
    ;;
    \?) 
        echo "Invalid option -$OPTARG" >&2
        exit 1
    ;;
  esac
done

#Handle the case in which no refinement boxes are given by setting default values in the refinementParameters file
if [ -z "${refinementBoxes[0]}" ]; then
    echo "The refinement boxes included in the simulation at hand  are:  --- NO DEFINITION GIVEN"
    # Replace the placeholders in the refinementParameters file with the actual values and save the result in the refinementParameters file
    for i in {0..3}; do
        sed -i "s/REFINEMENT_BOX_PLACEHOLDER_$i/false/g" "0.orig/include/refinementParameters"
        sed -i "s/REFINEMENT_LEVEL_PLACEHOLDER_$i/1/g" "0.orig/include/refinementParameters"
        sed -i "s/SPAN_PLACEHOLDER_$i/(0.1 0.1 0.1)/g" "0.orig/include/refinementParameters"
        sed -i "s/ORIG_X_PLACEHOLDER_$i/0/g" "0.orig/include/refinementParameters"
        sed -i "s/ORIG_Z_PLACEHOLDER_$i/0/g" "0.orig/include/refinementParameters"
    done
fi

#Handle the case in which no train refinement is required by settin default values in the refinementParameters file
if [ -z "${refinementTrain[0]}" ]; then
    echo "Refinement of the train is included in the simulation: false  --- NO DEFINITION GIVEN"
    # Replace the placeholders in the refinementParameters file with the actual values and save the result in the refinementParameters file
    sed -i "s/REFINEMENT_TRAIN_PLACEHOLDER/false/g" "0.orig/include/refinementParameters"
    sed -i "s/REFINEMENT_DISTANCE_PLACEHOLDER/0/g" "0.orig/include/refinementParameters"
    sed -i "s/REFINEMENT_LEVEL_TRAIN_PLACEHOLDER/1/g" "0.orig/include/refinementParameters"
fi

#Handle the case in which no block mesh vertices are given by setting default values in the blockMeshDict file
if [ -z "${blockMeshVertices[0]}" ]; then
    echo "The vertices of the block mesh are:  --- NO DEFINITION GIVEN"
    # Replace the placeholders in the blockMeshDict file with the actual values and save the result in the blockMeshDict file
    
    sed -i "s/OUTER_PLACEHOLDER_0/(-1.268 0 -1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_1/(2.812 0 -1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_2/(2.812 1.3 -1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_3/(-1.268 1.3 -1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_4/(-1.268 0 1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_5/(2.812 0 1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_6/(2.812 1.3 1.22)/g" "0.orig/include/blockParameters"
    sed -i "s/OUTER_PLACEHOLDER_7/(-1.268 1.3 1.22)/g" "0.orig/include/blockParameters"
fi

#Handle the case in which no block mesh cells are given by setting default values in the blockMeshDict file
if [ -z "${blockMeshCells[0]}" ]; then
    echo "The number of cells at the lowest level of refinement in the block mesh are:  --- NO DEFINITION GIVEN"
    # Replace the placeholders in the blockMeshDict file with the actual values and save the result in the blockMeshDict file
    sed -i "s/NCELLS_PLACEHOLDER_0/40/g" "0.orig/include/blockParameters"
    sed -i "s/NCELLS_PLACEHOLDER_1/13/g" "0.orig/include/blockParameters"
    sed -i "s/NCELLS_PLACEHOLDER_2/24/g" "0.orig/include/blockParameters"
fi



if [[ $angulation_flag == "false" && $angle_value != "0" ]]; then
  echo "Error - The angle value is not 0 but the angulation flag is set to false. Please set the angulation flag to true or set the angle value to 0."
  exit 1
fi


# Replace the boundary type values of the placeholders in the blockParameters file based on the angulation flag
if [ "$angulation_flag" = true ]; then
    sed -i "s/FRONTWALLTYPE_PLACEHOLDER/patch/g" "0.orig/include/blockParameters"
    sed -i "s/BACKWALLTYPE_PLACEHOLDER/patch/g" "0.orig/include/blockParameters"
else
    sed -i "s/FRONTWALLTYPE_PLACEHOLDER/symmetryPlane/g" "0.orig/include/blockParameters"
    sed -i "s/BACKWALLTYPE_PLACEHOLDER/symmetryPlane/g" "0.orig/include/blockParameters"

fi

sed -i "s/ANGULATION_FLAG_PLACEHOLDER/$angulation_flag/g" "0.orig/include/angulationParameters"
sed -i "s/ANGULATION_ANGLE_PLACEHOLDER/$angle_value/g" "0.orig/include/angulationParameters"
sed -i "s/GALLERY_BOX_FLAG_PLACEHOLDER/$gallery_included/g" "0.orig/include/angulationParameters"
sed -i "s/ROTATE_REFINEMENT_FLAG_PLACEHOLDER/$rotated_refinement/g" "0.orig/include/angulationParameters"

##############################################################################


# Rotate the box_galleria.stl file by an angle specified in the 0.orig/include/angulationParameters filen along the y axis (also translate the box_galleria.stl file to the origin)
# Also suppress the output of the surfaceTransformPoints command
# Do all this only if the gallery is included in the simulation

if [ "$gallery_included" = true ]; then
    surfaceTransformPoints -translate "(-0.5 0 -0.25)" -rollPitchYaw "(0 ${2:-0} 0)" constant/triSurface/box_galleria.stl constant/triSurface/box_galleria.stl > /dev/null

    # Do the same for the front and back internal planes
    surfaceTransformPoints -translate "(-60 0 0.25)" -rollPitchYaw "(0 ${2:-0} 0)" constant/triSurface/frontInternalWall.stl constant/triSurface/frontInternalWall.stl > /dev/null
    surfaceTransformPoints -translate "(-60 0 -0.25)" -rollPitchYaw "(0 ${2:-0} 0)" constant/triSurface/backInternalWall.stl constant/triSurface/backInternalWall.stl > /dev/null
fi


# ----------------------------* ACTUALLY RUN THE CODE *--------------------------


echo "=========================* RUNNING THE SIMULATION *========================="



#Create the logs directory if it does not exist
mkdir -p "$scratchDir"/"$name"/logs

echo "- Meshing..."

# Run the applications and return the log files to the logs directory

surfaceFeatureExtract >& "$scratchDir"/"$name"/log.surfaceFeatureExtract

blockMesh >& "$scratchDir"/"$name"/log.blockMesh

decomposePar >& "$scratchDir"/"$name"/log.decomposePar

# Using distributedTriSurfaceMesh?
if foamDictionary -entry geometry -value system/snappyHexMeshDict | \
   grep -q distributedTriSurfaceMesh
then
    echo "surfaceRedistributePar does not need to be run anymore"
    echo " - distributedTriSurfaceMesh will do on-the-fly redistribution"
fi

# Time snappyHexMesh and save the time to a log file
start_time=$(date +%s.%N)  # Get the start time in seconds with nanoseconds precision
mpirun --hostfile machinefile.$JOB_ID -np $process snappyHexMesh -overwrite -parallel  >& "$scratchDir"/"$name"/log.snappyHexMesh
end_time=$(date +%s.%N)  # Get the end time in seconds with nanoseconds precision
execution_time=$(echo "$end_time - $start_time" | bc)  # Calculate the execution time
echo "SnappyHexMesh_Time: $execution_time" >> "$scratchDir"/"$name"/log.time  # Write the execution time to the log.time file

mpirun --hostfile machinefile.$JOB_ID -np $process topoSet -parallel >& "$scratchDir"/"$name"/log.topoSet

mpirun --hostfile machinefile.$JOB_ID -np $process createPatch -parallel -overwrite >& "$scratchDir"/"$name"/log.createPatch

echo "- Running the simulation..."
# restore the 0/ directory from the 0.orig/ directory inside each processor directory
\ls -d processor* | xargs -I {} rm -rf ./{}/0
\ls -d processor* | xargs -I {} cp -r 0.orig ./{}/0 #> /dev/null 2>&1

mpirun --hostfile machinefile.$JOB_ID -np $process patchSummary -parallel >& "$scratchDir"/"$name"/log.patchSummary

mpirun --hostfile machinefile.$JOB_ID -np $process potentialFoam -parallel -writephi >& "$scratchDir"/"$name"/log.potentialFoam

mpirun --hostfile machinefile.$JOB_ID -np $process checkMesh -parallel -writeFields '(nonOrthoAngle)' -constant >& "$scratchDir"/"$name"/log.checkMesh

# Time simpleFoam and append the time to log.time
start_time=$(date +%s.%N)  # Get the start time in seconds with nanoseconds precision
mpirun --hostfile machinefile.$JOB_ID -np $process simpleFoam -parallel >& "$scratchDir"/"$name"/log.simpleFoam
end_time=$(date +%s.%N)  # Get the end time in seconds with nanoseconds precision
execution_time=$(echo "$end_time - $start_time" | bc)  # Calculate the execution time
echo "SimpleFoam_Time: $execution_time" >> "$scratchDir"/"$name"/log.time  # Write the execution time to the log.time file

reconstructParMesh -constant >& "$scratchDir"/"$name"/log.reconstructParMesh

reconstructPar -latestTime >& "$scratchDir"/"$name"/log.reconstructPar

echo "========================================================================"

#Generate the train.foam file
touch "$scratchDir"/"$name"/train.foam

# Move all the log files to the logs directory
mv "$scratchDir"/"$name"/log.* "$scratchDir"/"$name"/logs
#------------------------------------------------------------------------------

echo "- End Parallel Run"

# Move the results of the simulation (in '"$scratchDir"/"$name"') to '/global-scratch/ecabiati/results'
# Create the results directory if it does not exist
mkdir -p "$scratchDir"/results/
mkdir -p "$scratchDir"/results/"$name_case"

echo "- Rerouting the results to the results directory and cleaning the simulation directory..."

mv "$scratchDir"/"$name"/0.orig "$scratchDir"/results/"$name_case"
mv "$scratchDir"/"$name"/constant "$scratchDir"/results/"$name_case"
mv "$scratchDir"/"$name"/postProcessing "$scratchDir"/results/"$name_case"
mv "$scratchDir"/"$name"/logs "$scratchDir"/results/"$name_case"

# Remove the simulation folder
rm -r "$scratchDir"/"$name"

# Run the allclean script to clean the /home/meccanica/ecabiati/freight_train_CFD/simulation folder
"$localDir"/simulation/Allclean


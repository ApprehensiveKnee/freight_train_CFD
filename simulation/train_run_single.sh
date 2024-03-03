#!/bin/bash             # use bash as command interpreter
#$ -cwd
#$ -N freight_train           # jobName
#$ -j y                 # merges output and errors
#$ -S /bin/bash         # scripting language
#$ -l h_rt=1:00:00      # jobDuration hh:mm:ss
#$ -q all.q             # queueName
#$ -pe mpi 16           # cpuNumber


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

echo "Moved inside $localDir/simulation"                               # Run from this directory

echo "Start Parallel Run":

echo "- Importing OpenFOAM"

source "/home/meccanica/ecabiati/.openfoam_modules"

echo "- Preparing the simulation environment..."


#cd "${0%/*}" || exit                                # Run from this directory
#. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions        # Tutorial run functions
#------------------------------------------------------------------------------
# Alternative decomposeParDict name:
#decompDict="-decomposeParDict system/decomposeParDict.6"
## Standard decomposeParDict name:
# unset decompDict

# copy train surface from resources directory
mkdir -p "$localDir"/simulation/constant/triSurface

cp -f \
    "$localDir"/objects/motrice_rescaled.stl \
    constant/triSurface/

cp -f \
    "$localDir"/objects/box_galleria.stl \
    constant/triSurface/

cp -f \
    "$localDir"/objects/frontInternalWall.stl \
    constant/triSurface/   

cp -f \
    "$localDir"/objects/backInternalWall.stl \
    constant/triSurface/

# Define some default values
angulation_flag="false"
angle_value="0"
gallery_included="false"
rotated_refinement="false"

OPTSTRING="av:go"

# Parse the arguments passed to the script
while getopts ${OPTSTRING} opt; do
  case $opt in
    a) angulation_flag="true"
    ;;
    v) angle_value="$OPTARG"
    ;;
    g) gallery_included="true"
    ;;
    o) rotated_refinement="true"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

if [[ $angulation_flag == "false" && $angle_value != "0" ]]; then
  echo "Error - The angle value is not 0 but the angulation flag is set to false. Please set the angulation flag to true or set the angle value to 0."
  exit 1
fi

echo "The angulation flag is $angulation_flag"
echo "The angle is $angle_value"
echo "The gallery is included in the simulation: $gallery_included"
echo "The refinement boxes are rotated: $rotated_refinement"

# Replace the placeholder in the angulationParameters_0 file with the actual value and save the result in the angulationParameters file
sed "s/ANGULATION_ANGLE_PLACEHOLDER/$angle_value/g" "0.orig/include/angulationParameters_0"> \0.orig/include/angulationParameters
sed -i "s/ANGULATION_FLAG_PLACEHOLDER/$angulation_flag/g" "0.orig/include/angulationParameters" 
sed -i "s/GALLERY_FLAG_PLACEHOLDER/$gallery_included/g" "0.orig/include/angulationParameters"
sed -i "s/REFINEMENT_BOXES_ROTATION_FLAG_PLACEHOLDER/$rotated_refinement/g" "0.orig/include/angulationParameters"

# Rotate the box_galleria.stl file by an angle specified in the 0.orig/include/angulationParameters filen along the y axis (also translate the box_galleria.stl file to the origin)
# Also suppress the output of the surfaceTransformPoints command
# Do all this only if the gallery is included in the simulation

if [ "$gallery_included" = true ]; then
    surfaceTransformPoints -translate "(-0.5 0 -0.25)" -rollPitchYaw "(0 ${2:-0} 0)" constant/triSurface/box_galleria.stl constant/triSurface/box_galleria.stl > /dev/null

    # Do the same for the front and back internal planes
    surfaceTransformPoints -translate "(-60 0 0.25)" -rollPitchYaw "(0 ${2:-0} 0)" constant/triSurface/frontInternalWall.stl constant/triSurface/frontInternalWall.stl > /dev/null
    surfaceTransformPoints -translate "(-60 0 -0.25)" -rollPitchYaw "(0 ${2:-0} 0)" constant/triSurface/backInternalWall.stl constant/triSurface/backInternalWall.stl > /dev/null
fi


#Create the logs directory if it does not exist
mkdir -p "$localDir"/simulation/logs

echo "- Meshing..."

# Run the applications and return the log files to the logs directory

surfaceFeatureExtract >& "$localDir"/simulation/log.surfaceFeatureExtract

blockMesh >& "$localDir"/simulation/log.blockMesh

decomposePar >& "$localDir"/simulation/log.decomposePar

# Using distributedTriSurfaceMesh?
# if foamDictionary -entry geometry -value system/snappyHexMeshDict | \
#    grep -q distributedTriSurfaceMesh
# then
#     echo "surfaceRedistributePar does not need to be run anymore"
#     echo " - distributedTriSurfaceMesh will do on-the-fly redistribution"
# fi

mpirun --hostfile machinefile.$JOB_ID snappyHexMesh -parallel -overwrite >& "$localDir"/simulation/log.snappyHexMesh

mpirun --hostfile machinefile.$JOB_ID topoSet -parallel >& "$localDir"/simulation/log.topoSet

mpirun --hostfile machinefile.$JOB_ID cretePatch -parallel -overwrite >& "$localDir"/simulation/log.createPatch

echo "- Running the simulation..."
# restore the 0/ directory from the 0.orig/ directory inside each processor directory
\ls -d processor* | xargs -I {} rm -rf ./{}/0
\ls -d processor* | xargs -I {} cp -r 0.orig ./{}/0 #> /dev/null 2>&1

mpirun --hostfile machinefile.$JOB_ID patchSummary -parallel >& "$localDir"/simulation/log.patchSummary

mpirun --hostfile machinefile.$JOB_ID potentialFoam -parallel -writephi >& "$localDir"/simulation/log.potentialFoam

mpirun --hostfile machinefile.$JOB_ID checkMesh -parallel -writeFields '(nonOrthoAngle)' -constant >& "$localDir"/simulation/log.checkMesh

mpirun --hostfile machinefile.$JOB_ID simpleFoam -parallel >& "$localDir"/simulation/log.simpleFoam

reconstructParMesh -constant

reconstructPar -latestTime

#Generate the train.foam file
touch "$localDir"/simulation/train.foam

# Move all the log files to the logs directory
mv "$localDir"/simulation/log.* "$localDir"/simulation/logs


#------------------------------------------------------------------------------

echo "End Parallel Run"
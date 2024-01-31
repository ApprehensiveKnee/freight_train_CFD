#!/bin/bash             # use bash as command interpreter
#$ -cwd                 # currentWorkingDirectory
#$ -N freight_train           # jobName
#$ -j y                 # merges output and errors
#$ -S /bin/bash         # scripting language
#$ -l h_rt=1:00:00      # jobDuration hh:mm:ss
#$ -q all.q             # queueName
#$ -pe mpi 16           # cpuNumber

echo "Start Parallel Run":

echo "- Importing OpenFOAM"

source "/home/meccanica/ecabiati/.openfoam_modules"

echo "- Initiating Simulation"


#cd "${0%/*}" || exit                                # Run from this directory
#. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions        # Tutorial run functions
#------------------------------------------------------------------------------
# Alternative decomposeParDict name:
#decompDict="-decomposeParDict system/decomposeParDict.6"
## Standard decomposeParDict name:
# unset decompDict

# Define the local directory where the simulation is run
localDir='/home/meccanica/ecabiati/freight_train_CFD'

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

# Define the rotation angle to be used for the simulation
#angle=$(cat 0.orig/include/angulationParameters | grep angulationAngle | awk 'NR ==1{print $2}')
angle=0

# Replace the placeholder in the angulationParameters_0 file with the value in angle and save the result in the angulationParameters file
sed "s/ANGULATION_ANGLE_PLACEHOLDER/$angle/g" "/home/meccanica/ecabiati/freight_train_CFD/simulation/0.orig/include/angulationParameters_0"> /home/meccanica/ecabiati/freight_train_CFD/simulation/\0.orig/include/angulationParameters

# Rotate the box_galleria.stl file by an angle specified in the 0.orig/include/angulationParameters filen along the y axis (also translate the box_galleria.stl file to the origin)
# Also suppress the output of the surfaceTransformPoints command
surfaceTransformPoints -translate "(-0.5 0 -0.25)" -rollPitchYaw "(0 $angle 0)" "$localDir"/simulation/constant/triSurface/box_galleria.stl "$localDir"/simulation/constant/triSurface/box_galleria.stl > /dev/null

# Do the same for the front and back internal planes
surfaceTransformPoints -translate "(-60 0 0.25)" -rollPitchYaw "(0 $angle 0)" "$localDir"/simulation/constant/triSurface/frontInternalWall.stl "$localDir"/simulation/constant/triSurface/frontInternalWall.stl > /dev/null
surfaceTransformPoints -translate "(-60 0 -0.25)" -rollPitchYaw "(0 $angle 0)" "$localDir"/simulation/constant/triSurface/backInternalWall.stl "$localDir"/simulation/constant/triSurface/backInternalWall.stl > /dev/null

#Create the logs directory if it does not exist
mkdir -p "$localDir"/simulation/logs

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

mpirun --hostfile machinefile.$JOB_ID snappyHexMesh -parallel >& "$localDir"/simulation/log.snappyHexMesh

mpirun --hostfile machinefile.$JOB_ID topoSet -parallel >& "$localDir"/simulation/log.topoSet

mpirun --hostfile machinefile.$JOB_ID cretePatch -paralle >& "$localDir"/simulation/log.createPatch


# restore the 0/ directory from the 0.orig/ directory inside each processor directory
#echo "Restore 0/ form 0.orig/  [processor dictionaries]"
#\ls -d processor* | xargs -I {} rm -rf ./{}/0
#\ls -d processor* | xargs -I {} cp -r 0.orig ./{}/0 > /dev/null 2>&1

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
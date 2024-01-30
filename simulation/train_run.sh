#!/bin/bash             # use bash as command interpreter
#$ -cwd                 # currentWorkingDirectory
#$ -N freight_train           # jobName
#$ -j y                 # merges output and errors
#$ -S /bin/bash         # scripting language
#$ -l h_rt=1:00:00      # jobDuration hh:mm:ss
#$ -q all.q             # queueName
#$ -pe mpi 16           # cpuNumber


time ./Allrun_cluster > output.txt
echo End Parallel Run
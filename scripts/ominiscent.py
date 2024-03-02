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

# ----------------- 1. Dimension of the box -----------------


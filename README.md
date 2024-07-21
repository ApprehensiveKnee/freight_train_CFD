# freight_train_CFD
A small CFD analysis performed using OpenFoam, considering the motorBike use case from the OpenFoam tutorials as the backbone for the model of the solution, integrated with a simplified CAD model of a [British Rail Class 66] locomotive plus some additional loads. 

The code has been modified to be hosted and run on a cluster managed by the _[sun grid engine (SGE)]_. The results obtained can be processed and visualized using the _[Paraview]_  software.

The directory also features a pyhon script used to automate the optimization process for the coice of some simple parameters that one would tipically set when running a CFD simulation


![Flow results from one of the simulations](https://github.com/ApprehensiveKnee/freight_train_CFD/blob/master/img/sim3.png)
<p float="left">
  <img src="https://github.com/ApprehensiveKnee/freight_train_CFD/blob/master/img/treno_quad_cad.png" width="100" />
  <img src="https://github.com/ApprehensiveKnee/freight_train_CFD/blob/master/img/treno_smus_cad.png" width="100" /> 
</p>

## Outilne of the code
The code is centered around two main files in charge of running the whole simulation and optimization process, on the cluster, in an automated manner. These files are:
 
 - `run_train_scratch.sh `: a parametric bash script whose role is that of running a single simulation based on specifications passed to it when called from command line. It is basically an extension of a simpler, more common, _job launch file_, used to stage a single simulation onto the cluster queue. \
 **<span style="color: orange">Problem Tackled: running different simulations more easily<span>**.\
  A rather annoying feature for such scripts is that, however simple they may be, the parameters for a specific simulation - such as the coordinates (dimensions) of the domain, the number of cells at lower resolution level, the refinement parameters - have to be hard coded into the single different files.\
 `run_train_scratch.sh ` removes this problem by allowing the user to pass the parameters to the script as _command line arguments_, after specifying, with an appropriate flag, the type of parameter we want to define.
 
 Here is an example of how to use the script:

```sh
# Move inside the directory where the script is located
cd /path/to/the/script
# Launch the script with the appropiate parameters
./run_train_scratch.sh -n <result_directory_name> 
                       -a <angulation_flag>
                       -v <velocity_angle_value>
                       -g <include_gallery_flag>
                       -o <rotation_ref_boxes_flag>
                       -b <coordinates_of_outer_domain>
                       -c <numer_of_cells_at_lower_resolution>
                       -r <refinement_boxes_parameters>
                       -t <refinement_train_parameters>

```


- `oscent.py`: a python script, written with some basic python packages, to fit the cluster environment. It is the **core** of the code, to be used as a sort of interface whenever interacting with the optimization process.
**<span style="color: orange">Problem Tackled: manage the optimization process more easily<span>**.\
It comes in two flavors: 
    * **<span style="color: orange">it allows to launch a batch of simulations<span>**. Each simulation differs from the others for the value of a single parameter, specified when launching the script, while the others are kept fixed across all the simulations. The pool of different values for the chosen parameter is obtained starting form hardcoded reference values and then adding a simple increment (linear with the reference value, positive or negative)
    * **<span style="color: orange">it runs a simple empirical algorithm to optimize (i.e. choose the best simulation) out of the previously run batches<span>**. By sorting out the best simulation, we also determine the best value for the parameter we were optimizing for.
    By iterating the process over the different parameters, we hope to obtain a set of parameters to run efficiently enough the final simulation to study the problem at hand.

Here is an example of how to use the script:

```sh

# Move inside the directory where the script is located
cd /path/to/the/script
# Launch a batch of simulations on the outer box/domain, cells, refinement boxes and train refinement parameters
# Please note that the options parsed are mutually exclusive
python oscent.py -b box
python oscent.py -b cells
python oscent.py -b ref
python oscent.py -b train

# Run the optimization process on the box, cells, boxes refinement, train refinement batchsimulations
python oscent.py -o box
python oscent.py -o cells
python oscent.py -o ref
python oscent.py -o train

```

## The optimization algorithm

The optimization algorithm was based on a simple method, which proved to be quite effective in practice. In this sense, we shall refer to it as an empirical algorithm. The algorithm is based on the following steps:

- get the results ($C_x$, force coefficients along the x axis) and execution times of the simulations run with different values of the parameter we want to optimize for
- compute for each simulation a score, to be used as a measure of the trade-off between the quality of the results and the time it took to obtain them. The scores are computed as follows

$$
score = \log(time_{tot}) + \alpha * |(C_x - C_{ref})|
$$

 where $time_{tot}$ is the total time it took to run the simulation (comprehensive of both `simpleFoam` and `snappyHexMesh`), $C_x$ is the force coefficient along the x axis, $C_{ref}$ is the reference value for the force coefficient, computed as the weighted sums of the $C_x$'s of the different simulations, and $\alpha$ is a parameter that we can tune to give more or less importance to the quality of the results.
- choose the simulation with the **lowest score as the best simulation**, and the value of the parameter that was used to run it as the best value for the parameter.


### A note
The search of the space of parameters implemented is far from extensive, and the optimization process is not very sophisticated. 

Ideally, one would like to implement something like a gradient descent algorithm, but in this case the fact that no such a thing as a dataset (or an analogous) is available, makes the implementation of such a method quite difficult. The algorithm chosen was thought up in an attempt to simplify the problem as well as mimicking the way a human would approach the problem, by plotting the results and then choosing the best value for the parameter.

[British Rail Class 66]: https://en.wikipedia.org/wiki/British_Rail_Class_66
[sun grid engine (SGE)]: https://en.wikipedia.org/wiki/Oracle_Grid_Engine
[Paraview]: https://www.paraview.org/

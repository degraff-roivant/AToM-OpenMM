AToM-OpenMM Tutorials
------------------------

### Tutorials

We recommend going over the tutorials in this sequence. 

- [ABFE/temoa-g1](ABFE/temoa-g1): absolute binding free energy between the TEMOA host and the G1 guest from the [SAMPL8 GDCC](https://github.com/samplchallenges/SAMPL8/tree/master/host_guest/GDCC) challenge.
 - [RBFE/temoa-g1-g4](RBFE/temoa-g1-g4): relative binding free energy between the G1 and G4 guests to the TEMOA host from the [SAMPL8 GDCC](https://github.com/samplchallenges/SAMPL8/tree/master/host_guest/GDCC) challenge.
- [ABFE/fkbp](ABFE/fkbp): absolute binding free energies of a series of complexes of FKBP with ligand fragments from [Pan A, Xu H, Palpant T, Shaw DE; JCTC 2017](http://dx.doi.org/10.1021/acs.jctc.7b00172)
- [RBFE/eralpha](RBFE/eralpha): relative binding free energies of four ligands binding to the ERα protein receptor from [Azimi, Khuttan, Wu, Pal, Gallicchio. Relative Binding Free Energy Calculations for Ligands with Diverse Scaffolds with the Alchemical Transfer Method](https://pubs.acs.org/doi/10.1021/acs.jcim.1c01129).

### Software requirements

This AToM-OpenMM software. The examples have been written assuming that it is installed under `$HOME/software/AToM-OpenMM`.

Follow the [installation instructions](https://github.com/Gallicchio-Lab/openmm-atmmetaforce-plugin) to install OpenMM and the ATM Meta Force plugin. In general, we assume that the [OpenMM](http://openmm.org) libraries (version 7.6.0 or newer) have been installed in a location where python can find them. Presumably you did so under a `conda` environment. If so activate the environment to run the examples. We also assume that the [ATMMetaForce OpenMM plugin](https://github.com/Gallicchio-Lab/openmm-atmmetaforce-plugin) is installed and available within the same OpenMM environment and that python can find the corresponding python bindings. 

When using a conda environment, the examples can be launched with the ``python`` command of that environment. For other situations, a sample `runopenmm` script is provided in the  [scripts/]( https://github.com/Gallicchio-Lab/AToM-OpenMM/tree/master/examples/scripts) to get you started if needed. It requires you to define the environment variable `OPENMM_DIR` pointing to the OpenMM installation on your system. It also assumes that the python OpenMM bindings have been stored under the same folder.

Free energy analysis requires R with the UWHAM R module. Do ``conda install r-base`` to install R in a conda environment. To install the UWHAM module run `install.packages("UWHAM")` in R.


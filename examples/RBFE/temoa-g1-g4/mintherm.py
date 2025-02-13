from __future__ import print_function

from simtk import openmm as mm
from simtk.openmm.app import *
from simtk.openmm import *
from simtk.unit import *
from sys import stdout
import os, re,time, shutil, math
from datetime import datetime

from atmmetaforce import *

#the multiple-time step integrator does not have a setTemperature() method
def setTemperature(self, temperature):
    self.setGlobalVariableByName('kT', MOLAR_GAS_CONSTANT_R*temperature)
MTSLangevinIntegrator.setTemperature = setTemperature

print("Started at: " + str(time.asctime()))
start=datetime.now()

jobname = "temoa-g1-g4"

#define the receptor atoms and the ligands atoms based on their resids
rcpt_resid = 1
lig1_resid = 2
lig2_resid = 3

#displacement vector and Vsite offsets
displ = [ 22.0, 22.0, 22.0 ]
displacement      = [  displ[i] for i in range(3) ] * angstrom
lig1_restr_offset = [  0.       for i in range(3) ] * angstrom
lig2_restr_offset = [  displ[i] for i in range(3) ] * angstrom

#reference atoms of the ligands for the alignment restraints
#these are molecular indexes (0 is the first atom of each ligand)
refatoms_lig1 = [8, 6, 4]
refatoms_lig2 = [3, 5, 1]

#define the thermodynamic/alchemical state
#the system is prepared at the alchemical intermediate state at lambda=1/2
temperature = 300.0 * kelvin
lmbd = 0.50
lambda1 = lmbd
lambda2 = lmbd
alpha = 0.0 / kilocalorie_per_mole
u0 = 0.0 * kilocalorie_per_mole
w0coeff = 0.0 * kilocalorie_per_mole
umsc =  100.0 * kilocalorie_per_mole
ubcore = 50.0 * kilocalorie_per_mole
acore = 0.062500
direction = 1

#load system
prmtop = AmberPrmtopFile(jobname + '.prmtop')
inpcrd = AmberInpcrdFile(jobname + '.inpcrd')
system = prmtop.createSystem(nonbondedMethod=PME, nonbondedCutoff=0.9*nanometer,
                             constraints=HBonds)

#load the ATM Meta Force facility
atm_utils = ATMMetaForceUtils(system)

number_of_atoms = prmtop.topology.getNumAtoms()

#list of receptor atoms and ligands
rcpt_atoms = []
for at in prmtop.topology.atoms():
    if int(at.residue.id) == rcpt_resid:
        rcpt_atoms.append(at.index)
        
lig1_atoms = []
for at in prmtop.topology.atoms():
    if int(at.residue.id) == lig1_resid:
        lig1_atoms.append(at.index)
        
lig2_atoms = []
for at in prmtop.topology.atoms():
    if int(at.residue.id) == lig2_resid:
        lig2_atoms.append(at.index)

#Vsite restraints for each ligand. 
#the CMs are defined by all atoms of each molecule
rcpt_cm_atoms = rcpt_atoms
lig1_cm_atoms = lig1_atoms
lig2_cm_atoms = lig2_atoms
#Output lists of atoms so they can be placed into the asyncre cntl file if needed
print("List of ligand 1 CM atoms (LIGAND1_CM_ATOMS):")
print(lig1_cm_atoms)
print("List of ligand 2 CM atoms (LIGAND2_CM_ATOMS):")
print(lig2_cm_atoms)
print("List of receptor CM atoms (RCPT_CM_ATOMS):")
print(rcpt_cm_atoms)
#force constant and tolerance     
kf = 25.0 * kilocalorie_per_mole/angstrom**2 #force constant for Vsite CM-CM restraint
r0 = 5 * angstrom #radius of Vsite sphere
#Vsite restraint for the first ligand, assumed in the binding site
atm_utils.addRestraintForce(lig_cm_particles = lig1_cm_atoms,
                            rcpt_cm_particles = rcpt_cm_atoms,
                            kfcm = kf,
                            tolcm = r0,
                            offset = lig1_restr_offset)
#Vsite restraint for the second ligand, assumed in the solvent bulk
atm_utils.addRestraintForce(lig_cm_particles = lig2_cm_atoms,
                            rcpt_cm_particles = rcpt_cm_atoms,
                            kfcm = kf,
                            tolcm = r0,
                            offset = lig2_restr_offset)

#alignment restraints, to force the two ligands to remains rougly superimposed
#when they are both translated into the binding site
lig1_ref_atoms  = [ refatoms_lig1[i]+lig1_atoms[0] for i in range(3)]
lig2_ref_atoms  = [ refatoms_lig2[i]+lig2_atoms[0] for i in range(3)]
atm_utils.addAlignmentForce(liga_ref_particles = lig1_ref_atoms,
                            ligb_ref_particles = lig2_ref_atoms,
                            kfdispl = 2.5 * kilocalorie_per_mole/angstrom**2,
                            ktheta =  10.0 * kilocalorie_per_mole,
                            kpsi =  10.0 * kilocalorie_per_mole,
                            offset = lig2_restr_offset)

#restrain all heavy atoms of receptor and ligands to equilibrate only the solvent
fc = 25.0 * kilocalorie_per_mole/angstrom**2
tol = 0.5 * angstrom
hydrogen = Element.getByAtomicNumber(1)
posrestr_atoms = []
for at in prmtop.topology.atoms():
    if ( int(at.residue.id) == rcpt_resid or int(at.residue.id) == lig1_resid or int(at.residue.id) == lig2_resid ) and at.element is not hydrogen:
        posrestr_atoms.append(at.index)
atm_utils.addPosRestraints(posrestr_atoms, inpcrd.positions, fc, tol)

#create ATM Force
atmforcegroup = 2
nonbonded_force_group = 1
atm_utils.setNonbondedForceGroup(nonbonded_force_group)
atmvariableforcegroups = [nonbonded_force_group]
atmforce = ATMMetaForce(lambda1, lambda2,  alpha * kilojoules_per_mole, u0/kilojoules_per_mole, w0coeff/kilojoules_per_mole, umsc/kilojoules_per_mole, ubcore/kilojoules_per_mole, acore, direction, atmvariableforcegroups )
#adds all atoms to the force with zero displacement
for at in prmtop.topology.atoms():
    atmforce.addParticle(int(at.id)-1, 0., 0., 0.)
#the ligand atoms get displaced, ligand 1 from binding site to the solvent bulk
#and ligand 2 from the bulk solvent to the binding site
for i in lig1_atoms:
    atmforce.setParticleParameters(i, i, displ[0] * angstrom, displ[1] * angstrom, displ[2] * angstrom)
for i in lig2_atoms:
    atmforce.setParticleParameters(i, i, -displ[0] * angstrom, -displ[1] * angstrom, -displ[2] * angstrom)
atmforce.setForceGroup(atmforcegroup)
system.addForce(atmforce)

#Set up Langevin integrator
initial_temperature = 50 * kelvin
final_temperature = 300 * kelvin
temperature = initial_temperature
frictionCoeff = 0.5 / picosecond
MDstepsize = 0.001 * picosecond
#MD is conducted using forces from groups 0 (forces not added to the ATM Meta Force)
#and the group of the ATM Meta Force.
integrator = MTSLangevinIntegrator(temperature, frictionCoeff, MDstepsize, [(0,1), (atmforcegroup,1)])
integrator.setConstraintTolerance(0.00001)

platform_name = 'OpenCL'
#platform_name = 'CUDA'
platform = Platform.getPlatformByName(platform_name)
properties = {}
properties["Precision"] = "mixed"

simulation = Simulation(prmtop.topology, system, integrator,platform, properties)
print ("Using platform %s" % simulation.context.getPlatform().getName())
simulation.context.setPositions(inpcrd.positions)
if inpcrd.boxVectors is not None:
    simulation.context.setPeriodicBoxVectors(*inpcrd.boxVectors)

state = simulation.context.getState(getEnergy = True, groups = {1,3})
print("Potential energy before minimization =", simulation.context.getState(getEnergy = True, groups = {0,atmforcegroup}).getPotentialEnergy())

print("Energy minimizing the system ...")
simulation.minimizeEnergy()

print("Potential energy after minimization =", simulation.context.getState(getEnergy = True, groups = {0,atmforcegroup}).getPotentialEnergy())
  
print("Thermalization ...")

totalSteps = 50000
steps_per_cycle = 5000
number_of_cycles = int(totalSteps/steps_per_cycle)
delta_temperature = (final_temperature - initial_temperature)/number_of_cycles
simulation.reporters.append(StateDataReporter(stdout, steps_per_cycle, step=True, potentialEnergy = True, temperature=True))

#binding energy values and other parameters are recorded in this file
f = open(jobname + "_mintherm.out", 'w')

#MD with temperature ramp
for i in range(number_of_cycles):
    simulation.step(steps_per_cycle)
    state = simulation.context.getState(getEnergy = True, groups = {0,atmforcegroup})
    pot_energy = (state.getPotentialEnergy()).value_in_unit(kilocalorie_per_mole)
    pert_energy = (atmforce.getPerturbationEnergy(simulation.context)).value_in_unit(kilocalorie_per_mole)
    l1 = simulation.context.getParameter(atmforce.Lambda1())
    l2 = simulation.context.getParameter(atmforce.Lambda2())
    a = simulation.context.getParameter(atmforce.Alpha()) / kilojoules_per_mole
    umid = simulation.context.getParameter(atmforce.U0()) * kilojoules_per_mole
    w0 = simulation.context.getParameter(atmforce.W0()) * kilojoules_per_mole
    print("%f %f %f %f %f %f %f %f %f" % (temperature/kelvin,lmbd, l1, l2, a*kilocalorie_per_mole, umid/kilocalorie_per_mole, w0/kilocalorie_per_mole, pot_energy, pert_energy), file=f )
    f.flush()
    #prepare system for new temperature
    temperature = temperature + delta_temperature
    integrator.setTemperature(temperature)

#saves checkpoint
print( "SaveState ...")
simulation.saveState(jobname + '_mintherm.xml')

#saves a pdb file
positions = simulation.context.getState(getPositions=True).getPositions()
boxsize = simulation.context.getState().getPeriodicBoxVectors()
simulation.topology.setPeriodicBoxVectors(boxsize)
with open(jobname + '_mintherm.pdb', 'w') as output:
  PDBFile.writeFile(simulation.topology, positions, output)

end=datetime.now()
elapsed=end - start
print("elapsed time="+str(elapsed.seconds+elapsed.microseconds*1e-6)+"s")

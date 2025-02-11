#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 10:01:19 2022

@author: ceboncompte
"""

from DM_solver.solver import H_channel, H_solver

from hamiltonian import hheis_general, heisenberg_hamiltonian_3, ladder_exchanges, is_unitary
from use import matrix_plot, basis_transformation
from basis_matrix import coupled_matrix_gen

from qutip import *
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

# We first want to create the arbitrary Hamiltonian and print the matrix
Jij_vector = np.array([1, 0, 1]) # in natural units
Jij_ladder = np.array([1, 0, 1]) # in natural units
B = 0.5 # this B is energy!
spins = len(Jij_vector) + 1

# We check the Hamiltonian is Hermitian
H = hheis_general(Jij_vector, spins, B) + ladder_exchanges(Jij_ladder, spins)
H.check_herm()

# We get the eigenstates
B = 0
H.eigenstates()

# We plot the matrix
matrix_plot(H)

# We generate the basis-transformation matrix
trans_matrix = coupled_matrix_gen(spins)
matrix_plot(trans_matrix) # The basis states are rows
print(trans_matrix[0,:]) #first basis state in the first doublet subspace
print(trans_matrix[1,:]) #second

# We also want to check if the basis-transformation matrix is unitary
ct_trans_matrix = np.transpose(np.conjugate(trans_matrix))
matrix_plot(np.matmul(trans_matrix, ct_trans_matrix))
# We see we get an identity
# Alternatively (unitary test works with allclose numpy function)
is_unitary(trans_matrix)

# We finally basis transform and plot again the Hamiltonian matrix
H_coup = basis_transformation(H, trans_matrix)
# And we plot it
matrix_plot(H_coup)

# We check again if the Hamiltonian is Hermitian
H_coup.check_herm()

# Now we want to see how the energy of the ground state evolves with the magnetic field
number_iterations = 100
Bini = 0
Bfin = 2
values_B = np.linspace(Bini, Bfin, number_iterations)
energy_tracker = np.zeros((number_iterations))
n = 0

for B in values_B:
    # We first want to create the arbitrary Hamiltonian and print the matrix
    Jij_vector = np.array([1, 1, 1])
    spins = len(Jij_vector) + 1
    H = hheis_general(Jij_vector, spins, B)
    
    # We get the ground state
    gs = H.groundstate()
    print(gs[0], gs[1])    
    energy_tracker[n] = gs[0]
    n += 1

# we plot the energy of the groundstate
#plt.figure(figsize=(6,5))
plt.figure()
plt.plot(values_B, energy_tracker, label='E1')
plt.xlabel('$B$ ($E_0$)')
plt.ylabel('energy ($E_0$)')
plt.title('Energy of the groundstate')
plt.show()

# Therefore setting B = 0.5 allows us to stay in the not fully polarized state
B = 0.5
end_time = 5 # time of the oscillations (in natural units)
dimensions_time_evo_tracker = 1000 # number of time steps
time_evo_tracker = np.zeros((2, dimensions_time_evo_tracker))

# Now we want to see how does an initial state made out of one of the valence bonds of the
# ground state evolve. In particular we are interested in the probability of measuring all
# the valence bonds composing that ground state
Jij_vector = np.array([1, 1, 1])
spins = len(Jij_vector) + 1
H = hheis_general(Jij_vector, spins, B) + chain_bc(1, spins)
H.groundstate()

# Let's try to reconstruct this ground state
p1 = (basis(16, 5) - basis(16,6) - basis(16,9) + basis(16,10)).unit() #S12, S34
print(p1)
S = (basis(4,1) - basis(4,2)).unit() # SS same as p1

p2 = (basis(16, 3) - basis(16,5) - basis(16,10) + basis(16,12)).unit() # S14 S23, not used here
print(p2)

p3 = (basis(16, 3) - basis(16,6) - basis(16,9) + basis(16,12)).unit() #S13 S24
print(p3)

# Ground state for the bc case
gs_bc = (p1-p2).unit()
print(gs_bc) # up to a global pahse

# We base transform, to make the time evolution cheaper
trans_matrix = coupled_matrix_gen(spins)
H_coup = basis_transformation(H, trans_matrix)
H_singlet = H_coup[0:2, 0:2]

# We time evolve
CH0 = H_channel(H_singlet)
CH0.pulse.add_constant(2*np.pi*1.)
# We solve the Schrodinger equation
calculation = H_solver()
calculation.add_channels(CH0)

# Intitial state is the first state (first row) of the basis-transformation matrix
ket0 = tensor(S, S) #this is S12S34
print(ket0)
ket0_t = basis_transformation(ket0, trans_matrix)
print(ket0_t) #this is basis(2,0)
ket0_red = basis(2,0)
dm0 = ket0_red * ket0_red.dag()
dm0 = np.array(dm0)

# The other state composing the RVB
ket1 = p3 #this is S13S24
print(ket1)
ket1_t = basis_transformation(ket1, trans_matrix)
print(ket1_t) #this is -basis(2,0)+sqrt(3)*basis(2,1)
ket1_red = (basis(2,0) + np.sqrt(3)*basis(2,1)).unit()
print(ket1_red)
dm1 = ket1_red * ket1_red.dag()
dm1 = np.array(dm1)

# Calculate for end_time
number_steps = dimensions_time_evo_tracker
sample_rate = number_steps/end_time
calculation.calculate(dm0, end_time = end_time, sample_rate = sample_rate)

# Calculate the expectatoin value of the matrix dm0 and plot
dm_expect = calculation.return_expectation_values(dm0, dm1)
time_evo_tracker[0,:] = dm_expect[0]
time_evo_tracker[1,:] = dm_expect[1]
t = calculation.return_time()

# Finally we plot the oscillations
x = t
plt.plot(x, time_evo_tracker[0,:], label='$\Psi_0$')
plt.plot(x, time_evo_tracker[1,:], label='$\Psi_1$')
plt.title('Probability of measurement')
plt.xlabel('time ($t_0$)')
plt.ylabel('probability')
plt.legend()
#plt.ylabel('$J_{12} - J_{23}$ ($E_0$)')
plt.show()

# Finally what we will do is repeat this process multiple times varying the values of J. For being
# this case symmetirc we will fix one J and vary the other.

# --------------------------------------------- FOR THE ENERGY PLOTS
number_iterations = 100 # number of different values of J we test
energy_tracker = np.zeros((number_iterations, 2)) # 2 (singlet) refers to the number of states in the subspace
#J23ini = 1.5
#J23fin = 0.5
J23ini = 0.3
J23fin = 1.8
values_J23 = np.linspace(J23ini, J23fin, number_iterations)
#values_J23 = np.linspace(2, 0, number_iterations)
n = 0

# --------------------------------------------- FOR THE OSCILLATIONS AND FOURIERS
end_time = 5 # time of the oscillations (in natural units)
dimensions_expect_tracker = 1000 # number of time steps
expect_tracker = np.zeros((number_iterations, dimensions_expect_tracker))
expect_tracker_ = np.zeros((number_iterations, dimensions_expect_tracker))
amplitude0_tracker = np.zeros((number_iterations, dimensions_expect_tracker))
amplitude1_tracker = np.zeros((number_iterations, dimensions_expect_tracker))
proba_amplitude = np.zeros((number_iterations, 2)) # we use 2 states for measurement
B = 0.3
J12zero = 2
#J12zero = 3

# We generate the basis-transformation matrix
trans_matrix = coupled_matrix_gen(spins)

for J23 in values_J23:
    # We first want to create the arbitrary Hamiltonian and print the matrix
    #Jij_vector = np.array([J23, 0, J23])
    #Jij_ladder = np.array([J12zero - J23, J12zero - J23])
    
    #Jij_vector = np.array([J23, 0, 1])
    #Jij_ladder = np.array([J12zero - J23, 1])
    
    Jij_vector = np.array([J23, 0, J23])
    Jij_ladder = np.array([1, 1])
    spins = len(Jij_vector) + 1
    H = hheis_general(Jij_vector, spins, B) + ladder_exchanges(Jij_ladder, spins)
    
    # We plot the matrix
#    matrix_plot(H)
    
    # We finally basis transform and plot again the Hamiltonian matrix
    H_coup = basis_transformation(H, trans_matrix)
#    matrix_plot(H_coup)
    
    # We take the first doublet and we get the energies of the states
    H_singlet = H_coup[0:2, 0:2]
#    matrix_plot(H_doublet)
    
    # --------------------------------------------- OSCILLATIONS
    # We transform this Hamiltonian into an H_channel (non time dependent)
    CH0 = H_channel(H_singlet)
    CH0.pulse.add_constant(2*np.pi*1.) # natural units of f (1/time usually)
    
    # We solve the Schrodinger equation
    calculation = H_solver()
    calculation.add_channels(CH0)
    
    # Initial state dm0 and dm1 aready defined
    
    # Calculate for end_time
    number_steps = dimensions_expect_tracker
    sample_rate = number_steps/end_time
    calculation.calculate(dm1, end_time = end_time, sample_rate = sample_rate)
    
    # Calculate the expectatoin value of the matrix dm0 and plot
    dm_expect = calculation.return_expectation_values(dm0, dm1)
    expect_tracker[n,:] = dm_expect[0]
    expect_tracker_[n,:] = dm_expect[1]
    t = calculation.return_time()
    
    # We store the maximum and minimum of amplitude for each measurement
    max0 = np.amax(dm_expect[0])
    min0 = np.amin(dm_expect[0])
    max1 = np.amax(dm_expect[1])
    min1 = np.amin(dm_expect[1])
    proba_amplitude[n,0] = max0-min0
    proba_amplitude[n,1] = max1-min1
    
    # Fourier ttransform
    time_step = 1/sample_rate
    sig_fft0 = sp.fftpack.fft(dm_expect[0]) # we get the fft of the signal 
    sig_fft1 = sp.fftpack.fft(dm_expect[1])
    amplitude0 = np.abs(sig_fft0)
    amplitude1 = np.abs(sig_fft1)
    sample_freq = sp.fftpack.fftfreq(dm_expect[0].size, d = time_step) # length dimensions_expect_tracker (1000)
    amplitude0[0] = 0 # we set the zero frequency amplitude
    amplitude1[0] = 0
    amplitude0_tracker[n,:] = amplitude0 # amplitude has length of dimensions_expect_tracker (1000)
    amplitude1_tracker[n,:] = amplitude1

    # We diagonalize and obtain energy values
    ev = sp.linalg.eigvalsh(H_singlet)
    energy_tracker[n,:] = ev
    n+=1

# we plot the energy of the eigenstates
#plt.figure(figsize=(6,5))
plt.figure()
plt.plot(values_J23, np.transpose(energy_tracker)[0,:], label='E1')
plt.plot(values_J23, np.transpose(energy_tracker)[1,:], label='E2')
plt.axvline(x=0.5, color='k', linestyle='dotted')
plt.xlabel('$J_v/2$ ($E_0$)')
plt.ylabel('energy ($E_0$)')
#plt.title('Energies of the singlet subspace')
plt.show()

# finally we colour plot the expect_tracker matrix data array and the amplitude_tracker for the fourier transform
x = t
y = values_J23
plt.pcolormesh(x, y, expect_tracker)
plt.axhline(y=0.5, color='w', linestyle='dotted')
plt.axhline(y=1, color='k', linestyle='dashed')
#plt.title('Probability of $\Psi_0$')
plt.xlabel('$J_v/2$ ($E_0$)')
plt.ylabel('$J_{23}$ ($E_0$)')
plt.colorbar()
plt.show()

# and Fourier
x = sample_freq
#y = np.linspace(J12zero-2*J23ini, J12zero-2*J23fin, number_iterations)
y = values_J23
plt.pcolormesh(x[:50], y, amplitude0_tracker[:,:50])
plt.axhline(y=0.5, color='w', linestyle='dotted')
plt.axhline(y=1, color='w', linestyle='dashed')
#plt.title('Fourier transform of the probability of $\Psi_0$')
plt.xlabel('frequency ($f_0$)')
#plt.ylabel('$J_{12} - J_{23}$ ($E_0$)')
plt.ylabel('$J_v/2$ ($E_0$)')
plt.colorbar()
plt.show()

# We do the same for the other measured state
x = t
y = values_J23
plt.pcolormesh(x, y, expect_tracker_)
plt.axhline(y=0.5, color='k', linestyle='dotted')
#plt.title('Probability of $\Psi_1$')
plt.xlabel('time ($t_0$)')
plt.ylabel('$J_v/2$ ($E_0$)')
plt.colorbar()
plt.show()

# to plot the whole frequency spectrum (with negative ones)
x = sample_freq
#y = np.linspace(J12zero-2*J23ini, J12zero-2*J23fin, number_iterations)
y = values_J23
plt.pcolormesh(x[:50], y, amplitude1_tracker[:,:50])
plt.axhline(y=0.5, color='w', linestyle='dotted')
#plt.title('Fourier transform of the probability of $\Psi_1$')
plt.xlabel('frequency ($f_0$)')
#plt.ylabel('$J_{12} - J_{23}$ ($E_0$)')
plt.ylabel('$J_v/2$ ($E_0$)')
plt.colorbar()
plt.show()

# We want a better plot showing a maximum in amplitude of our measured states
plt.plot(values_J23, proba_amplitude[:,0], label='$S_{12}S_{34}$')
plt.plot(values_J23, proba_amplitude[:,1], label='$S_{13}S_{24}$')
#plt.plot(values_J23, proba_amplitude[:,1] - proba_amplitude[:,0], label='difference')
plt.axvline(x=1, color='k', linestyle='dashed')
plt.xlabel('$J_v/2$ ($E_0$)')
plt.ylabel('visibility')
#plt.title('Probability amplitude')
plt.legend()
plt.show()
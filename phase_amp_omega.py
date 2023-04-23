import numpy as np
from scipy.optimize import curve_fit

def read_ascii_file(file_name):
    """
    Reads a 3-column ASCII file, skipping lines that start with '#'.

    Args:
        file_name (str): The name of the file to read.

    Returns:
        tuple: A tuple containing three numpy arrays (time, real, imag).
    """
    data = []

    with open(file_name, 'r') as file:
        for line in file:
            if not line.startswith('#'):
                columns = line.split()
                data.append([np.float64(columns[0]), np.float64(columns[1]), np.float64(columns[2])])

    # Convert data to a numpy array and sort by the time column (leftmost column)
    data = np.array(data, dtype=np.float64)
    data = data[data[:, 0].argsort()]

    # Remove duplicate times
    unique_indices = np.unique(data[:, 0], return_index=True)[1]
    data = data[unique_indices]

    # Split the data back into time, real, and imag arrays
    time, real, imag = data[:, 0], data[:, 1], data[:, 2]

    return time, real, imag

def compute_derivative(time, data):
    """
    Calculates the time derivative of the input data using a second-order finite difference stencil.

    Args:
        time (numpy.ndarray): A numpy array containing time values.
        data (numpy.ndarray): A numpy array containing the data to be differentiated.

    Returns:
        numpy.ndarray: A numpy array containing the time derivative of the input data.
    """
    dt = time[1] - time[0]
    derivative = np.zeros_like(data)
    # Second-order in the interior:
    derivative[1:-1] = (data[2:] - data[:-2]) / (2 * dt)
    # Drop to first-order at the endpoints
    derivative[0] = (data[1] - data[0]) / dt
    derivative[-1] = (data[-1] - data[-2]) / dt

    return derivative


def process_wave_data(time, real, imag):
    """
    Calculates the cumulative phase and amplitude of a gravitational wave signal.

    Args:
        time (numpy.ndarray): A numpy array containing time values.
        real (numpy.ndarray): A numpy array containing the real part of the signal.
        imag (numpy.ndarray): A numpy array containing the imaginary part of the signal.

    Returns:
        tuple: A tuple containing three numpy arrays (time, cumulative_phase, amplitude).
    """
    # Calculate the amplitude of the gravitational wave signal.
    amplitude = np.sqrt((real**2 + imag**2), dtype=np.float64)

    # Calculate the instantaneous phase of the gravitational wave signal.
    phase = np.arctan2(imag, real, dtype=np.float64)

    # Initialize a variable to count the number of full cycles completed by the signal.
    cycles = 0

    # Initialize an empty list to store the cumulative phase of the signal.
    cum_phase = []

    # Set the variable `last_phase` to the first value of the instantaneous phase array.
    last_phase = phase[0]

    # Iterate over each value of the instantaneous phase array.
    for ph in phase:
        # Check if the absolute difference between the current phase and the previous phase
        # is greater than or equal to pi (to identify phase wrapping).
        if np.abs(ph - last_phase) >= np.pi:
            # If the current phase is positive, the phase wrapped from a positive value
            # to a negative value, so decrease the `cycles` variable by 1.
            if ph > 0:
                cycles -= 1
            # If the current phase is negative, the phase wrapped from a negative value
            # to a positive value, so increase the `cycles` variable by 1.
            if ph < 0:
                cycles += 1

        # Calculate the cumulative phase for the current time step and append it to the `cum_phase` list.
        cum_phase.append(ph + 2 * np.pi * cycles)

        # Update the `last_phase` variable with the current phase value.
        last_phase = ph

    # Calculate the cumulative phase for the current time step and append it to the `cum_phase` list.
    cum_phase = np.array(cum_phase, dtype=np.float64)

    # Compute the time derivative of the cumulative phase using a second-order finite difference stencil.
    cum_phase_derivative = compute_derivative(time, cum_phase)

    return time, cum_phase, amplitude, cum_phase_derivative

import sys

def fit_quadratic_and_output_min_omega(time, omega):
    def quadratic(x, a, b, c):
        return a * x**2 + b * x + c

    # Filter the data for t=100 to t=300
    time_filtered = time[(time >= 100) & (time <= 300)]
    omega_filtered = omega[(time >= 100) & (time <= 300)]

    # Fit a quadratic curve to the Omega data using nonlinear least squares
    params, _ = curve_fit(quadratic, time_filtered, omega_filtered)

    # Find the extremum value of the quadratic curve
    a, b, c = params
    extremum_x = -b / (2 * a)
    omega_min_quad_fit = quadratic(extremum_x, a, b, c)
    omega_at_t_zero = quadratic(0.0, a, b, c)

    print(f"The extremum of the quadratic curve occurs at t = {extremum_x:.15f} with omega = {omega_min_quad_fit:.15f} . implied omega(t=0) = {omega_at_t_zero:.15f}")
    
    
def main():
    """
    Main function that reads the gravitational wave data file, processes the data,
    and saves the output to a file. The input filename is provided via command line.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 phase_amp_omega.py <gravitational_wave_data.asc or .txt>")
        sys.exit(1)

    file_name = sys.argv[1]

    if not file_name.endswith('.asc') and not file_name.endswith('.txt'):
        print("Error: Input file must have a '.asc' or '.txt' extension.")
        sys.exit(1)

    time, real, imag = read_ascii_file(file_name)
    time, cumulative_phase, amplitude, omega = process_wave_data(time, real, imag)

    fit_quadratic_and_output_min_omega(time, omega)

    output_file = file_name
    if file_name.endswith('.asc'):
        output_file = output_file.replace('.asc', '_phase_amp_omega.asc')
    elif file_name.endswith('.txt'):
        output_file = output_file.replace('.txt', '_phase_amp_omega.txt')

    with open(output_file, 'w') as file:
        file.write("# Time    cumulative_phase    amplitude    omega\n")
        for t, cp, a, o in zip(time, cumulative_phase, amplitude, omega):
            file.write(f"{t:.15f} {cp:.15f} {a:.15f} {o:.15f}\n")

    print(f"Processed data has been saved to {output_file}")

if __name__ == "__main__":
    main()

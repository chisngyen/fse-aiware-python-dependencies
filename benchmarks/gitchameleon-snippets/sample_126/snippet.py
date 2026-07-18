import scipy.signal.windows as windows
import numpy as np
def compute_lanczos_window(window_size:int)->np.ndarray:

    window = 2*np.arange(window_size)/(window_size-1) - 1 
    window = np.sinc(window)
    window = window / np.max(window)
    return window

# --- test ---

window_size=31
window = compute_lanczos_window(window_size)
expect = np.array([
    3.89817183e-17, 7.09075143e-02, 1.49386494e-01, 2.33872321e-01,
    3.22568652e-01, 4.13496672e-01, 5.04551152e-01, 5.93561534e-01,
    6.78356039e-01, 7.56826729e-01, 8.26993343e-01, 8.87063793e-01,
    9.35489284e-01, 9.71012209e-01, 9.92705200e-01, 1.00000000e+00,
    9.92705200e-01, 9.71012209e-01, 9.35489284e-01, 8.87063793e-01,
    8.26993343e-01, 7.56826729e-01, 6.78356039e-01, 5.93561534e-01,
    5.04551152e-01, 4.13496672e-01, 3.22568652e-01, 2.33872321e-01,
    1.49386494e-01, 7.09075143e-02, 3.89817183e-17
])
assertion_value = np.allclose(window,expect)
assert assertion_value

import torch
def log_ndtr(input_tensor: torch.Tensor) -> torch.Tensor:
    import numpy as np
    from scipy.stats import norm
    output = torch.from_numpy(norm.logcdf(input_tensor.numpy()))
    return output

# --- test ---
from scipy.stats import norm
input_tensor = torch.linspace(-10, 10, steps=20)
expected_result = torch.tensor([-5.3231e+01, -4.3150e+01, -3.4164e+01, -2.6270e+01, -1.9462e+01,
        -1.3734e+01, -9.0731e+00, -5.4610e+00, -2.8617e+00, -1.2062e+00,
        -3.5572e-01, -5.8874e-02, -4.2585e-03, -1.1471e-04, -1.0854e-06,
        -3.5303e-09, -3.9019e-12, -1.4546e-15, -1.8203e-19, -7.6199e-24],
       dtype=torch.float64)
assert torch.allclose(log_ndtr(input_tensor), expected_result, rtol=1e-3, atol=1e-3)

import torch
def erf(input_tensor: torch.Tensor) -> torch.Tensor:
    import numpy as np
    from scipy.special import erf as scipy_erf
    output = torch.from_numpy(scipy_erf(input_tensor.numpy()))
    return output

# --- test ---
input_tensor = torch.linspace(0, 10, steps=10)
expected_result = torch.Tensor([0.0000,0.8839,0.9983,1.0000,1.0000,1.0000,1.0000,1.0000,1.0000,1.0000])
assert torch.allclose(erf(input_tensor), expected_result, rtol=1e-3, atol=1e-3)

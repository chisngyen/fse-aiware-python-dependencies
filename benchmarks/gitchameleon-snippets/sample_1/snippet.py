import torch
def gamma_ln(input_tensor: torch.Tensor) -> torch.Tensor:
    import numpy as np
    from scipy.special import gammaln as scipy_gammaln
    output = torch.from_numpy(scipy_gammaln(input_tensor.numpy()))
    return output

# --- test ---
input_tensor = torch.linspace(0, 10, steps=10)
expected_result = torch.Tensor([float('inf'),-0.0545,0.1092,1.0218,2.3770,4.0476,5.9637,8.0806,10.3675,12.8018])
assert torch.allclose(gamma_ln(input_tensor), expected_result, rtol=1e-3, atol=1e-3)

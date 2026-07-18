import torch
def gamma_ln(input_tensor: torch.Tensor) -> torch.Tensor:
    return torch.special.gammaln(input_tensor)

# --- test ---
input_tensor = torch.linspace(0, 10, steps=10)
expected_result = torch.Tensor([torch.inf,-0.0545,0.1092,1.0218,2.3770,4.0476,5.9637,8.0806,10.3675,12.8018])
assert torch.allclose(gamma_ln(input_tensor), expected_result, rtol=1e-3, atol=1e-3)

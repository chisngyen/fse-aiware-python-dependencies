import torch
def erfc(input_tensor: torch.Tensor) -> torch.Tensor:
    return torch.special.erfc(input_tensor)

# --- test ---
input_tensor = torch.linspace(0, 10, steps=10)
expected_result = torch.Tensor([1.0000e+00,1.1610e-01,1.6740e-03,2.4285e-06,3.2702e-10,3.9425e-15,4.1762e-21,3.8452e-28,3.0566e-36,1.4013e-45])
assert torch.allclose(erfc(input_tensor), expected_result, rtol=1e-3, atol=1e-3)

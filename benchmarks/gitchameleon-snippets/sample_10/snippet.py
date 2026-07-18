import torch
def bessel_i1(input_tensor: torch.Tensor) -> torch.Tensor:
    return torch.special.i1(input_tensor)

# --- test ---
input_tensor = torch.linspace(0, 10, steps=10)
expected_result = torch.Tensor([0.0000e+00,6.4581e-01,1.9536e+00,5.3391e+00,1.4628e+01,4.0623e+01,1.1420e+02,3.2423e+02,9.2770e+02,2.6710e+03])
assert torch.allclose(bessel_i1(input_tensor), expected_result, rtol=1e-3, atol=1e-3)

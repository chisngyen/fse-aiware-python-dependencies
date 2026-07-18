import torch
def invert_mask(tensor1: torch.Tensor, tensor2: torch.Tensor) -> torch.BoolTensor:
    return ~(tensor1 < tensor2)

# --- test ---
tensor1 = torch.Tensor([1, 2, 3])
tensor2 = torch.Tensor([3, 1, 2])
expected_mask=torch.Tensor([False, True, True])
assert torch.all(torch.eq(invert_mask(tensor1, tensor2), expected_mask))

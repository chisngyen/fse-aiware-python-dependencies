import kymatio
import torch
from kymatio import Scattering2D
from kymatio.scattering2d.frontend.torch_frontend import ScatteringTorch2D
from typing import Tuple

def compute_scattering(a: torch.Tensor) -> Tuple[torch.Tensor, ScatteringTorch2D]:


    S = Scattering2D(2, (32, 32), frontend='torch')
    S_a = S(a)
    return S, S_a

# --- test ---
import kymatio
a = torch.ones((1, 3, 32, 32))
S, S_a = compute_scattering(a)
assertion_value = isinstance(S_a, torch.Tensor)
assert assertion_value
assertion_value = isinstance(S, kymatio.scattering2d.frontend.torch_frontend.ScatteringTorch2D)
assert assertion_value

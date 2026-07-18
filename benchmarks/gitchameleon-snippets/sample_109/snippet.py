from scipy.spatial import distance
import numpy as np 
def compute_wminkowski(u:np.ndarray, v:np.ndarray, p:int, w:np.ndarray)->np.ndarray:

    return distance.wminkowski(u,v,p=p,w=w)

# --- test ---

u = np.asarray([11,12,13,14,15])
v = np.asarray([1,2,3,4,5])
w = np.asarray([0.1,0.3,0.15,0.25,0.2])
output = compute_wminkowski(u,v,p=3,w=w)
assertion_value   = np.allclose(output, 3.8029524607613916)
assert assertion_value

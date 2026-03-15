import numpy as np

TARGET_DIM = 384

_projection_cache = {}

def project_vector(vector):

    v = np.array(vector)

    dim = len(v)

    if dim == TARGET_DIM:
        return v.tolist()

    if dim not in _projection_cache:

        rng = np.random.default_rng(seed=42)

        matrix = rng.normal(
            size=(dim, TARGET_DIM)
        )

        matrix = matrix / np.sqrt(TARGET_DIM)

        _projection_cache[dim] = matrix

    matrix = _projection_cache[dim]

    projected = np.dot(v, matrix)

    return projected.tolist()

import numpy as np

# Dimensi target default (sering digunakan oleh model-model HuggingFace/Llama)
TARGET_DIM = 384

# Cache internal untuk menyimpan matriks proyeksi agar tidak dibuat ulang
_projection_cache = {}

def project_vector(vector, target_dim=TARGET_DIM):
    """
    Memproyeksikan vektor ke dimensi target menggunakan matriks proyeksi acak.
    Ini memastikan dimensi vektor konsisten sebelum masuk ke database atau clustering.
    """
    if vector is None:
        return None
        
    v = np.array(vector)
    input_dim = len(v)

    # Jika dimensi sudah sesuai, tidak perlu melakukan proyeksi
    if input_dim == target_dim:
        return v.tolist()

    # Membuat matriks proyeksi jika belum ada di cache untuk dimensi input ini
    # Seed 42 memastikan proyeksi selalu konsisten (deterministik)
    if input_dim not in _projection_cache:
        rng = np.random.default_rng(seed=42)
        
        # Inisialisasi matriks proyeksi acak (Gaussian Random Projection)
        matrix = rng.normal(
            loc=0.0, 
            scale=1.0 / np.sqrt(target_dim), 
            size=(input_dim, target_dim)
        )
        _projection_cache[input_dim] = matrix

    matrix = _projection_cache[input_dim]

    # Operasi Dot Product: [1 x input_dim] * [input_dim x target_dim] = [1 x target_dim]
    projected = np.dot(v, matrix)

    return projected.tolist()

def main():
    """Simple test to verify projection logic."""
    print("Testing Vector Projection...")
    test_v = [0.1] * 1536  # Contoh dimensi OpenAI
    result = project_vector(test_v)
    print(f"✅ Projected from 1536 to {len(result)} dimensions.")

if __name__ == "__main__":
    main()

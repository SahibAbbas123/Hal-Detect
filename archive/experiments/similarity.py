import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import mean_absolute_error

def check_similarity(arr1, arr2):
    # Convert to numpy arrays
    # .flatten() ensures that [[...]] becomes [...]
    vec1 = np.array(arr1).flatten().reshape(1, -1)
    vec2 = np.array(arr2).flatten().reshape(1, -1)

    # 1. Cosine Similarity (The most important for embeddings)
    # Measures the angle between vectors. 1.0 = identical, 0 = orthogonal
    cos_sim = cosine_similarity(vec1, vec2)[0][0]

    # 2. Euclidean Distance
    # Measures the straight-line distance between two points. 0.0 = identical
    euclidean_dist = np.linalg.norm(vec1 - vec2)

    # 3. Mean Absolute Error (MAE)
    # The average difference between individual numbers
    mae = mean_absolute_error(vec1.flatten(), vec2.flatten())

    print("-" * 30)
    print(f"Cosine Similarity: {cos_sim:.6f}") 
    print(f"Euclidean Distance: {euclidean_dist:.6f}")
    print(f"Mean Absolute Error: {mae:.6f}")
    print("-" * 30)

    if cos_sim > 0.99:
        print("Result: These arrays are NEARLY IDENTICAL.")
    elif cos_sim > 0.80:
        print("Result: These arrays are VERY SIMILAR.")
    elif cos_sim > 0.50:
        print("Result: These arrays are MODERATELY SIMILAR.")
    else:
        print("Result: These arrays are DIFFERENT.")

# =============================================================================
# PASTE YOUR ARRAYS BELOW
# =============================================================================

# array_1 = [[ 5.04830852e-02, 8.80059376e-02, 4.87482548e-03, 3.62688713e-02, 
#             -1.01811299e-03, 1.91537682e-02, 1.42319305e-02, -1.87865756e-02,
#             # ... paste the rest of the first array here
#             -1.05010256e-01]] 

# array_2 = [[ 5.26744798e-02, 3.32513154e-02, 1.29859997e-02, 3.64929698e-02,
#             2.59235576e-02, -6.75088447e-03, 4.30048071e-02, -5.87659702e-02,
#             # ... paste the rest of the second array here
#             -8.40253383e-02]]

array_1 = np.load('embeddings_1.npy')
array_2 = np.load('embeddings_2.npy')

# Note: Because your arrays are huge, you can also load them from a .txt or .npy file 
# if you save the output of your main.py to a file first.
# =============================================================================

# To make this example runnable immediately with your provided data:
# I'll just use the snippet provided in your prompt.
# In your real file, simply paste the full lists into array_1 and array_2.

try:
    check_similarity(array_1, array_2)
except Exception as e:
    print(f"Error: {e}. Please ensure you pasted the arrays correctly as Python lists.")

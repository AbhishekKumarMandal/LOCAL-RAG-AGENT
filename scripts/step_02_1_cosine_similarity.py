import math


def vector_length(vector):
    """
    Calculates the magnitude/length of a vector.

    Example:
        vector = [4, 3]

        length = sqrt(4^2 + 3^2)
               = sqrt(16 + 9)
               = 5
    """

    squared_sum = 0

    for value in vector:
        squared_sum += value * value

    return math.sqrt(squared_sum)


def dot_product(vector_a, vector_b):
    """
    Calculates the dot product of two vectors.

    Example:
        vector_a = [4, 3]
        vector_b = [8, 6]

        dot product =
        (4 * 8) + (3 * 6)
        = 50
    """

    # Both vectors must have the same number of dimensions.
    #
    # Invalid:
    #
    # [1, 2, 3]
    # [4, 5]
    #
    # A 384-dimensional embedding must be compared
    # with another 384-dimensional embedding.
    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Vectors must have the same dimensions"
        )

    result = 0

    # zip() combines corresponding elements.
    #
    # vector_a = [4, 3]
    # vector_b = [8, 6]
    #
    # zip() gives:
    #
    # (4, 8)
    # (3, 6)
    #
    # Therefore we calculate:
    #
    # (4 * 8) + (3 * 6)
    for a, b in zip(vector_a, vector_b):
        result += a * b

    return result


def cosine_similarity(vector_a, vector_b):
    """
    Calculates cosine similarity.

                    A . B
        cosine = -------------
                   |A| * |B|

    Typical interpretation:

         1  -> same direction
         0  -> perpendicular
        -1  -> opposite direction
    """

    dot = dot_product(vector_a, vector_b)

    length_a = vector_length(vector_a)
    length_b = vector_length(vector_b)

    # A zero vector has no direction.
    #
    # [0, 0]
    #
    # has length = 0.
    #
    # That would cause division by zero.
    if length_a == 0 or length_b == 0:
        raise ValueError(
            "Cosine similarity cannot be calculated for a zero vector"
        )

    return dot / (length_a * length_b)


# This block runs ONLY when this file itself is executed:
#
# python scripts/cosine_similarity.py
#
# It will NOT run when another Python file imports
# cosine_similarity().
if __name__ == "__main__":

    vector_a = [4, 3]
    vector_b = [8, 6]
    vector_c = [-3, 4]

    print(
        "A vs B:",
        cosine_similarity(vector_a, vector_b)
    )

    print(
        "A vs C:",
        cosine_similarity(vector_a, vector_c)
    )
from step_03_1_database_utils import get_connection
from step_01_3_real_embeddings import generate_embedding

def embedding_to_pgvector(embedding):

    """
    Convert a Python list:

    [0.12, -0.03, 0.44]

    into the textual vector format PostgreSQL expects:

    [0.12,-0.03,0.44]
    """

    return "[" + ",".join(
        str(value)
        for value in embedding
    ) + "]"


def save_embedding(content, embedding):

    vector_value = embedding_to_pgvector(embedding)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                    INSERT into embeddings(content, embedding)
                    VALUES(
                        %s,
                        %s::vector
                    )
                ''',
                (content, vector_value)
            )

if __name__ == "__main__":
    # texts = [
    #     "Java is a programming language",
    #     "Java is used for software development",
    #     "Bananas grow in tropical climates"
    # ]

    # for text in texts:

    #     embedding = generate_embedding(
    #         text
    #     )

    #     save_embedding(
    #         text,
    #         embedding
    #     )

    question = "which language is used for software development"
    question_embedding = generate_embedding(question)
    question_vector = embedding_to_pgvector(question_embedding)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                    SELECT content, 1 - (%s::vector <=> embedding) as consine_similarity FROM embeddings 
                    order by (%s::vector <=> embedding)
                ''',
                (question_vector, question_vector)
            )

            results = cursor.fetchall()

    print("\nQuestion:")
    print(question)

    for index, row in enumerate(results, start=1):
        content = row[0]
        cosine_similarity = row[1]

        print(
            f"\nMatch {index}"
        )

        print(
            "Content:",
            content
        )

        print(
            "Cosine similarity:",
            cosine_similarity
        )


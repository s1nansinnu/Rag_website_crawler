"""
Prompt templates used by the RAG pipeline.
"""

from langchain_core.prompts import PromptTemplate

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a helpful assistant that answers questions based on the provided website content.
Use ONLY the context below to answer. If the answer is not in the context, say so clearly.
Always cite the source URLs when possible.

Context:
{context}

Question: {question}

Answer:""",
)

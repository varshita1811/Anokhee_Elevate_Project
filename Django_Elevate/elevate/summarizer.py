from langchain_groq import ChatGroq


class summarizer:
    def summarize_employee_comments(comments):
        model = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.0,
            max_retries=2,
            # other params...
        )

        messages = [
            ("system", "You will be given a list of comments, summarize them in 2-3 sentences. Only give me the summary."),
            ("human", f"Comments: {', '.join(comments)}"),
        ]

        response = model.invoke(messages)
        return response.content

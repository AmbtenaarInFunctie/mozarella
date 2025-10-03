import os
import re

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from structures import ModelResponse

from openai import OpenAI
from typing import Dict, Any

class Model:
    def __init__(self, model_provider: str, model_name: str, n_iterations: int = 25): 
        self._model_provider = model_provider
        self._model_name = model_name
        self._n_iterations = n_iterations
        self._memory = InMemorySaver()
        self._model = self._init_model()

    def _get_system_prompt(self):
        with open(os.getcwd() + "/data/templates/system_prompt.md", "r") as f:
            content = f.read()
            f.close()

        return content

    def _init_model(self):

        agent = create_react_agent(
            model=f'{self._model_provider}:{self._model_name}',  
            tools=[],  
            prompt=self._get_system_prompt(),
            checkpointer=self._memory,
            response_format=ModelResponse
        )

        return agent

    async def _preprocess_support_docs(self, support_docs: Any) -> str:
        if not support_docs or not support_docs[0]:
            return "No support documents available."
        
        formatted_docs = []
        
        for i, result in enumerate(support_docs[0], 1):  # support_docs is a list containing one list of SearchResult objects
            doc_content = f"## Support Document {i}\n"
            
            # Add metadata if available
            if hasattr(result, 'metadata') and result.metadata:
                title = result.metadata.get('metadata:title', 'Unknown Title')
                doc_content += f"**Title:** {title}\n"
                doc_content += f"**URL:** {result.metadata.get('metadata:original_url', 'N/A')}\n"
                doc_content += f"**Domain:** {result.metadata.get('metadata:domain', 'N/A')}\n"
                doc_content += f"**Relevance Score:** {result.score:.4f}\n\n"
            
            # Add the main content
            if hasattr(result, 'content') and result.content:
                # Clean up the content by removing excessive whitespace and formatting
                content = result.content.strip()
                # Remove markdown links that are just empty []() 
                content = content.replace('[]()', '')
                # Remove data:image URLs that clutter the content
                content = re.sub(r'!\[.*?\]\(data:image[^)]+\)', '', content)
                content = re.sub(r'!\[.*?\]\(https://[^)]*\)', '', content)
                # Clean up multiple newlines
                content = re.sub(r'\n{3,}', '\n\n', content)
                
                doc_content += f"**Content:**\n{content}\n"
            
            formatted_docs.append(doc_content)


        return "\n" + "\n".join(formatted_docs) + "\n"

    async def _preprocess_prompt(self, prompt: str, support_docs: Any) -> str:
        
        template = f"""**User Question:** {prompt}

        {await self._preprocess_support_docs(support_docs)}

        **IMPORTANT INSTRUCTIONS:**
        1. Respond in the SAME LANGUAGE as the user's question above
        2. **CRITICAL**: Use ACTUAL URLs in your inline citations, NOT [Doc N]. Format: [https://full-url-here]
        3. Extract the URL from each Support Document's **URL** field and use it in your inline citations
        4. You MUST populate the citations array with Citation objects for EVERY URL you cite
        5. For each Citation object, include ALL required fields:
        - document_id: The URL from the support document
        - document_title: The Title from the support document
        - document_original_url: The URL from the support document
        - document_domain: The Domain from the support document
        - document_number: The Support Document number (1, 2, 3, etc.)
        - relevance_score: The Relevance Score from the support document

        Example inline citation: "Phishing is digital fraud [https://www.kvk.nl/veilig-zakendoen/pas-op-voor-phishing/]"
        NOT: "Phishing is digital fraud [Doc 1]"
        """

        return template
    
    async def run(self, prompt: str, support_docs: Any, user_id: str) -> ModelResponse:

        config = {"configurable": {"thread_id": user_id}}

        response = self._model.invoke(
            {"messages": [{"role": "user", "content": await self._preprocess_prompt(prompt, support_docs)}]},
            config  
        )

        # Extract the structured response from the model output
        structured_response = response.get('structured_response')

        return structured_response

    def __str__(self):
        return f"{self.model_provider}:{self.model_name}"

    def __repr__(self):
        return f"Model(model_provider={self.model_provider}, model_name={self.model_name})"
    
    
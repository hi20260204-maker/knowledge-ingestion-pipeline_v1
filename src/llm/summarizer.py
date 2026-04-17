import os
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LLMSummaryResponse(BaseModel):
    importance_score: int = Field(..., description="Score from 1 to 10 indicating how important or groundbreaking this IT news is.")
    summary: str = Field(..., description="A clear 3-sentence summary of the content.")
    key_points: List[str] = Field(..., description="Array of 2 to 5 key technical takeaways.")
    keywords: List[str] = Field(..., description="Array of 2 to 5 hashtag-style keywords like #AI, #Python")

def summarize_content(clean_content: str, api_key: str = None) -> LLMSummaryResponse:
    """
    Summarize the given content using OpenAI's structured outputs.
    Logs the process intricately.
    """
    logger.info(f"Initiating LLM summarization for content chunk (Length: {len(clean_content)} chars)")
    
    # Normally we load this from env, passed explicitly here for flexibility/testing
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        logger.error("OPENAI_API_KEY is not set. Summarization failed.")
        raise ValueError("API Key is missing")
    
    client = OpenAI(api_key=key)
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior tech lead. Analyze the IT news and output a JSON response. The summary, key_points, and keywords MUST be written in Korean. Stick strictly to the facts and maintain technical accuracy."},
                {"role": "user", "content": f"Summarize this:\n\n{clean_content}"}
            ],
            response_format=LLMSummaryResponse,
        )
        parsed_response = completion.choices[0].message.parsed
        
        logger.info(f"LLM summarization completed. Importance Score: {parsed_response.importance_score}/10")
        logger.info(f"Extracted Keywords: {parsed_response.keywords}")
        
        return parsed_response
        
    except Exception as e:
        logger.error(f"Error during LLM summarization: {str(e)}")
        raise e

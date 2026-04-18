import os
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LLMSummaryResponse(BaseModel):
    summary: str = Field(..., description="A clear 3-sentence summary of the content in Korean.")
    key_points: List[str] = Field(..., description="Array of 2 to 5 key technical takeaways in Korean.")
    topics: List[str] = Field(..., description="Detected tech topics like LLM, Python, Rust, MLOps, etc.")
    tags: List[str] = Field(..., description="Nature of the news: release, architecture, research, case_study, news.")
    confidence_score: float = Field(..., description="Confidence from 0.0 to 1.0 based on information availability.")

def summarize_content(clean_content: str, fetch_mode: str = "full", api_key: str = None) -> LLMSummaryResponse:
    """
    Summarize content and extract tech signals.
    Optimized for Snippet vs Full-body distinction.
    """
    logger.info(f"Initiating Mode-aware LLM analysis (Mode: {fetch_mode}, Length: {len(clean_content)} chars)")
    
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        logger.error("OPENAI_API_KEY is not set. Summarization failed.")
        raise ValueError("API Key is missing")
    
    client = OpenAI(api_key=key)
    
    # Mode-based System Instruction
    if fetch_mode == "snippet":
        system_instruction = (
            "You are a cautious senior tech lead. Analyze a LIMITED SNIPPET of IT news. "
            "1. Output a Korean summary and key points. "
            "2. DO NOT make assumptions beyond the text. Say '정보 부족' if unclear. "
            "3. Provide topics and tags based only on visible text. "
            "4. Start with a baseline confidence_score of 0.6 to 0.7. "
            "5. Stick strictly to facts. No hallucinations."
        )
    else:
        system_instruction = (
            "You are an insightful senior tech lead. Analyze the FULL BODY of IT news. "
            "1. Focus on technical background, core changes, and specific technical points. "
            "2. Provide a deep technical summary in Korean. "
            "3. Extract precise topics and tags. "
            "4. Confidence_score should be generally high (0.8 to 1.0) unless the text is noisy. "
            "5. Maintain high technical accuracy."
        )

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Analyze and Summarize (Mode: {fetch_mode}):\n\n{clean_content}"}
            ],
            response_format=LLMSummaryResponse,
        )
        parsed_response = completion.choices[0].message.parsed
        
        logger.info(f"LLM analysis completed. Topics: {parsed_response.topics}, Confidence: {parsed_response.confidence_score}")
        
        return parsed_response
        
    except Exception as e:
        logger.error(f"Error during LLM analysis: {str(e)}")
        raise e

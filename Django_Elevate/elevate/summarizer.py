import logging
import os
import textwrap
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

# Initialize the huggingface models globally
_tokenizer = None
_model = None

def get_summarizer_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        try:
            logger.info("Loading local summarization model (sshleifer/distilbart-cnn-12-6)...")
            model_name = "sshleifer/distilbart-cnn-12-6"
            _tokenizer = AutoTokenizer.from_pretrained(model_name)
            _model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        except Exception as e:
            logger.error(f"Failed to initialize local summarizer: {e}")
            raise
    return _tokenizer, _model

def chunk_text(text: str, max_chunk_size: int = 3000) -> list:
    """
    Splits text into chunks roughly up to max_chunk_size characters.
    3000 chars is roughly 600-800 tokens, which easily fits inside BART's 1024 token limit.
    """
    return textwrap.wrap(text, width=max_chunk_size, break_long_words=False, break_on_hyphens=False)

def _summarize_text_block(text: str, tokenizer, model) -> str:
    """Helper function to summarize a single block of text (already chunked)"""
    inputs = tokenizer(text, max_length=1024, truncation=True, return_tensors="pt")
    
    # Generate summary with min 10 words, max 60 words for concise output
    summary_ids = model.generate(
        inputs["input_ids"],
        num_beams=4,
        min_length=10,
        max_length=60,
        early_stopping=True
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()

def summarize_employee_comments(comments_list: list) -> str:
    """
    Takes a list of employee comments from various awards/nominations
    and produces a concise 1-2 sentence summary using a local BART model.
    Handles 'unlimited' tokens by chunking the comments if they are too long.
    """
    if not comments_list:
        return ""
        
    # Combine all comments into a single string
    combined_text = " ".join([str(c).strip() for c in comments_list if str(c).strip()])
    
    if len(combined_text.strip()) == 0:
        return ""
        
    try:
        tokenizer, model = get_summarizer_model()
        
        # If the combined text is short, just summarize it directly
        # roughly 1024 tokens = ~4000-5000 chars
        if len(combined_text) <= 4000:
            return _summarize_text_block(combined_text, tokenizer, model)
            
        # If the text is long, chunk it, summarize chunks, and combine summaries
        chunks = chunk_text(combined_text, max_chunk_size=3500)
        chunk_summaries = []
        
        for chunk in chunks:
            summary = _summarize_text_block(chunk, tokenizer, model)
            chunk_summaries.append(summary)
            
        final_combined_text = " ".join(chunk_summaries)
        
        # if the combined summaries are still too long, recursively summarize
        if len(final_combined_text) > 4000:
            return summarize_employee_comments([final_combined_text])
            
        # Final pass to get 1-2 sentences
        return _summarize_text_block(final_combined_text, tokenizer, model)
            
    except Exception as e:
        logger.error(f"Error during local model summarization: {e}")
        return "Failed to generate summary."

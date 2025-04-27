from fastapi import HTTPException
from better_profanity import profanity

# Initialize the profanity filter
profanity.load_censor_words()

def moderate_text(text: str) -> bool:
    """
    Returns True if text is inappropriate, False if it's safe
    Uses better-profanity for offline content moderation
    """
    if not text or not isinstance(text, str):
        return False

    try:
        # Check if text contains profanity
        contains_profanity = profanity.contains_profanity(text)
        
        if contains_profanity:
            print("Text contains inappropriate content")
            return True
        else:
            print("Text is considered safe")
            return False
            
    except Exception as e:
        print(f"Error in text moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in text moderation: {str(e)}")
from transformers import pipeline

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        print("Loading classifier...")
        _classifier = pipeline('text-classification', model='distilbert-base-uncased-finetuned-sst-2-english')
        print("Classifier loaded!")
    return _classifier

def moderate_text(text: str) -> bool:
    """
    Function to check if the text contains inappropriate content (e.g., toxicity).
    Returns True if toxic, False if not.
    """
    classifier = get_classifier()
    result = classifier(text)
    return result[0]['label'] == 'NEGATIVE'
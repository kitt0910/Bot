from transformers import pipeline

# Initialize the sentiment analysis pipeline
sentiment_analysis = pipeline("sentiment-analysis")

# Test the pipeline with an example sentence
result = sentiment_analysis("I love using transformers!")
print(result)
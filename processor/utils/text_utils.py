"""
Text utilities for the News Aggregator processor.
Provides common text processing functions.
"""

import re
import unicodedata
import string
from typing import List, Set, Dict, Any, Optional
import html


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text with HTML tags
        
    Returns:
        Text without HTML tags
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text with irregular whitespace
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove spaces at the beginning and end of lines
    text = re.sub(r'^ +| +$', '', text, flags=re.MULTILINE)
    
    return text.strip()


def remove_urls(text: str) -> str:
    """
    Remove URLs from text.
    
    Args:
        text: Text with URLs
        
    Returns:
        Text without URLs
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    return text


def remove_emails(text: str) -> str:
    """
    Remove email addresses from text.
    
    Args:
        text: Text with email addresses
        
    Returns:
        Text without email addresses
    """
    if not text:
        return ""
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    
    return text


def remove_special_chars(text: str, keep_punctuation: bool = False) -> str:
    """
    Remove special characters from text.
    
    Args:
        text: Text with special characters
        keep_punctuation: Whether to keep punctuation
        
    Returns:
        Text without special characters
    """
    if not text:
        return ""
    
    if keep_punctuation:
        # Keep alphanumeric characters and punctuation
        pattern = r'[^\w\s' + re.escape(string.punctuation) + ']'
        text = re.sub(pattern, '', text)
    else:
        # Keep only alphanumeric characters
        text = re.sub(r'[^\w\s]', '', text)
    
    return text


def remove_numbers(text: str) -> str:
    """
    Remove numbers from text.
    
    Args:
        text: Text with numbers
        
    Returns:
        Text without numbers
    """
    if not text:
        return ""
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    return text


def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode characters.
    
    Args:
        text: Text with Unicode characters
        
    Returns:
        Text with normalized Unicode characters
    """
    if not text:
        return ""
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    return text


def get_ngrams(text: str, n: int = 3) -> List[str]:
    """
    Get n-grams from text.
    
    Args:
        text: Text to get n-grams from
        n: Size of n-grams
        
    Returns:
        List of n-grams
    """
    if not text:
        return []
    
    # Split text into words
    words = text.split()
    
    # Get n-grams
    ngrams = []
    
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)
    
    return ngrams


def get_shingles(text: str, k: int = 3) -> Set[str]:
    """
    Get k-shingles from text.
    
    Args:
        text: Text to get shingles from
        k: Size of shingles
        
    Returns:
        Set of shingles
    """
    if not text:
        return set()
    
    # Split text into words
    words = text.split()
    
    # Get shingles
    shingles = set()
    
    for i in range(len(words) - k + 1):
        shingle = ' '.join(words[i:i+k])
        shingles.add(shingle)
    
    return shingles


def truncate_text(text: str, max_length: int = 1000, add_ellipsis: bool = True) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        add_ellipsis: Whether to add ellipsis
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Truncate text
    truncated = text[:max_length]
    
    # Add ellipsis
    if add_ellipsis:
        truncated += "..."
    
    return truncated


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.
    
    Args:
        text: Text to extract sentences from
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Remove empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def extract_paragraphs(text: str) -> List[str]:
    """
    Extract paragraphs from text.
    
    Args:
        text: Text to extract paragraphs from
        
    Returns:
        List of paragraphs
    """
    if not text:
        return []
    
    # Split text into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Remove empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    # Get sets of words
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def calculate_text_similarity_ngrams(text1: str, text2: str, n: int = 3) -> float:
    """
    Calculate similarity between two texts using n-gram Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        n: Size of n-grams
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    # Get sets of n-grams
    ngrams1 = set(get_ngrams(text1, n))
    ngrams2 = set(get_ngrams(text2, n))
    
    # Calculate Jaccard similarity
    intersection = len(ngrams1.intersection(ngrams2))
    union = len(ngrams1.union(ngrams2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def extract_keywords(text: str, max_keywords: int = 10, min_word_length: int = 3) -> List[str]:
    """
    Extract keywords from text based on frequency.
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords
        min_word_length: Minimum word length
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters
    text = remove_special_chars(text)
    
    # Split into words
    words = text.split()
    
    # Filter words by length
    words = [word for word in words if len(word) >= min_word_length]
    
    # Count word frequencies
    word_counts = {}
    
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    
    # Sort words by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Get top keywords
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    return keywords


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Generate a summary from text by extracting top sentences.
    
    Args:
        text: Text to summarize
        max_sentences: Maximum number of sentences
        
    Returns:
        Summary text
    """
    if not text:
        return ""
    
    # Extract sentences
    sentences = extract_sentences(text)
    
    if not sentences:
        return ""
    
    # If fewer sentences than max_sentences, return all
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    
    # Extract keywords
    keywords = extract_keywords(text, max_keywords=20)
    
    # Score sentences based on keyword presence
    sentence_scores = []
    
    for sentence in sentences:
        score = 0
        
        # Count keywords in sentence
        for keyword in keywords:
            if keyword.lower() in sentence.lower():
                score += 1
        
        # Normalize score by sentence length
        if len(sentence.split()) > 0:
            score = score / len(sentence.split())
        
        sentence_scores.append((sentence, score))
    
    # Sort sentences by score
    sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    
    # Get top sentences
    top_sentences = [sentence for sentence, score in sorted_sentences[:max_sentences]]
    
    # Sort sentences by original order
    original_order = []
    
    for sentence in sentences:
        if sentence in top_sentences:
            original_order.append(sentence)
    
    # Join sentences
    summary = " ".join(original_order)
    
    return summary
"""
Text processing utilities for manipulating and analyzing text content.
"""
import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def chunk_text(text: str, max_chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for processing
    
    Args:
        text: The text to split
        max_chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of the chunk (try to end at sentence boundary)
        end = min(start + max_chunk_size, len(text))
        
        # If we're not at the end, find the last sentence boundary
        if end < len(text):
            # Find the last sentence ending within the chunk
            last_period = text.rfind('.', start, end)
            last_question = text.rfind('?', start, end)
            last_exclamation = text.rfind('!', start, end)
            
            # Find the latest sentence boundary
            sentence_end = max(last_period, last_question, last_exclamation)
            
            if sentence_end > start + max_chunk_size // 2:
                # Use the sentence boundary if it's not too close to the start
                end = sentence_end + 1
        
        # Add the chunk
        chunks.append(text[start:end])
        
        # Move to the next chunk with overlap
        start = end - overlap if end - overlap > start else end
    
    return chunks

def extract_dialogue(text: str) -> List[Dict[str, str]]:
    """
    Extract dialogue from text with speaker attribution
    
    Args:
        text: The text to extract dialogue from
        
    Returns:
        List of dictionaries with 'speaker' and 'dialogue' keys
    """
    # Pattern for dialogue with attribution: "Text," speaker said.
    pattern = r'"([^"]+)"\s*(?:,|\.)\s*(?:([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?)(?:\s+(?:said|asked|replied|answered|shouted|whispered|muttered|exclaimed|responded))'
    
    matches = re.findall(pattern, text)
    dialogue = []
    
    for match in matches:
        if len(match) >= 2 and match[0] and match[1]:
            dialogue.append({
                'dialogue': match[0],
                'speaker': match[1]
            })
    
    # If no matches with explicit attribution, try plain quotes
    if not dialogue:
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, text)
        dialogue = [{'dialogue': q, 'speaker': 'Unknown'} for q in quotes if q]
    
    return dialogue

def identify_scene_breaks(text: str) -> List[int]:
    """
    Identify indices of potential scene breaks in text
    
    Args:
        text: The text to analyze
        
    Returns:
        List of indices where scene breaks likely occur
    """
    # Look for explicit scene break markers
    explicit_markers = [
        r'\n\s*\*\s*\*\s*\*\s*\n',
        r'\n\s*#\s*#\s*#\s*\n',
        r'\n\s*\-\s*\-\s*\-\s*\n',
        r'\n\s*\.\s*\.\s*\.\s*\n',
        r'\n\s*□\s*□\s*□\s*\n',
        r'\n\s*○\s*○\s*○\s*\n',
        r'\n\s*♦\s*♦\s*♦\s*\n'
    ]
    
    break_indices = []
    
    # Find explicit markers
    for marker in explicit_markers:
        for match in re.finditer(marker, text):
            break_indices.append(match.start())
    
    # Also look for paragraph breaks followed by time/location transitions
    transition_patterns = [
        r'\n\n[A-Z][^.!?]*(?:later|hours|minutes|days|weeks|months|years)[^.!?]*[.!?]',
        r'\n\n[A-Z][^.!?]*(?:meanwhile|elsewhere|across|nearby)[^.!?]*[.!?]',
        r'\n\n(?:The next|That|The following)[^.!?]*(?:morning|afternoon|evening|day|night)[^.!?]*[.!?]'
    ]
    
    for pattern in transition_patterns:
        for match in re.finditer(pattern, text):
            break_indices.append(match.start())
    
    # Sort and de-duplicate
    break_indices = sorted(set(break_indices))
    
    return break_indices

def calculate_reading_statistics(text: str) -> Dict[str, Any]:
    """
    Calculate reading statistics for text
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary with reading statistics
    """
    # Split text into words and sentences
    words = re.findall(r'\b\w+\b', text.lower())
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Count syllables (approximate)
    def count_syllables(word: str) -> int:
        """Count syllables in a word (rough approximation)"""
        word = word.lower()
        if len(word) <= 3:
            return 1
            
        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
        
        # Adjust for common patterns
        if word.endswith("e") and not word.endswith("le"):
            count -= 1
        if word.endswith("es") or word.endswith("ed"):
            count -= 1
        if count == 0:
            count = 1
            
        return count
    
    total_syllables = sum(count_syllables(word) for word in words)
    
    # Calculate metrics
    word_count = len(words)
    sentence_count = len(sentences)
    syllable_count = total_syllables
    
    if sentence_count == 0:
        return {
            "word_count": word_count,
            "sentence_count": 0,
            "avg_words_per_sentence": 0,
            "avg_syllables_per_word": 0,
            "flesch_kincaid": 0
        }
    
    avg_words_per_sentence = word_count / sentence_count
    avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0
    
    # Flesch-Kincaid Grade Level
    flesch_kincaid = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": round(avg_words_per_sentence, 2),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        "flesch_kincaid": round(flesch_kincaid, 2)
    }

def analyze_pacing(text: str) -> Dict[str, Any]:
    """
    Analyze the pacing of a text
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary with pacing analysis
    """
    # Split text into chunks of roughly equal size
    chunks = chunk_text(text, max_chunk_size=1000, overlap=0)
    
    # Analyze each chunk
    chunk_stats = []
    
    for i, chunk in enumerate(chunks):
        # Count dialogue versus narrative ratio
        dialogue_lines = extract_dialogue(chunk)
        dialogue_words = sum(len(d['dialogue'].split()) for d in dialogue_lines)
        total_words = len(re.findall(r'\b\w+\b', chunk))
        dialogue_ratio = dialogue_words / total_words if total_words > 0 else 0
        
        # Estimate action intensity by looking for action verbs and descriptive language
        action_verbs = [
            'run', 'jump', 'hit', 'throw', 'push', 'pull', 'grab', 'dash', 'race',
            'fight', 'slam', 'crash', 'explode', 'attack', 'defend', 'strike', 'dodge',
            'sprint', 'charge', 'shoot', 'blast', 'swing', 'duck', 'dive', 'leap'
        ]
        
        action_count = sum(chunk.lower().count(' ' + verb + ' ') for verb in action_verbs)
        action_intensity = action_count / (total_words / 100) if total_words > 0 else 0
        
        # Estimate emotional intensity
        emotion_words = [
            'fear', 'anger', 'joy', 'sadness', 'hate', 'love', 'rage', 'terror',
            'happy', 'sad', 'furious', 'terrified', 'ecstatic', 'depressed', 'worried',
            'anxious', 'excited', 'nervous', 'afraid', 'angry', 'glad', 'upset', 'thrilled'
        ]
        
        emotion_count = sum(chunk.lower().count(' ' + word + ' ') for word in emotion_words)
        emotional_intensity = emotion_count / (total_words / 100) if total_words > 0 else 0
        
        # Add to stats
        chunk_stats.append({
            'chunk': i+1,
            'dialogue_ratio': round(dialogue_ratio, 2),
            'action_intensity': round(action_intensity, 2),
            'emotional_intensity': round(emotional_intensity, 2),
            'total_words': total_words
        })
    
    # Determine pacing profile
    dialogue_trend = [s['dialogue_ratio'] for s in chunk_stats]
    action_trend = [s['action_intensity'] for s in chunk_stats]
    emotion_trend = [s['emotional_intensity'] for s in chunk_stats]
    
    # Detect pacing issues
    pacing_issues = []
    
    # Check for flat pacing (little variation)
    if max(action_trend) - min(action_trend) < 0.2 and max(emotion_trend) - min(emotion_trend) < 0.2:
        pacing_issues.append("Flat pacing - little variation in action or emotional intensity")
    
    # Check for action-heavy sections without emotional balance
    for i, stats in enumerate(chunk_stats):
        if stats['action_intensity'] > 0.5 and stats['emotional_intensity'] < 0.2:
            pacing_issues.append(f"Chunk {i+1}: High action without emotional context")
    
    # Check for dialogue-heavy sections
    for i, stats in enumerate(chunk_stats):
        if stats['dialogue_ratio'] > 0.7:
            pacing_issues.append(f"Chunk {i+1}: Very dialogue-heavy (may slow pacing)")
    
    return {
        'chunk_stats': chunk_stats,
        'dialogue_trend': dialogue_trend,
        'action_trend': action_trend,
        'emotion_trend': emotion_trend,
        'pacing_issues': pacing_issues
    }

def remove_adverbs(text: str) -> str:
    """
    Remove or reduce excessive adverbs (words ending in 'ly')
    
    Args:
        text: The text to process
        
    Returns:
        Text with reduced adverbs
    """
    # Find adverbs but preserve particularly expressive ones
    adverbs_to_keep = [
        'only', 'early', 'really', 'likely', 'nearly', 'barely', 'hardly',
        'certainly', 'definitely', 'absolutely', 'precisely', 'exactly',
        'completely', 'entirely', 'utterly', 'deeply', 'truly', 'fully'
    ]
    
    def should_remove(match):
        adverb = match.group(0).strip()
        if adverb.lower() in adverbs_to_keep:
            return adverb
        return ""
    
    # Look for adverbs followed by space or punctuation
    pattern = r'\b\w+ly\b[\s,.]'
    
    # Remove only a portion of adverbs (every other one)
    matches = list(re.finditer(pattern, text))
    for i, match in enumerate(matches):
        if i % 2 == 0:  # Remove every other adverb
            adverb = match.group(0).strip()
            if adverb.lower() not in adverbs_to_keep:
                space_or_punct = match.group(0)[-1]
                text = text[:match.start()] + space_or_punct + text[match.end():]
    
    return text

def find_repeated_phrases(text: str, min_length: int = 3, min_occurrences: int = 3) -> List[Tuple[str, int]]:
    """
    Find repeated phrases in text
    
    Args:
        text: The text to analyze
        min_length: Minimum number of words in a phrase
        min_occurrences: Minimum number of occurrences to report
        
    Returns:
        List of tuples with phrase and occurrence count
    """
    # Normalize text for comparison
    normalized = text.lower()
    words = normalized.split()
    
    # Find repeated word sequences
    phrases = {}
    
    for i in range(len(words) - min_length + 1):
        phrase = ' '.join(words[i:i+min_length])
        phrases[phrase] = phrases.get(phrase, 0) + 1
    
    # Filter by occurrence count
    repeated = [(phrase, count) for phrase, count in phrases.items() if count >= min_occurrences]
    
    # Sort by occurrence count (descending)
    repeated.sort(key=lambda x: x[1], reverse=True)
    
    return repeated
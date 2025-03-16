"""
Character Designer Agent
Specializes in creating detailed character profiles and ensuring character consistency.
"""
import logging
from typing import Dict, Any, List, Optional
from core.agent import Agent

logger = logging.getLogger(__name__)

class CharacterDesignerAgent(Agent):
    """
    Agent specialized in creating and developing characters for stories.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Character Designer Agent"""
        super().__init__(name="Character Designer", config=config, llm_provider=llm_provider)
    
    def create_character_profiles(self, outline: str, genre: str) -> str:
        """
        Create detailed character profiles based on a story outline
        
        Args:
            outline: The story outline
            genre: The genre of the story
            
        Returns:
            Detailed character profiles
        """
        logger.info(f"Creating character profiles for {genre} story")
        
        profiles_prompt = f"""
        Based on the following {genre} story outline, create detailed profiles for the main characters.
        
        Story Outline:
        {outline}
        
        Analyze the outline to identify all important characters. For each character, provide a comprehensive profile including:

        1. Character Name: Full name and any nicknames or titles
        
        2. Role in Story: Protagonist, antagonist, supporting character, etc.
        
        3. Physical Description:
           - Age, gender, appearance
           - Distinctive physical traits
           - Typical clothing/style
        
        4. Background:
           - Personal history relevant to the story
           - Family connections
           - Cultural/social context
        
        5. Personality:
           - Core traits (3-5 defining characteristics)
           - Strengths and weaknesses
           - Values and beliefs
           - Habits and quirks
        
        6. Goals and Motivations:
           - Primary goal in the story
           - Underlying motivations
           - Conflicts (internal and external)
        
        7. Character Arc:
           - Starting state
           - Key development points
           - Ending state/transformation
        
        8. Relationships:
           - Connections to other characters
           - Evolution of key relationships through the story
        
        9. Voice/Speech Patterns:
           - Typical vocabulary and syntax
           - Verbal tics or catchphrases
           - Communication style
        
        Format each profile with clear headings and structure. Make sure each character feels distinct and three-dimensional,
        with clear arcs relevant to the story's theme and plot. Ensure the profiles align with genre expectations for {genre}.
        
        Prioritize consistency with the outline while adding depth that enriches the story.
        """
        
        return self.generate(profiles_prompt, temperature=0.7)
    
    def analyze_character_consistency(self, chapters: List[str], character_profiles: str) -> Dict[str, Any]:
        """
        Analyze character consistency across chapters
        
        Args:
            chapters: List of chapter content
            character_profiles: Character profiles
            
        Returns:
            Dictionary with consistency analysis
        """
        # For efficiency, analyze a sample of chapters
        sample_chapters = []
        if len(chapters) <= 3:
            sample_chapters = chapters
        else:
            sample_chapters = [chapters[0], chapters[len(chapters)//2], chapters[-1]]
        
        sample_text = "\n\n---CHAPTER BREAK---\n\n".join(sample_chapters)
        
        analysis_prompt = f"""
        Analyze character consistency in the following story excerpts based on the established character profiles.
        
        Character Profiles:
        {character_profiles}
        
        Story Excerpts:
        {sample_text}
        
        For each main character, evaluate consistency across these dimensions:
        1. Personality traits
        2. Voice and speech patterns
        3. Goal-oriented behavior
        4. Relationship dynamics
        5. Character development progression
        
        Identify any inconsistencies, including:
        - Contradictory behavior
        - Out-of-character actions or dialogue
        - Sudden unexplained personality changes
        - Forgotten knowledge or skills
        - Relationship inconsistencies
        
        Format your response as JSON with these fields:
        - "characters": Array of analyzed characters
        - "consistency_issues": Array of specific issues found
        - "suggestions": Array of fixes for each issue
        - "overall_rating": Number from 1-10 of overall character consistency
        """
        
        response = self.generate(analysis_prompt, temperature=0.4)
        return self.parse_json_response(response, default={"consistency_issues": []})
    
    def develop_character_arc(self, character_name: str, character_profile: str, outline: str) -> Dict[str, Any]:
        """
        Develop a detailed character arc
        
        Args:
            character_name: The character's name
            character_profile: The character's profile
            outline: The story outline
            
        Returns:
            Detailed character arc information
        """
        arc_prompt = f"""
        Develop a detailed character arc for '{character_name}' based on their profile and the story outline.
        
        Character Profile:
        {character_profile}
        
        Story Outline:
        {outline}
        
        Create a comprehensive character arc that tracks their development through each stage of the story.
        
        Include:
        1. Starting State: The character's initial condition, beliefs, flaws, and situation
        
        2. Inciting Incident: How the story's events first impact this character
        
        3. Progressive Complications: Key challenges that force character growth
        
        4. Turning Points: Moments of significant internal change or decision
        
        5. Crisis Points: Major dilemmas that test the character's values
        
        6. Climactic Choice: The ultimate decision that defines their arc
        
        7. Resolution State: How they've changed by the end of the story
        
        8. Chapter-by-Chapter Development: Brief notes on their progression in each chapter
        
        Format your response as JSON with these sections clearly labeled.
        """
        
        response = self.generate(arc_prompt, temperature=0.7)
        return self.parse_json_response(response, default={"character_arc": {}})
    
    def create_character_relationships(self, character_profiles: str) -> Dict[str, Any]:
        """
        Define relationships between characters
        
        Args:
            character_profiles: Character profiles
            
        Returns:
            Character relationship map
        """
        relationships_prompt = f"""
        Based on the following character profiles, create a detailed relationship map between all major characters.
        
        Character Profiles:
        {character_profiles}
        
        For each possible pair of characters, define:
        1. The nature of their relationship (family, friends, rivals, etc.)
        2. The history between them (how they met, significant events)
        3. Current dynamics (trust levels, power dynamics, tensions)
        4. Evolution of the relationship throughout the story
        5. Key conflicts or bonds that drive plot developments
        
        Format your response as JSON with character names as keys and relationship details as values.
        Make sure to account for how relationships might evolve through the story.
        """
        
        response = self.generate(relationships_prompt, temperature=0.6)
        return self.parse_json_response(response, default={"relationships": {}})
    
    def create_dialogue_samples(self, character_name: str, character_profile: str, situations: List[str]) -> Dict[str, List[str]]:
        """
        Create sample dialogue for a character in different situations
        
        Args:
            character_name: The character's name
            character_profile: The character's profile
            situations: List of situations for dialogue samples
            
        Returns:
            Dictionary mapping situations to dialogue samples
        """
        situations_text = "\n".join([f"- {s}" for s in situations])
        
        dialogue_prompt = f"""
        Create sample dialogue for the character '{character_name}' in various situations,
        based on their profile.
        
        Character Profile:
        {character_profile}
        
        Write dialogue samples for this character in each of these situations:
        {situations_text}
        
        For each situation, provide:
        1. A brief snippet of dialogue (3-5 lines) showing how this character would speak
        2. Notes on their tone, word choice, and speech patterns
        
        Ensure the dialogue is consistent with the character's personality, background, and emotional state.
        Format your response as JSON with situations as keys and dialogue samples with notes as values.
        """
        
        response = self.generate(dialogue_prompt, temperature=0.7)
        return self.parse_json_response(response, default={"dialogue_samples": {}})
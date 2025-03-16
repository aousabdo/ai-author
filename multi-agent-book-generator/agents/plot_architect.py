"""
Plot Architect Agent
Responsible for creating coherent plot outlines and story structures.
"""
import logging
from typing import Dict, Any, List, Optional
from core.agent import Agent

logger = logging.getLogger(__name__)

class PlotArchitectAgent(Agent):
    """
    Agent specialized in constructing plot outlines and story structures.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Plot Architect Agent"""
        super().__init__(name="Plot Architect", config=config, llm_provider=llm_provider)
    
    def create_outline(self, genre: str, description: str, num_chapters: int, writing_style: str) -> str:
        """
        Create a detailed chapter-by-chapter outline for a book
        
        Args:
            genre: The genre of the book
            description: A high-level description of the book
            num_chapters: The number of chapters to include
            writing_style: The desired writing style
            
        Returns:
            A detailed chapter-by-chapter outline
        """
        logger.info(f"Creating outline for {genre} book with {num_chapters} chapters")
        
        outline_prompt = f"""
        Create a detailed chapter-by-chapter outline for a {num_chapters}-chapter {genre} novel 
        written in the {writing_style} style, based on the following description:

        {description}

        For each chapter, provide:
        1. A brief title that captures the essence of the chapter
        2. A summary of key events and character developments (100-200 words)
        3. An estimated word count for the chapter (between 2,000-5,000 words)

        Use this consistent format for each chapter:

        Chapter 1: [Title]
        Summary: [100-200 word summary of events and character developments]
        Estimated word count: [number]

        Chapter 2: [Title]
        Summary: [100-200 word summary]
        Estimated word count: [number]

        And so on...

        Ensure the outline:
        - Covers a complete story arc with proper pacing (setup, rising action, climax, resolution)
        - Includes compelling character development throughout
        - Contains appropriate plot points for the {genre} genre
        - Varies the chapter lengths as appropriate for the content and pacing
        - Has clear cause-and-effect relationships between chapters
        - Builds tension and maintains momentum throughout
        - Resolves the major conflicts by the end

        Make sure the outline is cohesive, engaging, and follows traditional narrative structure while
        being appropriate for the {genre} genre and {writing_style} style.
        """
        
        return self.generate(outline_prompt, temperature=0.7)
    
    def enhance_outline(self, outline: str, feedback: str) -> str:
        """
        Enhance an existing outline based on feedback
        
        Args:
            outline: The existing outline
            feedback: Feedback for improvement
            
        Returns:
            An enhanced outline
        """
        enhance_prompt = f"""
        Enhance the following book outline based on the provided feedback.
        
        Current Outline:
        {outline}
        
        Feedback for Improvement:
        {feedback}
        
        Provide a revised outline that addresses all the feedback points while maintaining 
        the same format and general structure. Focus on improving narrative cohesion, character 
        development, and plot progression.
        
        Make sure each chapter still includes a title, summary, and estimated word count.
        """
        
        return self.generate(enhance_prompt, temperature=0.7)
    
    def create_story_world(self, genre: str, outline: str) -> str:
        """
        Create detailed world-building for the story
        
        Args:
            genre: The genre of the book
            outline: The existing plot outline
            
        Returns:
            Detailed world-building for the story
        """
        worldbuilding_prompt = f"""
        Based on the following outline for a {genre} novel, create detailed world-building elements.
        
        Outline:
        {outline}
        
        Provide comprehensive world-building details about:
        
        1. Setting:
           - Primary locations and their unique characteristics
           - Historical context relevant to the story
           - Social structures, governments, or systems
           - Relevant cultural details
        
        2. Rules/Magic/Technology:
           - For fantasy: magic systems and their rules/limitations
           - For sci-fi: technology and scientific principles
           - For other genres: special rules or systems unique to the world
        
        3. Timeline:
           - Key historical events that impact the story
           - Important dates or time periods
           - Seasonal or cyclical events relevant to the plot
        
        Format your response as a comprehensive world-building guide that would help a writer
        maintain consistency throughout the novel.
        """
        
        return self.generate(worldbuilding_prompt, temperature=0.7)
    
    def develop_plot_threads(self, outline: str, num_threads: int = 3) -> Dict[str, List[str]]:
        """
        Develop secondary plot threads that run through the story
        
        Args:
            outline: The existing plot outline
            num_threads: Number of secondary plot threads to develop
            
        Returns:
            Dictionary mapping thread names to their chapter-by-chapter progressions
        """
        threads_prompt = f"""
        Based on the following book outline, develop {num_threads} secondary plot threads that
        weave throughout the story, complementing the main plot.
        
        Book Outline:
        {outline}
        
        For each secondary plot thread:
        1. Provide a name or theme for the thread
        2. Briefly describe its overall purpose in the story
        3. Track its progression chapter by chapter, explaining how it develops
        
        Format your response as JSON with the following structure:
        {{
            "thread_name": {{
                "purpose": "Overall purpose and meaning of this thread",
                "progression": [
                    "Chapter 1: What happens with this thread in chapter 1",
                    "Chapter 2: What happens with this thread in chapter 2",
                    ...
                ]
            }},
            ...
        }}
        """
        
        response = self.generate(threads_prompt, temperature=0.7)
        return self.parse_json_response(response, default={"threads": []})
    
    def create_plot_twist(self, outline: str, character_profiles: str, chapter_num: int) -> str:
        """
        Create a compelling plot twist for a specific chapter
        
        Args:
            outline: The existing plot outline
            character_profiles: Character profiles
            chapter_num: The chapter number for the twist
            
        Returns:
            Description of the plot twist and its implementation
        """
        twist_prompt = f"""
        Create a compelling and unexpected plot twist for Chapter {chapter_num} in the
        following story outline, using the established characters.
        
        Story Outline:
        {outline}
        
        Character Profiles:
        {character_profiles}
        
        Provide:
        1. A brief description of the plot twist
        2. How it would be revealed in the chapter
        3. Its impact on the characters and overall story
        4. How it connects to previous events (foreshadowing)
        5. How to integrate it naturally into the existing outline
        
        The twist should be surprising but logical - it should make sense within the
        established world and character motivations, even if readers didn't see it coming.
        """
        
        return self.generate(twist_prompt, temperature=0.8)
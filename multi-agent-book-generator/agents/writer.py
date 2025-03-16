"""
Writer Agent
Specializes in generating creative content based on outlines and character profiles.
"""
import logging
from typing import Dict, Any, List, Optional
from core.agent import Agent

logger = logging.getLogger(__name__)

class WriterAgent(Agent):
    """
    Agent specialized in writing creative content for stories.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Writer Agent"""
        super().__init__(name="Writer", config=config, llm_provider=llm_provider)
    
    def write_chapter(self, chapter_info: Dict[str, Any], previous_chapters: List[str], 
                     character_profiles: str, writing_style: str) -> str:
        """
        Write a chapter based on the outline and previous chapters
        
        Args:
            chapter_info: Information about the chapter to write
            previous_chapters: Content of previous chapters
            character_profiles: Character profiles
            writing_style: The desired writing style
            
        Returns:
            The written chapter
        """
        chapter_num = chapter_info.get("chapter_num", 1)
        chapter_title = chapter_info.get("title", f"Chapter {chapter_num}")
        chapter_summary = chapter_info.get("summary", "")
        target_word_count = chapter_info.get("word_count", 3000)
        
        logger.info(f"Writing chapter {chapter_num}: {chapter_title} ({target_word_count} words)")
        
        # Create context based on previous chapters
        prev_chapters_context = ""
        if previous_chapters:
            # For token efficiency, summarize previous chapters instead of including full text
            prev_chapters_context = "\n\nContext from previous chapters (for continuity):\n"
            for i, prev_chapter in enumerate(previous_chapters[-2:]):  # Only include last 2 chapters
                prev_idx = chapter_num - len(previous_chapters[-2:]) + i
                # Extract first 200 words and last 200 words for context
                prev_words = prev_chapter.split()
                start_context = " ".join(prev_words[:200]) if len(prev_words) > 200 else prev_chapter
                end_context = " ".join(prev_words[-200:]) if len(prev_words) > 400 else ""
                
                prev_chapters_context += f"Chapter {prev_idx} beginning: {start_context}\n\n"
                if end_context:
                    prev_chapters_context += f"Chapter {prev_idx} ending: {end_context}\n\n"
        
        # Create a prompt for the chapter
        chapter_prompt = f"""
        Write Chapter {chapter_num}: "{chapter_title}" for a story in the {writing_style} style.
        
        Chapter Summary:
        {chapter_summary}
        
        Character Information (reference for consistency):
        {character_profiles[:2000]}...
        {prev_chapters_context}
        
        Guidelines:
        - Target word count: Approximately {target_word_count} words
        - Writing style: {writing_style}
        - Include vivid description, engaging dialogue, and meaningful character development
        - Focus on showing rather than telling
        - Maintain consistent character voices based on their profiles
        - Advance the plot as outlined in the chapter summary
        - End the chapter in a way that encourages the reader to continue
        
        Begin the chapter directly with the narrative, without including the chapter number or title.
        """
        
        # If the target word count is large, we might need to chunk the generation
        if target_word_count > 3000:
            return self._write_long_chapter(chapter_prompt, target_word_count)
        else:
            return self.generate(chapter_prompt, temperature=0.7)
    
    def _write_long_chapter(self, initial_prompt: str, target_word_count: int, max_chunks: int = 3) -> str:
        """
        Write a long chapter by generating it in chunks
        
        Args:
            initial_prompt: The prompt for the first chunk
            target_word_count: Target word count for the chapter
            max_chunks: Maximum number of chunks to generate
            
        Returns:
            The complete chapter
        """
        chunks = []
        total_words = 0
        words_per_chunk = min(2500, target_word_count // max_chunks)
        
        # Generate the first chunk
        logger.info(f"Generating chunk 1/{max_chunks} for long chapter")
        first_chunk = self.generate(initial_prompt, temperature=0.7)
        chunks.append(first_chunk)
        
        # Count words
        chunk_words = len(first_chunk.split())
        total_words += chunk_words
        logger.info(f"Chunk 1 generated: {chunk_words} words")
        
        # Generate additional chunks if needed
        for i in range(2, max_chunks + 1):
            if total_words >= target_word_count:
                break
                
            remaining_words = target_word_count - total_words
            
            # If what's left is small, just add it to the current chunk target
            if remaining_words < 1000:
                words_per_chunk = remaining_words
            
            logger.info(f"Generating chunk {i}/{max_chunks} for long chapter")
            
            continuation_prompt = f"""
            Continue the following chapter, adding approximately {words_per_chunk} more words.
            Maintain the same style, tone, and character voices.
            Pick up exactly where the previous section left off without any recapping or transition phrases.
            
            Previous section:
            {chunks[-1][-500:]}
            
            Continue directly from this point:
            """
            
            next_chunk = self.generate(continuation_prompt, temperature=0.7)
            chunks.append(next_chunk)
            
            chunk_words = len(next_chunk.split())
            total_words += chunk_words
            logger.info(f"Chunk {i} generated: {chunk_words} words (total: {total_words})")
        
        # Combine chunks
        full_chapter = "\n\n".join(chunks)
        return full_chapter
    
    def revise_chapter(self, chapter: str, feedback: str) -> str:
        """
        Revise a chapter based on feedback
        
        Args:
            chapter: The chapter content to revise
            feedback: Revision feedback
            
        Returns:
            The revised chapter
        """
        revision_prompt = f"""
        Revise the following chapter based on the provided feedback.
        
        Original Chapter:
        {chapter[:3000]}... [truncated for length]
        
        Feedback:
        {feedback}
        
        Provide a revised version that addresses all the feedback points while maintaining the same
        overall narrative, plot points, and character development. Keep the same approximate length.
        
        The revision should improve the writing while staying true to the original chapter's content and purpose.
        """
        
        return self.generate(revision_prompt, temperature=0.7)
    
    def generate_chapter_title(self, chapter_content: str) -> str:
        """
        Generate a title for a chapter based on its content
        
        Args:
            chapter_content: The content of the chapter
            
        Returns:
            A chapter title
        """
        title_prompt = f"""
        Create an engaging and appropriate title for the following book chapter.
        The title should:
        - Capture the essence of the chapter's content
        - Be concise (1-6 words)
        - Intrigue the reader without giving away major twists
        - Maintain a consistent style with a literary work
        
        Chapter Content (excerpt):
        {chapter_content[:2000]}...
        
        Respond with ONLY the title, nothing else.
        """
        
        title = self.generate(title_prompt, temperature=0.7, max_tokens=20)
        
        # Clean up the title
        title = title.strip().strip('"\'').strip()
        if ':' in title and not title.startswith('Chapter'):
            # Remove "Chapter X:" prefix if present
            title = title.split(':', 1)[1].strip()
            
        return title
    
    def improve_chapter_hooks(self, chapter_ending: str, next_chapter_beginning: str) -> str:
        """
        Improve the hook at the end of a chapter
        
        Args:
            chapter_ending: The end of the current chapter
            next_chapter_beginning: The beginning of the next chapter
            
        Returns:
            Improved chapter ending with a better hook
        """
        hook_prompt = f"""
        Improve the ending of this chapter to create a stronger hook that leads into the next chapter.
        
        Current chapter ending:
        {chapter_ending}
        
        Beginning of next chapter:
        {next_chapter_beginning}
        
        Rewrite the last paragraph or two of the current chapter to:
        1. Create more anticipation or curiosity
        2. Better connect to what happens in the next chapter
        3. Maintain the same style and tone
        4. Keep the same events but enhance their presentation
        
        Provide ONLY the rewritten ending paragraphs, nothing else.
        """
        
        return self.generate(hook_prompt, temperature=0.7)
    
    def write_specific_scene(self, scene_description: str, characters_involved: str, 
                           writing_style: str, word_count: int = 800) -> str:
        """
        Write a specific scene for a chapter
        
        Args:
            scene_description: Description of the scene to write
            characters_involved: Characters involved in the scene
            writing_style: The desired writing style
            word_count: Target word count for the scene
            
        Returns:
            The written scene
        """
        scene_prompt = f"""
        Write a vivid and engaging scene based on the following description, in a {writing_style} style.
        
        Scene Description:
        {scene_description}
        
        Characters Involved:
        {characters_involved}
        
        Guidelines:
        - Target word count: Approximately {word_count} words
        - Style: {writing_style}
        - Include sensory details (sight, sound, smell, taste, touch)
        - Balance dialogue, action, and description
        - Convey character emotions and internal thoughts where appropriate
        - Create a clear sense of setting and atmosphere
        
        Focus on crafting an immersive scene that advances the story and reveals character.
        """
        
        return self.generate(scene_prompt, temperature=0.7)
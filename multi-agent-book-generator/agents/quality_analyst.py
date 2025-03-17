"""
Quality Analyst Agent
Specializes in evaluating overall book quality and making final improvements.
"""
import logging
from typing import Dict, Any, List, Optional
from core.agent import Agent
from utils.text_processing import calculate_reading_statistics

logger = logging.getLogger(__name__)

class QualityAnalystAgent(Agent):
    """
    Agent specialized in evaluating overall book quality and making final improvements.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Quality Analyst Agent"""
        super().__init__(name="Quality Analyst", config=config, llm_provider=llm_provider)
    
    def evaluate_book_quality(self, chapters: List[str], character_profiles: str, 
                             outline: str, genre: str, writing_style: str) -> Dict[str, Any]:
        """
        Perform a comprehensive quality assessment of the entire book
        
        Args:
            chapters: List of all chapters
            character_profiles: Character profiles
            outline: Original book outline
            genre: Book genre
            writing_style: Target writing style
            
        Returns:
            Comprehensive quality assessment
        """
        logger.info("Performing comprehensive book quality assessment")
        
        # Calculate reading statistics
        reading_stats = {}
        total_word_count = 0
        
        for i, chapter in enumerate(chapters):
            chapter_stats = calculate_reading_statistics(chapter)
            reading_stats[f"chapter_{i+1}"] = chapter_stats
            total_word_count += chapter_stats.get("word_count", 0)
        
        # Create a book sample for analysis (intro, middle, end)
        book_sample = ""
        if chapters:
            book_sample = (
                f"BEGINNING:\n{chapters[0][:1500]}...\n\n"
                f"MIDDLE:\n{chapters[len(chapters)//2][:1500]}...\n\n"
                f"END:\n{chapters[-1][:1500]}..."
            )
        
        # Convert outline to a brief summary for the prompt
        outline_summary = outline[:1500] + "..." if len(outline) > 1500 else outline
        
        assessment_prompt = f"""
        Perform a comprehensive quality assessment of this book.
        
        Genre: {genre}
        Writing Style: {writing_style}
        Total Word Count: {total_word_count}
        
        Book Outline Summary:
        {outline_summary}
        
        Book Excerpts:
        {book_sample}
        
        Evaluate the following aspects:
        
        1. Plot and Structure:
           - Coherence and logical progression
           - Completeness of story arc
           - Effective setup and payoff
           - Pacing and rhythm
        
        2. Character Development:
           - Depth and dimensionality
           - Consistency and believability
           - Character arcs and growth
           - Distinctiveness of characters
        
        3. Writing Craft:
           - Prose quality and clarity
           - Style consistency with target ({writing_style})
           - Balance of showing vs telling
           - Dialogue effectiveness
        
        4. Genre Elements:
           - Adherence to {genre} conventions
           - Fulfillment of genre expectations
           - Originality within genre constraints
        
        5. Overall Impact:
           - Emotional resonance
           - Thematic coherence
           - Memorability
           - Reader engagement
        
        For each aspect, provide:
        - A detailed assessment
        - Specific strengths
        - Areas for improvement
        - A numerical score (1-10)
        
        Also identify any critical issues that must be addressed.
        
        Format your response as JSON with these categories and subcategories.
        """
        
        response = self.generate(assessment_prompt, temperature=0.4)
        quality_assessment = self.parse_json_response(response, default={
            "plot_and_structure": {"score": 5},
            "character_development": {"score": 5},
            "writing_craft": {"score": 5},
            "genre_elements": {"score": 5},
            "overall_impact": {"score": 5},
            "critical_issues": []
        })
        
        # Calculate overall scores
        scores = {}
        for category in ["plot_and_structure", "character_development", "writing_craft", 
                         "genre_elements", "overall_impact"]:
            if category in quality_assessment:
                scores[category] = quality_assessment[category].get("score", 5)
        
        if scores:
            scores["overall"] = sum(scores.values()) / len(scores)
        else:
            scores["overall"] = 5
        
        quality_assessment["scores"] = scores
        quality_assessment["reading_stats"] = reading_stats
        
        logger.info(f"Quality assessment complete. Overall score: {scores['overall']:.1f}/10")
        return quality_assessment
    
    def generate_title(self, chapters: List[str], outline: str, genre: str) -> str:
        """
        Generate a compelling title for the book
        
        Args:
            chapters: List of chapters (or at least the first few)
            outline: Book outline
            genre: Book genre
            
        Returns:
            Generated title
        """
        # Use first chapter and outline for context
        first_chapter = chapters[0][:2000] if chapters else ""
        outline_sample = outline[:1500] if len(outline) > 1500 else outline
        
        title_prompt = f"""
        Generate a compelling and marketable title for this {genre} book.
        
        Book Outline:
        {outline_sample}
        
        First Chapter Excerpt:
        {first_chapter}
        
        Create 5 potential titles that:
        - Capture the essence of the story
        - Appeal to {genre} readers
        - Are memorable and distinctive
        - Hint at the main theme or conflict
        - Are appropriate for the content and tone
        
        For each title, provide a brief explanation of why it works.
        Then select the best title and explain why it's the strongest option.
        
        Format your response as JSON with "titles" (array of options with explanations) 
        and "best_title" (the single best title).
        """
        
        response = self.generate(title_prompt, temperature=0.8)
        result = self.parse_json_response(response, default={"best_title": "Untitled"})
        
        # return result.get("best_title", "Untitled")
           
        # Extract the title string - ensure we're returning a string, not a dict
        title = result.get("best_title", "Untitled")
        if isinstance(title, dict) and 'title' in title:
            title = title['title']
        elif not isinstance(title, str):
            title = "Untitled"
        
        return title
    
    def fix_critical_issues(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Fix critical quality issues in a chapter
        
        Args:
            chapter: Chapter content
            issues: List of critical issues to fix
            
        Returns:
            Updated chapter with issues fixed
        """
        if not issues:
            return chapter
        
        # Format issues for the prompt
        issues_text = "\n".join([
            f"{i+1}. {issue.get('description', 'Unspecified issue')}"
            for i, issue in enumerate(issues)
        ])
        
        fix_prompt = f"""
        Revise this chapter to fix the following critical quality issues.
        
        Chapter content:
        {chapter[:2000]}...
        [middle of chapter omitted for brevity]
        ...{chapter[-2000:]}
        
        Critical issues to fix:
        {issues_text}
        
        Instructions:
        1. Address each critical issue while preserving the original story elements
        2. Maintain the same basic events and character interactions
        3. Keep a similar chapter length
        4. Focus specifically on fixing the identified issues
        
        Return the complete revised chapter with all issues addressed.
        """
        
        # For longer chapters, use a more targeted approach
        if len(chapter) > 8000:
            return self._fix_issues_in_long_chapter(chapter, issues)
        
        return self.generate(fix_prompt, temperature=0.6)
    
    def _fix_issues_in_long_chapter(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Fix issues in a long chapter by addressing them one by one
        
        Args:
            chapter: Chapter content
            issues: List of issues to fix
            
        Returns:
            Updated chapter with issues fixed
        """
        # Apply fixes sequentially
        updated_chapter = chapter
        
        for i, issue in enumerate(issues):
            description = issue.get('description', '')
            
            if not description:
                continue
                
            # Check if issue mentions specific text to fix
            target_text = issue.get('text', '')
            
            if target_text and target_text in updated_chapter:
                # If we have specific text to fix, create a targeted prompt
                fix_prompt = f"""
                Rewrite this specific passage to fix this issue: "{description}"
                
                Original passage:
                {target_text}
                
                Provide only the rewritten passage that fixes the issue while maintaining the
                same basic meaning and purpose. Match the surrounding style and tone.
                """
                
                fixed_passage = self.generate(fix_prompt, temperature=0.6)
                
                # Replace the problematic passage
                updated_chapter = updated_chapter.replace(target_text, fixed_passage)
            else:
                # For general issues without specific text, apply a general improvement
                logger.info(f"Applying general fix for issue: {description}")
                
                # We'll skip general fixes for very long chapters as they're less effective
                # and more likely to cause problems
                continue
        
        return updated_chapter
    
    def improve_opening_chapter(self, chapter: str, outline: str, genre: str) -> str:
        """
        Improve the opening chapter to better hook readers
        
        Args:
            chapter: Opening chapter content
            outline: Book outline
            genre: Book genre
            
        Returns:
            Improved opening chapter
        """
        opening_prompt = f"""
        Improve the opening chapter of this {genre} book to better hook readers.
        
        Original opening chapter:
        {chapter[:3000]}...
        
        Book outline:
        {outline[:1000]}...
        
        Enhance the opening to:
        1. Create a stronger hook in the first paragraph
        2. Establish the protagonist and their situation more compellingly
        3. Introduce the main conflict or question more clearly
        4. Set the tone and atmosphere more effectively
        5. Use more engaging and vivid language
        
        Maintain the same basic events and character introductions, but make the opening
        more captivating for {genre} readers. Focus especially on the first few pages.
        
        Provide a revised version of the opening chapter (at least the first 1000-2000 words).
        """
        
        return self.generate(opening_prompt, temperature=0.7)
    
    def improve_ending_chapter(self, chapter: str, previous_chapter: str, outline: str) -> str:
        """
        Improve the final chapter for a more satisfying conclusion
        
        Args:
            chapter: Final chapter content
            previous_chapter: Second-to-last chapter content
            outline: Book outline
            
        Returns:
            Improved final chapter
        """
        ending_prompt = f"""
        Improve the final chapter of this book to create a more satisfying conclusion.
        
        Previous chapter (excerpt):
        {previous_chapter[-1500:]}
        
        Final chapter:
        {chapter}
        
        Book outline (ending section):
        {outline[-1000:]}
        
        Enhance the ending to:
        1. Resolve the main conflicts and story arcs more satisfyingly
        2. Provide emotional closure for key characters
        3. Reinforce the book's core themes
        4. Create a more memorable final impression
        5. Tie up loose ends while maintaining appropriate ambiguity
        
        Maintain the same basic resolution and outcomes, but make the execution more
        impactful and resonant. The improved ending should feel earned and meaningful.
        
        Provide a revised version of the final chapter.
        """
        
        return self.generate(ending_prompt, temperature=0.7)
    
    def evaluate_marketability(self, title: str, first_chapter: str, 
                              outline: str, genre: str) -> Dict[str, Any]:
        """
        Evaluate the marketability of the book
        
        Args:
            title: Book title
            first_chapter: Opening chapter content
            outline: Book outline
            genre: Book genre
            
        Returns:
            Marketability assessment
        """
        market_prompt = f"""
        Evaluate the marketability of this {genre} book.
        
        Title: {title}
        
        Book Outline:
        {outline[:1500]}...
        
        First Chapter Excerpt:
        {first_chapter[:1500]}...
        
        Assess the following aspects of marketability:
        
        1. Title Appeal:
           - Memorability and distinctiveness
           - Genre appropriateness
           - Commercial potential
        
        2. Hook Strength:
           - Opening paragraph effectiveness
           - Reader engagement potential
           - Commercial appeal of the premise
        
        3. Genre Fit:
           - Alignment with {genre} reader expectations
           - Uniqueness within the genre
           - Marketable tropes and elements
        
        4. Target Audience:
           - Primary demographic appeal
           - Potential reader segments
           - Comparable successful titles
        
        5. Selling Points:
           - Key marketable elements
           - Potential cover/blurb highlights
           - Unique selling propositions
        
        Format your response as JSON with these categories and a "marketability_score" (1-10)
        for the book's overall commercial potential.
        """
        
        response = self.generate(market_prompt, temperature=0.5)
        return self.parse_json_response(response, default={"marketability_score": 5})
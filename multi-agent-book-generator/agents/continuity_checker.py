"""
Continuity Checker Agent
Specializes in analyzing and fixing narrative continuity issues.
"""
import logging
import re
from typing import Dict, Any, List, Optional
from core.agent import Agent

logger = logging.getLogger(__name__)

class ContinuityCheckerAgent(Agent):
    """
    Agent specialized in identifying and resolving continuity issues in narratives.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Continuity Checker Agent"""
        super().__init__(name="Continuity Checker", config=config, llm_provider=llm_provider)
    
    def quick_check(self, chapters: List[str], character_profiles: str) -> Dict[str, Any]:
        """
        Perform a quick continuity check during the writing process
        
        Args:
            chapters: List of chapters written so far
            character_profiles: Character profiles for reference
            
        Returns:
            Dictionary with quick continuity analysis
        """
        # For quick checks, we focus on the most recent chapter and its relationship
        # to previous chapters
        
        if len(chapters) <= 1:
            # Not enough chapters for continuity checking
            return {"issues": [], "suggestions": []}
        
        # Get the most recent chapter and a sample from previous chapters
        recent_chapter = chapters[-1]
        previous_sample = ""
        
        # Take samples from earlier chapters for context
        if len(chapters) == 2:
            previous_sample = chapters[0][:2000]  # First 2000 chars of only previous chapter
        else:
            # Sample from first chapter and chapter just before the most recent
            previous_sample = chapters[0][:1000] + "\n\n...\n\n" + chapters[-2][-1000:]
        
        check_prompt = f"""
        Perform a quick continuity check between the most recent chapter and previous content.
        
        Previous Content Sample:
        {previous_sample}
        
        Most Recent Chapter:
        {recent_chapter[:3000]}... [truncated for length]
        
        Character Profiles (for reference):
        {character_profiles[:1500]}... [truncated for length]
        
        Check for these common continuity issues:
        1. Character inconsistencies (traits, knowledge, abilities)
        2. Timeline errors (sequence of events, time passing)
        3. Setting inconsistencies (locations, objects, environment)
        4. Plot contradictions (events that contradict earlier narrative)
        5. Knowledge errors (characters knowing things they shouldn't)
        
        Only report actual continuity problems, not stylistic issues or suggestions.
        Format your response as JSON with these keys:
        - "issues": Array of specific continuity problems found
        - "suggestions": Array of simple fixes for each issue
        """
        
        response = self.generate(check_prompt, temperature=0.3)
        return self.parse_json_response(response, default={"issues": [], "suggestions": []})
    
    def check_story_continuity(self, chapters: List[str], character_profiles: str, 
                              structured_outline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform a comprehensive continuity check across all chapters
        
        Args:
            chapters: List of all chapters
            character_profiles: Character profiles
            structured_outline: Structured chapter outline for reference
            
        Returns:
            Comprehensive continuity analysis
        """
        logger.info("Performing comprehensive continuity check across all chapters")
        
        # Extract key elements first for easier reference
        elements = self._extract_story_elements(chapters, character_profiles)
        
        # Analyze continuity across chapters
        continuity_issues = {}
        total_issues = 0
        
        # For token management, check chapters in small batches
        batch_size = 2
        for i in range(0, len(chapters), batch_size):
            batch_chapters = chapters[i:i + batch_size]
            batch_indices = list(range(i, min(i + batch_size, len(chapters))))
            
            # Create context by including summaries of other chapters
            context = "Other chapters summary:\n"
            for j, outline_item in enumerate(structured_outline):
                if j not in batch_indices:
                    context += f"Chapter {j+1}: {outline_item.get('title', '')}\n"
                    context += f"Summary: {outline_item.get('summary', '')}\n\n"
            
            batch_text = "\n\n---CHAPTER BREAK---\n\n".join(batch_chapters)
            
            # Check this batch
            batch_prompt = f"""
            Analyze the following chapters for continuity issues.
            
            Key Story Elements (for reference):
            {elements}
            
            Context from other chapters:
            {context}
            
            Chapters to analyze:
            {", ".join([f"Chapter {idx+1}" for idx in batch_indices])}
            
            Content:
            {batch_text}
            
            Check for these continuity issues:
            1. Character consistency (traits, behaviors, knowledge, abilities)
            2. Timeline consistency (sequence of events, time passing)
            3. Setting consistency (locations, objects, environment)
            4. Plot consistency (events align with established narrative)
            5. Factual consistency (details remain constant)
            
            For each issue found, provide:
            - The specific chapter number
            - A brief description of the issue
            - The relevant text snippet
            - A suggested fix
            
            Format your response as JSON with chapter numbers as keys, each containing an array of issues.
            """
            
            response = self.generate(batch_prompt, temperature=0.3)
            batch_issues = self.parse_json_response(response, default={})
            
            # Add batch issues to overall issues
            for chapter_idx in batch_indices:
                chapter_num = chapter_idx + 1
                chapter_key = str(chapter_num)
                
                if chapter_key in batch_issues and batch_issues[chapter_key]:
                    if chapter_key not in continuity_issues:
                        continuity_issues[chapter_key] = []
                    
                    continuity_issues[chapter_key].extend(batch_issues[chapter_key])
                    total_issues += len(batch_issues[chapter_key])
        
        # Create the final report
        continuity_report = {
            "chapter_fixes": continuity_issues,
            "total_fixes": total_issues,
            "story_elements": elements
        }
        
        logger.info(f"Continuity check complete. Found {total_issues} issues across {len(continuity_issues)} chapters.")
        return continuity_report
    
    def _extract_story_elements(self, chapters: List[str], character_profiles: str) -> str:
        """
        Extract key narrative elements for continuity checking
        
        Args:
            chapters: List of chapters
            character_profiles: Character profiles
            
        Returns:
            String of key narrative elements
        """
        # For efficiency, sample from the chapters
        chapter_samples = []
        if len(chapters) <= 3:
            chapter_samples = chapters
        else:
            # Take first, middle, and last chapter
            chapter_samples = [
                chapters[0],
                chapters[len(chapters) // 2],
                chapters[-1]
            ]
        
        combined_text = "\n\n---CHAPTER BREAK---\n\n".join(chapter_samples)
        
        extract_prompt = f"""
        Extract key narrative elements from the story for continuity checking.
        
        Story samples:
        {combined_text[:5000]}... [truncated for length]
        
        Character information:
        {character_profiles[:2000]}... [truncated for length]
        
        Extract and organize these elements:
        1. Characters: Names, roles, and key attributes
        2. Locations: All settings and their descriptions
        3. Timeline: Key events in chronological order
        4. Objects: Important items and their properties
        5. Relationships: Connections between characters
        6. Rules: Established principles/laws (magic systems, technology, etc.)
        
        Format this as a concise reference list for continuity checking.
        """
        
        return self.generate(extract_prompt, temperature=0.4)
    
    def apply_fixes(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply continuity fixes to a chapter
        
        Args:
            chapter: Chapter content
            issues: List of continuity issues to fix
            
        Returns:
            Fixed chapter content
        """
        if not issues:
            return chapter
        
        # Create a single fix prompt that addresses all issues at once
        issues_text = "\n".join([
            f"{i+1}. {issue.get('description', '')}\n"
            f"   Text: \"{issue.get('text', '')}\"\n"
            f"   Fix: {issue.get('fix', '')}"
            for i, issue in enumerate(issues)
        ])
        
        fix_prompt = f"""
        Revise the following chapter to fix the specified continuity issues.
        
        Chapter content:
        {chapter}
        
        Continuity issues to fix:
        {issues_text}
        
        Provide the complete revised chapter with all issues fixed. 
        Maintain the same overall length, style, and content, changing only what's needed to fix the continuity problems.
        Do not add comments or explanations - just provide the revised chapter text.
        """
        
        return self.generate(fix_prompt, temperature=0.5)
    
    def check_character_consistency(self, character_name: str, chapters: List[str], 
                                   character_profile: str) -> Dict[str, Any]:
        """
        Check consistency for a specific character across chapters
        
        Args:
            character_name: Name of the character to check
            chapters: List of chapters
            character_profile: Profile of the character
            
        Returns:
            Character consistency analysis
        """
        # Extract mentions of the character
        character_mentions = self._extract_character_mentions(character_name, chapters)
        
        if not character_mentions:
            return {
                "character": character_name,
                "issues": [],
                "consistency_score": 10
            }
        
        check_prompt = f"""
        Analyze consistency for the character "{character_name}" across the story.
        
        Character Profile:
        {character_profile}
        
        Character Appearances:
        {character_mentions}
        
        Check for consistency in:
        1. Personality traits and behavior
        2. Speech patterns and vocabulary
        3. Skills and abilities
        4. Background details and history
        5. Relationships with other characters
        6. Physical description and appearance
        7. Character development and arc
        
        Format your response as JSON with these fields:
        - "character": Character name
        - "issues": Array of specific inconsistencies found
        - "chapter_locations": Object mapping issues to chapter numbers
        - "suggestions": Array of fixes for each issue
        - "consistency_score": Number from 1-10 indicating overall consistency
        """
        
        response = self.generate(check_prompt, temperature=0.4)
        return self.parse_json_response(response, default={"character": character_name, "issues": []})
    
    def _extract_character_mentions(self, character_name: str, chapters: List[str]) -> str:
        """
        Extract mentions of a specific character from chapters
        
        Args:
            character_name: Name of the character
            chapters: List of chapters
            
        Returns:
            String with character mentions from different chapters
        """
        mentions = []
        
        for i, chapter in enumerate(chapters):
            # Create regex pattern to find paragraphs mentioning character
            # This is a simple approach - could be more sophisticated
            pattern = r'([^.!?]*\b' + re.escape(character_name) + r'\b[^.!?]*[.!?])'
            matches = re.findall(pattern, chapter)
            
            # Select a sample of mentions (up to 3 per chapter)
            sample = matches[:3] if len(matches) > 3 else matches
            
            if sample:
                mentions.append(f"Chapter {i+1}:\n" + "\n".join(sample))
        
        # Combine mentions with chapter markers
        if mentions:
            return "\n\n".join(mentions)
        else:
            return f"No clear mentions of {character_name} found."
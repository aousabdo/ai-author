"""
Pacing Advisor Agent
Specializes in analyzing and improving narrative pacing and flow.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple  # Added Tuple import here
from core.agent import Agent
from utils.text_processing import analyze_pacing, identify_scene_breaks

logger = logging.getLogger(__name__)

class PacingAdvisorAgent(Agent):
    """
    Agent specialized in analyzing and improving narrative pacing.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Pacing Advisor Agent"""
        super().__init__(name="Pacing Advisor", config=config, llm_provider=llm_provider)
    
    def analyze_pacing(self, chapters: List[str], structured_outline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the pacing across chapters
        
        Args:
            chapters: List of chapters to analyze
            structured_outline: Structured outline with chapter information
            
        Returns:
            Dictionary with pacing analysis
        """
        logger.info(f"Analyzing pacing for {len(chapters)} chapters")
        
        # First, create a book-level pacing model
        book_pacing_model = self._create_book_pacing_model(structured_outline)
        
        # For each chapter, analyze pacing
        chapter_analyses = {}
        chapter_fixes = {}
        total_fixes = 0
        
        for i, chapter in enumerate(chapters):
            chapter_num = i + 1
            logger.info(f"Analyzing pacing for Chapter {chapter_num}")
            
            # Get expected pacing for this chapter
            expected_pacing = "steady"  # Default
            if str(chapter_num) in book_pacing_model.get("chapter_pacing", {}):
                expected_pacing = book_pacing_model["chapter_pacing"][str(chapter_num)]
            
            # Use text processing tools for initial analysis
            pacing_stats = analyze_pacing(chapter)
            scene_breaks = identify_scene_breaks(chapter)
            
            # Analyze chapter sample
            excerpt = chapter[:2000] + "..." + chapter[-2000:] if len(chapter) > 4000 else chapter
            
            chapter_prompt = f"""
            Analyze the narrative pacing of this chapter excerpt.
            
            Book-level pacing model:
            {book_pacing_model["description"]}
            
            Expected pacing for Chapter {chapter_num}: {expected_pacing}
            
            Chapter {chapter_num} Excerpt:
            {excerpt}
            
            Pacing Statistics:
            - Dialogue ratio trend: {pacing_stats.get('dialogue_trend', [])}
            - Action intensity trend: {pacing_stats.get('action_trend', [])}
            - Emotional intensity trend: {pacing_stats.get('emotion_trend', [])}
            - Number of scene breaks: {len(scene_breaks)}
            
            Analyze the pacing for:
            1. Overall flow and rhythm (too fast/slow/inconsistent)
            2. Scene transitions and breaks
            3. Balance of action, dialogue, and description
            4. Tension build-up and release
            5. Alignment with expected pacing for this point in the story
            
            Identify any pacing issues, including:
            - Rushed or skipped important moments
            - Dragging sections that slow the narrative
            - Uneven or jarring transitions
            - Misaligned pacing for the chapter's role in the story arc
            
            Format your response as JSON with these fields:
            - "issues": Array of specific pacing issues found
            - "specific_locations": Array of locations in the chapter for each issue
            - "fixes": Array of suggested improvements for each issue
            - "pacing_score": Number from 1-10 rating the chapter's pacing quality
            """
            
            response = self.generate(chapter_prompt, temperature=0.4)
            
            # Parse and store results
            analysis = self.parse_json_response(response, default={
                "issues": [],
                "specific_locations": [],
                "fixes": [],
                "pacing_score": 5
            })
            
            chapter_analyses[str(chapter_num)] = analysis
            
            # Collect specific fixes needed
            issues = analysis.get("issues", [])
            locations = analysis.get("specific_locations", [])
            fixes = analysis.get("fixes", [])
            
            if not issues or not fixes:
                continue
                
            fix_count = min(len(issues), len(fixes))
            chapter_fixes[str(chapter_num)] = []
            
            for j in range(fix_count):
                location = locations[j] if j < len(locations) else "Unknown location"
                
                chapter_fixes[str(chapter_num)].append({
                    "description": issues[j] if j < len(issues) else "",
                    "location": location,
                    "fix": fixes[j] if j < len(fixes) else ""
                })
            
            total_fixes += fix_count
        
        # Analyze consistency across chapters
        overall_pacing_analysis = self._analyze_overall_pacing(chapter_analyses, structured_outline)
        
        # Create the final report
        pacing_report = {
            "book_pacing_model": book_pacing_model,
            "overall_analysis": overall_pacing_analysis,
            "chapter_analyses": chapter_analyses,
            "chapter_fixes": chapter_fixes,
            "total_fixes": total_fixes
        }
        
        logger.info(f"Pacing analysis complete. Found {total_fixes} issues across {len(chapter_fixes)} chapters.")
        return pacing_report
    
    def _create_book_pacing_model(self, structured_outline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a pacing model for the entire book
        
        Args:
            structured_outline: Structured outline with chapter information
            
        Returns:
            Dictionary with book-level pacing model
        """
        # Extract chapter summaries for analysis
        chapter_summaries = []
        for i, chapter in enumerate(structured_outline):
            summary = f"Chapter {i+1}: {chapter.get('title', '')}\n{chapter.get('summary', '')}"
            chapter_summaries.append(summary)
        
        all_summaries = "\n\n".join(chapter_summaries)
        
        model_prompt = f"""
        Create a detailed pacing model for this book based on the chapter outlines.
        
        Chapter Outlines:
        {all_summaries}
        
        Analyze the overall narrative structure and create a pacing model that includes:
        
        1. Story arc stages (setup, rising action, climax, falling action, resolution)
        2. Key tension points and their locations
        3. Recommended pacing for each chapter (slow, moderate, fast)
        4. Natural ebbs and flows of tension
        5. Key emotional beats and their distribution
        
        Format your response as JSON with these fields:
        - "description": Detailed description of the overall pacing model
        - "story_arc": Object mapping arc stages to chapter ranges
        - "key_moments": Array of important story moments and their chapters
        - "chapter_pacing": Object mapping chapter numbers to recommended pacing
        """
        
        response = self.generate(model_prompt, temperature=0.5)
        return self.parse_json_response(response, default={
            "description": "Standard narrative arc with rising tension",
            "story_arc": {},
            "key_moments": [],
            "chapter_pacing": {}
        })
    
    def _analyze_overall_pacing(self, chapter_analyses: Dict[str, Any], 
                              structured_outline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze overall pacing across the book
        
        Args:
            chapter_analyses: Individual chapter analyses
            structured_outline: Structured outline with chapter information
            
        Returns:
            Dictionary with overall pacing analysis
        """
        # Extract pacing scores
        pacing_scores = []
        for chapter_num, analysis in chapter_analyses.items():
            pacing_scores.append((int(chapter_num), analysis.get("pacing_score", 5)))
        
        # Sort by chapter number
        pacing_scores.sort(key=lambda x: x[0])
        
        # Create a simplified analysis for the prompt
        scores_text = ", ".join([f"Ch{num}: {score}" for num, score in pacing_scores])
        
        # Extract chapter transitions that might need work
        weak_transitions = []
        for i in range(len(pacing_scores) - 1):
            curr_chapter, curr_score = pacing_scores[i]
            next_chapter, next_score = pacing_scores[i + 1]
            
            # Look for large drops in pacing score
            if curr_score - next_score > 2:
                weak_transitions.append((curr_chapter, next_chapter))
        
        overall_prompt = f"""
        Analyze the overall pacing across all chapters of the book.
        
        Chapter pacing scores: {scores_text}
        
        Potential weak transitions between: {weak_transitions}
        
        Based on this data and the chapter outlines, provide:
        
        1. An assessment of the book's overall pacing
        2. Identification of any pacing patterns or issues
        3. Recommendations for improving the overall pacing arc
        4. Specific attention to transitions between chapters
        
        Format your response as JSON with these fields:
        - "overall_assessment": General assessment of the book's pacing
        - "pacing_patterns": Identified patterns in pacing
        - "problem_areas": Specific sections with pacing issues
        - "recommendations": Key recommendations for improvement
        """
        
        response = self.generate(overall_prompt, temperature=0.5)
        return self.parse_json_response(response, default={
            "overall_assessment": "Mixed pacing with some inconsistencies",
            "pacing_patterns": [],
            "problem_areas": [],
            "recommendations": []
        })
    
    def apply_fixes(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply pacing fixes to a chapter
        
        Args:
            chapter: The chapter content
            issues: List of pacing issues to fix
            
        Returns:
            Updated chapter with pacing fixes applied
        """
        if not issues:
            return chapter
        
        # Create a batch prompt that includes all fixes
        issues_text = "\n".join([
            f"{i+1}. Issue: {issue.get('description', '')}\n"
            f"   Location: {issue.get('location', 'Unspecified')}\n"
            f"   Fix: {issue.get('fix', '')}"
            for i, issue in enumerate(issues)
        ])
        
        fix_prompt = f"""
        Revise the following chapter to fix the specified pacing issues.
        
        Chapter content:
        {chapter[:1000]}...
        [middle of chapter omitted for brevity]
        ...{chapter[-1000:]}
        
        Pacing issues to fix:
        {issues_text}
        
        Instructions:
        1. For each issue, apply the suggested fix to the appropriate location
        2. Adjust surrounding text as needed for smooth transitions
        3. Maintain the same events and character development
        4. Return the complete revised chapter
        
        Focus specifically on improving narrative flow, scene transitions, and the balance
        of action, dialogue, and description. Keep the same approximate chapter length.
        """
        
        # For larger chapters, use a different approach
        if len(chapter) > 8000:
            return self._apply_targeted_pacing_fixes(chapter, issues)
        
        return self.generate(fix_prompt, temperature=0.6)
    
    def _apply_targeted_pacing_fixes(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply targeted pacing fixes to specific sections of a large chapter
        
        Args:
            chapter: The chapter content
            issues: List of pacing issues to fix
            
        Returns:
            Updated chapter with pacing fixes applied
        """
        for issue in issues:
            description = issue.get('description', '')
            location = issue.get('location', '')
            fix = issue.get('fix', '')
            
            if not description or not fix:
                continue
                
            # Try to identify the location in the text
            location_found = False
            
            # Check if location contains an excerpt we can find
            if "..." in location:
                parts = location.split("...")
                if len(parts) >= 2:
                    start_text = parts[0].strip()
                    end_text = parts[1].strip()
                    
                    if start_text in chapter and end_text in chapter:
                        # Find the section to fix
                        start_idx = chapter.find(start_text)
                        end_idx = chapter.find(end_text, start_idx + len(start_text)) + len(end_text)
                        
                        if start_idx >= 0 and end_idx > start_idx:
                            section_to_fix = chapter[start_idx:end_idx]
                            
                            # Create a prompt to fix just this section
                            section_prompt = f"""
                            Revise this specific section to fix a pacing issue: {description}
                            
                            Original section:
                            {section_to_fix}
                            
                            Fix to apply: {fix}
                            
                            Provide ONLY the revised section that maintains the same basic content
                            but addresses the pacing issue. Keep approximately the same length.
                            """
                            
                            # Generate the fixed section
                            fixed_section = self.generate(section_prompt, temperature=0.6)
                            
                            # Replace the section in the chapter
                            chapter = chapter[:start_idx] + fixed_section + chapter[end_idx:]
                            location_found = True
            
            # If we couldn't find a specific location, skip this fix
            if not location_found:
                logger.warning(f"Could not locate section for pacing fix: {description}")
        
        return chapter
    
    def improve_chapter_transition(self, chapter_end: str, next_chapter_start: str) -> Tuple[str, str]:
        """
        Improve the transition between two chapters
        
        Args:
            chapter_end: The ending of the current chapter
            next_chapter_start: The beginning of the next chapter
            
        Returns:
            Tuple of improved chapter ending and next chapter beginning
        """
        transition_prompt = f"""
        Improve the transition between these two chapters to create better narrative flow.
        
        Current chapter ending:
        {chapter_end}
        
        Next chapter beginning:
        {next_chapter_start}
        
        Create:
        1. A revised ending for the current chapter that creates anticipation
        2. A revised beginning for the next chapter that connects smoothly
        
        Both revisions should maintain the same events and character actions,
        but improve the rhythm, flow, and connection between chapters.
        
        Format your response as JSON with these fields:
        - "revised_ending": The improved ending for the current chapter
        - "revised_beginning": The improved beginning for the next chapter
        - "notes": Brief explanation of the improvements made
        """
        
        response = self.generate(transition_prompt, temperature=0.6)
        result = self.parse_json_response(response, default={
            "revised_ending": chapter_end,
            "revised_beginning": next_chapter_start
        })
        
        return result.get("revised_ending", chapter_end), result.get("revised_beginning", next_chapter_start)
    
    def analyze_scene_structure(self, chapter: str) -> Dict[str, Any]:
        """
        Analyze the scene structure within a chapter
        
        Args:
            chapter: The chapter content
            
        Returns:
            Dictionary with scene structure analysis
        """
        # Identify potential scene breaks
        scene_breaks = identify_scene_breaks(chapter)
        
        # Create a list of potential scenes
        scenes = []
        prev_break = 0
        
        for break_idx in scene_breaks:
            scene_text = chapter[prev_break:break_idx]
            if len(scene_text.strip()) > 100:  # Only include non-trivial scenes
                scenes.append(scene_text)
            prev_break = break_idx
        
        # Add the final scene
        if prev_break < len(chapter) and len(chapter[prev_break:].strip()) > 100:
            scenes.append(chapter[prev_break:])
        
        scene_analysis_prompt = f"""
        Analyze the scene structure of this chapter which appears to contain {len(scenes)} scenes.
        
        For each scene, assess:
        1. Purpose in the narrative
        2. Pacing (slow, moderate, fast)
        3. Emotional tone
        4. Effectiveness of opening and closing
        
        Then evaluate:
        - Overall scene sequence and flow
        - Balance between scenes
        - Effectiveness of scene transitions
        - Pacing variation between scenes
        
        Format your response as JSON with:
        - "scenes": Array of scene analyses
        - "flow_assessment": Overall assessment of scene flow
        - "recommended_changes": Suggestions for improving scene structure
        """
        
        if scenes:
            # Include a sample of scenes in the prompt
            scene_samples = []
            for i, scene in enumerate(scenes[:3]):  # Limit to first 3 scenes
                sample = scene[:500] + "..." if len(scene) > 500 else scene
                scene_samples.append(f"Scene {i+1} sample:\n{sample}\n")
            
            scene_analysis_prompt += f"\n\nScene samples:\n{''.join(scene_samples)}"
        
        response = self.generate(scene_analysis_prompt, temperature=0.5)
        return self.parse_json_response(response, default={
            "scenes": [],
            "flow_assessment": "Not analyzed",
            "recommended_changes": []
        })
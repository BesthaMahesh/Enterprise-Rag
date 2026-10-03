import re
from typing import List, Dict, Any


class ParsedSection:
    def __init__(self, title: str, content: str, level: int = 1, page: int = 1):
        self.title = title
        self.content = content
        self.level = level
        self.page = page

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "page": self.page
        }


class DocumentParser:
    """Parses raw text into structured sections and blocks."""

    @staticmethod
    def parse_markdown(text: str) -> List[ParsedSection]:
        sections: List[ParsedSection] = []
        lines = text.split("\n")
        
        current_title = "Overview"
        current_content: List[str] = []
        current_level = 1
        current_page = 1

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
        page_pattern = re.compile(r"<!--\s*Page\s+(\d+)\s*-->", re.IGNORECASE)

        for line in lines:
            # Check page indicator
            page_match = page_pattern.match(line.strip())
            if page_match:
                current_page = int(page_match.group(1))
                continue

            # Check heading
            match = heading_pattern.match(line)
            if match:
                # Flush previous section
                if current_content:
                    body = "\n".join(current_content).strip()
                    if body:
                        sections.append(ParsedSection(
                            title=current_title,
                            content=body,
                            level=current_level,
                            page=current_page
                        ))
                    current_content = []

                current_level = len(match.group(1))
                current_title = match.group(2).strip()
            else:
                current_content.append(line)

        # Flush trailing section
        if current_content:
            body = "\n".join(current_content).strip()
            if body:
                sections.append(ParsedSection(
                    title=current_title,
                    content=body,
                    level=current_level,
                    page=current_page
                ))

        if not sections:
            sections.append(ParsedSection(
                title="Document Body",
                content=text.strip(),
                level=1,
                page=1
            ))

        return sections

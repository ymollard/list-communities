from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict

import os,sys
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(current_dir))
from utils.event_matcher import EventMatcher

class GlobalEventsGenerator:
    """Generates a global events file by combining and merging all community events"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.output_file = root_dir / 'events.json'
        self.event_matcher = EventMatcher()

    def read_community_events(self, events_file: Path) -> List[Dict]:
        """Read events from a community's events file"""
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading events file {events_file}: {e}")
            return []

    def merge_events(self, events: List[Dict]) -> List[Dict]:
        """
        Merge events that are the same across different communities.
        Uses EventMatcher to detect same events even with different URLs.
        """
        merged_events = []
        processed_events = set()  # Keep track of processed events by their index
        
        for i, event in enumerate(events):
            if i in processed_events:
                continue
                
            current_event = event.copy()
            current_communities = set(event.get('communities', [event.get('community')] if event.get('community') else []))
            
            # Look for matching events
            for j, other_event in enumerate(events[i+1:], start=i+1):
                if j not in processed_events and self.event_matcher.are_same_event(event, other_event):
                    # Merge communities
                    other_communities = set(other_event.get('communities', [other_event.get('community')] if other_event.get('community') else []))
                    current_communities.update(other_communities)
                    processed_events.add(j)
                    
                    # Use the most complete information from either event
                    if len(other_event.get('description', '')) > len(current_event.get('description', '')):
                        current_event['description'] = other_event['description']
                    
                    # Keep the most detailed location
                    if len(other_event.get('location', '')) > len(current_event.get('location', '')):
                        current_event['location'] = other_event['location']

            # Update communities in the merged event
            current_event['communities'] = sorted(list(current_communities))
            if 'community' in current_event:
                del current_event['community']
            
            merged_events.append(current_event)
            processed_events.add(i)

        # Sort by date
        merged_events.sort(key=lambda x: x['date'], reverse=True)
        return merged_events

    def generate_global_events(self):
        """Generate global events file by combining and merging all community events"""
        all_events = []

        # Collect all events from communities
        for community_dir in self.root_dir.iterdir():
            if community_dir.is_dir() and not community_dir.name.startswith('.'):
                events_file = community_dir / 'events.json'
                if events_file.exists():
                    events = self.read_community_events(events_file)
                    all_events.extend(events)

        # Merge duplicate events
        merged_events = self.merge_events(all_events)

        # Write the combined events to the global file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_events, f, indent=2, ensure_ascii=False)
        
        original_count = len(all_events)
        merged_count = len(merged_events)
        print(f"Generated global events file with {merged_count} unique events")
        if original_count > merged_count:
            print(f"Merged {original_count - merged_count} duplicate events")

def main():
    root_dir = Path('.')
    generator = GlobalEventsGenerator(root_dir)
    generator.generate_global_events()

if __name__ == "__main__":
    main()
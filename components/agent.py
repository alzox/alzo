import os
from langchain.tools import tool
import requests
from icalendar import Calendar, Event
import recurring_ical_events
import arrow

@tool
def weekly_meetings() -> str:
    """
    Fetches and displays the meetings a user has given the current week.
    Respond with "Here are your meetings for the week:"
    Common synonyms: meanings
    """
    GOOGLE = os.getenv("GOOGLE_ICS_LINK")
    OUTLOOK = os.getenv("OUTLOOK_ICS_LINK")
    print("Fetching .ics files")
    google_calendar = Calendar.from_ical(requests.get(GOOGLE).text)
    outlook_calendar = Calendar.from_ical(requests.get(OUTLOOK).text)
    now = arrow.now().datetime.date()
    weekend = arrow.now().ceil('week').datetime.date()
    def get_event_date(event):
        return event.start.date() if hasattr(event.start, 'date') else event.start
    events = [event for event in google_calendar.events if now < get_event_date(event) < weekend] \
            +[event for event in outlook_calendar.events if now < get_event_date(event) < weekend]\
            + recurring_ical_events.of(google_calendar).between(start=now, stop=weekend)          \
            + recurring_ical_events.of(outlook_calendar).between(start=now, stop=weekend)         
    
    return [(event.start,
             event.end,
             event.summary,
             event.description.replace("*",""),
             event.duration,
             event.attendees,
             event.location,
             event.classification,
             event.categories
             ) for event in events]

TOOLS = [weekly_meetings]

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(arrow.now())
    print(arrow.now().ceil('week'))
    print(weekly_meetings())
    for event in weekly_meetings():
        print(event)
        print("-----")
    print(len(weekly_meetings()))

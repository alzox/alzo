import os
import requests

from icalendar import Calendar
import recurring_ical_events
import arrow

from langchain.tools import tool

@tool
def weekly_meetings():
    """
    Fetches and displays the meetings a user has given the current week.
    Respond with "Here are your meetings for the week:"
    Common synonyms: meanings
    """
    GOOGLE = os.getenv("GOOGLE_ICS_LINK")
    OUTLOOK = os.getenv("OUTLOOK_ICS_LINK")
    google_calendar = Calendar.from_ical(requests.get(GOOGLE).text)     # pyright: ignore
    outlook_calendar = Calendar.from_ical(requests.get(OUTLOOK).text)   # pyright: ignore
    now = arrow.now().datetime.date()
    weekend = arrow.now().ceil('week').datetime.date()
    def get_event_date(event):
        return event.start.date() if hasattr(event.start, 'date') else event.start
    events = [event for event in google_calendar.events if now < get_event_date(event) < weekend] \
            +[event for event in outlook_calendar.events if now < get_event_date(event) < weekend]\
            + recurring_ical_events.of(google_calendar).between(start=now, stop=weekend)          \
            + recurring_ical_events.of(outlook_calendar).between(start=now, stop=weekend)         
    
    return [(event.start,                       # pyright: ignore
             event.end,                         # pyright: ignore
             event.summary,                     # pyright: ignore
             event.description.replace("*",""), # pyright: ignore
             event.duration,                    # pyright: ignore
             event.attendees,                   # pyright: ignore
             event.location,                    # pyright: ignore
             event.classification,              # pyright: ignore
             event.categories                   # pyright: ignore
             ) for event in events]

TOOLS = [weekly_meetings]

# if __name__ == "__main__":
   # from dotenv import load_dotenv
    # print(arrow.now())
    # print(arrow.now().ceil('week'))
    # print(weekly_meetings())
    # for event in weekly_meetings():
    #     print(event)
    #     print("-----")
    # print(len(weekly_meetings()))


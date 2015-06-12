from get_database import get_section_db
from recommender.trip import Section
from datetime import datetime, timedelta
import logging

def get_all_sections(section_id):
    """ Return all sections in the trip that the specified section is a part of
        For example, if this is the section to go to the train station, return all
        sections for the same trip.
        The input is the _id field of the section
    """
    section = Section.section_from_json(get_section_db().find_one({'_id': section_id}))
    allSections = get_section_db().find({"trip_id": section.trip_id})
    return list(allSections)

def get_all_sections_for_user_day(user,year,month,day):
    """ Return all sections in the trip that the specified section is a part of
        For example, if this is the section to go to the train station, return all
        sections for the same trip.
        The input is the _id field of the section
    """
    dayMidnight = datetime(year,month,day,0,0,0)
    nextDayMidnight = dayMidnight + timedelta(days =1)
    sectionIt = get_section_db().find({'user_id': user,
        "section_start_datetime": {"$gt": dayMidnight},
        "section_end_datetime": {"$lt": nextDayMidnight}})
    return [Section.section_from_json(s) for s in sectionIt]

def get_trip_before(section_id):
    """ Return the trip just before the one that this section belongs to.
    """
    section = Section.section_from_json(get_section_db().find_one({'_id': section_id}))
    logging.debug("Found section %s" % section)
    firstSection = Section.section_from_json(get_section_db().find_one({"trip_id": section.trip_id, "section_id": 0}))
    logging.debug("First section %s" % firstSection)
    # First, try to find the seection assuming that data collection was continuous
    prevPlace = Section.section_from_json(get_section_db().find_one({"section_end_datetime": firstSection.start_time}))
    logging.debug("prevPlace %s" % prevPlace)
    # This should be the "place" trip
    if prevPlace is not None:
        logging.debug("prevPlace.section_type = %s" % prevPlace.section_type)
        if prevPlace.section_type != "place":
            return None
        else:
            prevTrip = get_section_db().find_one({"section_end_datetime": prevPlace.start_time})
            return prevTrip
    else:
        assert(False)
    return allSections
